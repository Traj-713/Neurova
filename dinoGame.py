import serial
print(serial.__file__)
from pynput.keyboard import Controller

# Set up serial communication
arduino_port = '/dev/cu.usbmodem2101'  # Replace with the port where your Arduino is connected (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
baud_rate = 9600
ser = serial.Serial(arduino_port, baud_rate)

# Set up the keyboard controller
keyboard = Controller()

print("Listening for Arduino messages...")

try:
    while True:
        if ser.in_waiting > 0:  # Check if there's data from the Arduino
            line = ser.readline().decode('utf-8').strip()  # Read the line and decode it
            print(f"Received: {line}")
            
            if line == "TOGGLE_SPACE":
                # Simulate a spacebar press
                keyboard.press(' ')
                keyboard.release(' ')
                print("Spacebar toggled")
except KeyboardInterrupt:
    print("Exiting...")
    ser.close()
