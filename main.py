import cv2
import os
import argparse
import serial
from datetime import datetime
import face_recognition

# Configuration
OUTPUT_DIR = "class_captures"
STUDENT_DB = "student_images"
SERIAL_PORT = 'COM3'  # Change to your Arduino port
BAUD_RATE = 9600

def setup():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(STUDENT_DB, exist_ok=True)
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera")
    return cap

def capture_image(camera, filename):
    ret, frame = camera.read()
    if ret:
        cv2.imwrite(filename, frame)
        print(f"Captured: {filename}")
        return filename
    return None

def load_student_data():
    known_encodings = []
    known_names = []
    
    for file in os.listdir(STUDENT_DB):
        if file.endswith(('.jpg', '.png')):
            path = os.path.join(STUDENT_DB, file)
            image = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(os.path.splitext(file)[0])
    
    return known_encodings, known_names

def process_attendance(start_img, end_img):
    known_encodings, known_names = load_student_data()
    present = set()
    
    for img_path in [start_img, end_img]:
        image = face_recognition.load_image_file(img_path)
        face_encodings = face_recognition.face_encodings(image)
        
        for encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.6)
            if True in matches:
                present.add(known_names[matches.index(True)])
    
    absent = set(known_names) - present
    return sorted(present), sorted(absent)

def serial_listener():
    camera = setup()
    start_capture = None
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Listening on {SERIAL_PORT}...")
        
        while True:
            if ser.in_waiting > 0:
                command = ser.readline().decode('utf-8').strip()
                print(f"Received: {command}")
                
                if command == "CAPTURE_START":
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(OUTPUT_DIR, f"start_{timestamp}.jpg")
                    start_capture = capture_image(camera, filename)
                
                elif command == "CAPTURE_END" and start_capture:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(OUTPUT_DIR, f"end_{timestamp}.jpg")
                    end_capture = capture_image(camera, filename)
                    
                    if end_capture:
                        present, absent = process_attendance(start_capture, end_capture)
                        print("\nAttendance Report:")
                        print(f"Present: {present}")
                        print(f"Absent: {absent}")
                        
                        # Save report
                        report_file = os.path.join(OUTPUT_DIR, f"report_{timestamp}.txt")
                        with open(report_file, 'w') as f:
                            f.write(f"Attendance Report - {timestamp}\n\n")
                            f.write("Present:\n" + "\n".join(present) + "\n\n")
                            f.write("Absent:\n" + "\n".join(absent))
    
    finally:
        camera.release()
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--trigger', help='Direct capture trigger')
    args = parser.parse_args()
    
    if args.trigger:
        camera = setup()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_DIR, f"{args.trigger}_{timestamp}.jpg")
        capture_image(camera, filename)
        camera.release()
    else:
        serial_listener()