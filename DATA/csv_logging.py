import serial
import csv

PORT = "COM3"
BAUD = 115200 

ser = serial.Serial(PORT, BAUD, timeout=1)

with open("navic_clean_log_walking_4.csv", "a", newline="") as file:
    writer = csv.writer(file)

    print("Logging started... Press Ctrl+C to stop")

    try:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if not line:
                continue

            parts = line.split(",")

            # Expect exactly 11 fields
            if len(parts) == 11:
                writer.writerow(parts)
                file.flush()
                print("Stored:", line)

    except KeyboardInterrupt:
        print("\nLogging stopped.")
    finally:
        ser.close()
