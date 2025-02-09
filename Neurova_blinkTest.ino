const int voltagePin = A0; // Pin for voltage input
const int ledPin = LED_BUILTIN; // Built-in LED pin
const float threshold = 2; // Threshold voltage (adjust as needed)
const int numSamples = 10; // Number of samples for averaging
const unsigned long spikeIgnoreDuration = 70; // Spike duration in milliseconds (0.07 seconds)

float voltageSum = 0;
float averageVoltage = 0;
int sampleCount = 0;
bool ledState = false; // Current LED state
unsigned long lastToggleTime = 0;

void setup() {
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
  Serial.begin(9600);
}

void loop() {
  // Read voltage input
  int rawValue = analogRead(voltagePin);
  float voltage = (rawValue / 1023.0) * 5.0; // Convert to voltage (assuming 5V reference)

  // Update average voltage
  voltageSum += voltage;
  sampleCount++;
  
  if (sampleCount >= numSamples) {
    averageVoltage = voltageSum / numSamples; // Calculate average
    voltageSum = 0; // Reset sum
    sampleCount = 0; // Reset sample count

    // Check if average voltage exceeds the threshold
    if (averageVoltage > threshold) {
      unsigned long currentTime = millis();

      // Ignore short spikes by ensuring the toggle doesn't happen too quickly
      if (currentTime - lastToggleTime > spikeIgnoreDuration) {
        ledState = !ledState; // Toggle LED state
        digitalWrite(ledPin, ledState ? HIGH : LOW); // Update LED
        lastToggleTime = currentTime; // Update last toggle time
        delay(100);
      }
    }
  }

  delay(10); // Delay to control sampling rate
}

