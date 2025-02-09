const int voltagePin = A0; // Pin for voltage input
const int ledPin = LED_BUILTIN; // Built-in LED pin
const float threshold = 2; // Threshold voltage
const int numSamples = 10; // Number of samples for averaging
const unsigned long spikeIgnoreDuration = 70; // Spike duration in milliseconds

float voltageSum = 0;
float averageVoltage = 0;
int sampleCount = 0;
bool ledState = false; // Current LED state
unsigned long lastToggleTime = 0;

void setup() {
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
  Serial.begin(9600); // Start serial communication
}

void loop() {
  // Read the voltage input
  int rawValue = analogRead(voltagePin);
  float voltage = (rawValue / 1023.0) * 5.0; // Convert to voltage (assuming 5V reference)

  // Update average voltage
  voltageSum += voltage;
  sampleCount++;

  if (sampleCount >= numSamples) {
    averageVoltage = voltageSum / numSamples;
    voltageSum = 0; // Reset sum
    sampleCount = 0; // Reset sample count

    // Check if average voltage exceeds the threshold
    if (averageVoltage > threshold) {
      unsigned long currentTime = millis();

      // Ignore short spikes by checking duration
      if (currentTime - lastToggleTime > spikeIgnoreDuration) {
        Serial.println("TOGGLE_SPACE"); // Send toggle signal over serial
        ledState = !ledState; // Toggle LED state
        digitalWrite(ledPin, ledState ? HIGH : LOW); // Update LED
        lastToggleTime = currentTime;   // Update the last toggle time
      }
    }
  }

  delay(10); // Delay to control sampling rate
}
