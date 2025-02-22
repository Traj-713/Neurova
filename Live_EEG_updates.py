import serial
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
import time

# Define EEG frequency bands
BANDS = {
    "delta": (0.5, 4),
    "theta": (4, 8),
    "alpha": (8, 12),  # Relaxation
    "beta": (12, 30),  # Concentration
    "gamma": (30, 40)
}

# Sampling settings
fs = 250  # Sampling frequency in Hz
buffer_size = fs * 2  # 2 seconds of data for processing
eeg_buffer = []

# Serial port setup (update COM port)
arduino_port = "/dev/cu.usbmodem2101"  # Change to your Arduino port (e.g., "/dev/ttyUSB0" for Linux)
baud_rate = 115200
ser = serial.Serial(arduino_port, baud_rate, timeout=1)

# Bandpass filter function
def bandpass_filter(data, fs, lowcut, highcut):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = signal.butter(4, [low, high], btype='band')
    return signal.filtfilt(b, a, data)

# Compute power spectral density (PSD) for each band
def compute_band_power(data, fs):
    band_powers = {}
    for band, (low, high) in BANDS.items():
        filtered_data = bandpass_filter(data, fs, low, high)
        band_power = np.sum(filtered_data ** 2) / len(filtered_data)  # Power estimation
        band_powers[band] = band_power
    return band_powers

# Normalize power values to account for individual differences
def normalize_powers(band_powers):
    total_power = sum(band_powers.values())
    return {band: power / total_power for band, power in band_powers.items()}

# Parameters for frequency response plotting
plot_interval = 30  # seconds between plots (excluding countdown)
last_plot_time = time.time()
plot_counter = 1

# Data storage for time series plots (if still desired)
timestamps = []
alpha_powers = []
beta_powers = []
concentration_levels = []

start_time = time.time()

print("Recording EEG data. Press Ctrl+C to stop.")
try:
    while True:
        line = ser.readline().decode().strip()
        if line:
            try:
                eeg_value = float(line)  # Assuming a single EEG channel value per line
                eeg_buffer.append(eeg_value)

                if len(eeg_buffer) >= buffer_size:
                    eeg_data = np.array(eeg_buffer[-buffer_size:])  # Use last 'buffer_size' samples

                    # Process EEG signal for band power estimation
                    band_powers = compute_band_power(eeg_data, fs)
                    normalized_powers = normalize_powers(band_powers)

                    # Extract relevant powers for concentration calculation
                    alpha_power = normalized_powers["alpha"]
                    beta_power = normalized_powers["beta"]

                    # Simple rule: If beta > alpha → Concentrated; else → Relaxed
                    concentration_level = beta_power / (alpha_power + beta_power)

                    # Store data
                    elapsed_time = time.time() - start_time
                    timestamps.append(elapsed_time)
                    alpha_powers.append(alpha_power)
                    beta_powers.append(beta_power)
                    concentration_levels.append(concentration_level)

                    print(f"Time: {elapsed_time:.2f}s | Alpha: {alpha_power:.4f} | Beta: {beta_power:.4f} | Concentration: {concentration_level:.2f}")

                    # Check if it's time to plot the frequency response
                    current_time = time.time()
                    if current_time - last_plot_time >= plot_interval:
                        # Compute PSD using Welch's method
                        f, Pxx = signal.welch(eeg_data, fs, nperseg=buffer_size//2)
                        
                        # Create and save the frequency response plot
                        plt.figure(figsize=(8, 4))
                        plt.semilogy(f, Pxx, color='magenta')
                        plt.xlabel('Frequency (Hz)')
                        plt.ylabel('PSD (V^2/Hz)')
                        plt.title(f"Frequency Response Plot {plot_counter} at t={int(elapsed_time)}s")
                        plt.grid(True)
                        filename = f"frequency_response_{plot_counter}.png"
                        plt.savefig(f"test_data/{filename}")
                        plt.close()  # Close the figure to free up memory

                        print(f"Saved {filename}")
                        
                        # Countdown of 5 seconds printed to terminal
                        for sec in range(5, 0, -1):
                            print(f"Next plot in {sec} seconds...", end="\r")
                            time.sleep(1)
                        start_time = time.time()
                        print(" " * 30, end="\r")  # Clear the line

                        # Update for next plot
                        last_plot_time = time.time()
                        plot_counter += 1

            except ValueError:
                pass  # Ignore invalid serial data

except KeyboardInterrupt:
    print("\nRecording stopped. Plotting final results...")

    # Close serial port
    ser.close()

    # Optionally, plot overall EEG band power over time
    plt.figure(figsize=(12, 6))

    plt.plot(timestamps, alpha_powers, label="Alpha (8-12 Hz)", color='blue')
    plt.plot(timestamps, beta_powers, label="Beta (12-30 Hz)", color='red')
    plt.xlabel("Time (s)")
    plt.ylabel("Normalized Power")
    plt.title("EEG Band Power Over Time")
    plt.legend()
    plt.grid()

    # plt.subplot(2, 1, 2)
    # plt.plot(timestamps, concentration_levels, label="Concentration Level", color='green')
    # plt.xlabel("Time (s)")
    # plt.ylabel("Concentration (Beta / (Alpha + Beta))")
    # plt.title("Concentration Level Over Time")
    # plt.legend()
    # plt.grid()

    plt.tight_layout()
    plt.show()
