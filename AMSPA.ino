const int triggerButton = 2;  // Button to start the process
const int ledPin = 13;        // Status LED

void setup() {
  pinMode(triggerButton, INPUT_PULLUP);
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
  while (!Serial);  // Wait for serial connection
}

void loop() {
  if (digitalRead(triggerButton) == LOW) {
    digitalWrite(ledPin, HIGH);
    triggerCameraSequence();
    digitalWrite(ledPin, LOW);
    delay(60000);  // Debounce delay (1 minute)
  }
}

void triggerCameraSequence() {
  // Send start command
  Serial.println("CAPTURE_START");
  delay(5000);  // Time for first capture
  
  // Wait for class duration (45 minutes minus 10 minutes)
  delay(35 * 60 * 1000);  // 35 minutes
  
  // Send end command
  Serial.println("CAPTURE_END");
}