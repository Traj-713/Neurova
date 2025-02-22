import serial
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
import time

# Define EEG frequency bands (in Hz)
BANDS = {
    "delta": (0.5, 4),
    "theta": (4, 8),
    "alpha": (8, 12),  # Relaxation
    "beta": (12, 30),  # Concentration
    "gamma": (30, 40)
}

# Sampling settings
fs = 250              # Sampling frequency in Hz
duration = 30         # Duration (in seconds) of each recording segment
num_samples = fs * duration  # Total samples to record per segment

# Serial port setup (update COM port)
arduino_port = "/dev/cu.usbmodem2101"  # Change to the correct COM port (e.g., /dev/ttyUSB0 for Linux)
baud_rate = 115200
ser = serial.Serial(arduino_port, baud_rate, timeout=1)

# Bandpass filter function (to isolate bands)
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

plot_counter = 1
print("Starting continuous EEG recording. Press Ctrl+C to stop.")

try:
    while True:
        eeg_data = []
        print(f"\nRecording EEG data for {duration} seconds (Plot {plot_counter})...")
        # Reset elapsed time for each segment
        segment_start_time = time.time()

        # Collect data for 'duration' seconds (or num_samples samples)
        while len(eeg_data) < num_samples:
            line = ser.readline().decode().strip()
            if line:
                try:
                    eeg_value = float(line)  # Assuming each line is a single EEG value
                    eeg_data.append(eeg_value)
                except ValueError:
                    pass  # Ignore invalid data

        # Calculate elapsed time for the current segment
        elapsed_time = time.time() - segment_start_time

        # Convert collected data to a NumPy array
        eeg_data = np.array(eeg_data)

        # Compute FFT on the data
        frequencies = np.fft.fftfreq(len(eeg_data), d=1/fs)
        fft_values = np.fft.fft(eeg_data)

        # Consider only the positive frequencies
        half = len(frequencies) // 2
        positive_frequencies = frequencies[:half]
        positive_fft_values = np.abs(fft_values[:half])

        # Compute power for frequency bands
        band_powers = compute_band_power(eeg_data, fs)
        normalized_powers = normalize_powers(band_powers)

        # Calculate concentration level: Beta / (Alpha + Beta)
        concentration_level = normalized_powers['beta'] / (normalized_powers['alpha'] + normalized_powers['beta'])

        # Create the plot with two subplots:
        # (1) Frequency spectrum (FFT result)
        # (2) Concentration level (displayed as a horizontal line for the segment)
        plt.figure(figsize=(12, 6))
        
        # Frequency spectrum plot
        plt.subplot(2, 1, 1)
        plt.plot(positive_frequencies, positive_fft_values, color='magenta')
        plt.title(f'Frequency Spectrum of EEG Signal (Plot {plot_counter})\nElapsed Time: {elapsed_time:.1f}s')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Amplitude')
        plt.grid()

        # Concentration level plot
        plt.subplot(2, 1, 2)
        # For demonstration, we show the concentration level as a horizontal line across the segment
        plt.plot([0, duration], [concentration_level, concentration_level], label="Concentration Level", color='green')
        plt.xlabel("Time (s)")
        plt.ylabel("Concentration Level")
        plt.title("Concentration Level Over 30 Seconds")
        plt.legend()
        plt.grid()

        plt.tight_layout()
        filename = f"eeg_plot_{plot_counter}.png"
        plt.savefig(f"test_data/{filename}")
        plt.close()
        print(f"Saved {filename} | Concentration Level: {concentration_level:.2f}")

        # 5-second countdown before next recording segment
        for sec in range(5, 0, -1):
            print(f"Next recording starts in {sec} seconds...", end="\r")
            time.sleep(1)
        print(" " * 40, end="\r")  # Clear the line

        plot_counter += 1

except KeyboardInterrupt:
    print("\nEEG recording stopped. Closing serial port...")
    ser.close()
    print("Program terminated.")
