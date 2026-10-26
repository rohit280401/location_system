
"""Raspberry Pi gateway for the ESP32/LoRa GPS monitor."""

import math
import threading
import time
from pathlib import Path

import joblib
import pandas as pd
import serial
from flask import Flask, jsonify

SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 9600
Q = 1e-5
R = 0.5
MODEL_DIR = Path(__file__).resolve().parent

model = joblib.load(MODEL_DIR / "gps_error_model.joblib")
FEATURE_NAMES = list(joblib.load(MODEL_DIR / "model_features.joblib"))

app = Flask(__name__)
latest_data = {}  # Empty until the first valid GPS packet arrives.
data_lock = threading.Lock()


class KalmanFilter1D:
    """One-dimensional Kalman filter that retains state between samples."""

    def __init__(self, q=Q, r=R):
        if q < 0 or r <= 0:
            raise ValueError("Q must be >= 0 and R must be > 0")
        self.q = q
        self.r = r
        self.estimate = None
        self.uncertainty = 1.0

    def update(self, measurement):
        measurement = float(measurement)
        if self.estimate is None:
            # Same initial condition as the training notebook's array filter.
            self.estimate = measurement
            return self.estimate

        predicted_uncertainty = self.uncertainty + self.q
        gain = predicted_uncertainty / (predicted_uncertainty + self.r)
        self.estimate += gain * (measurement - self.estimate)
        self.uncertainty = (1.0 - gain) * predicted_uncertainty
        return self.estimate


def parse_packet(raw):
    """Parse ESP32 packet: <ID:lat,lon,speed,course,sats,altitude,hdop>."""
    raw = raw.strip()
    if b"<" not in raw or not raw.endswith(b">"):
        return None
    payload = raw[raw.rfind(b"<") + 1 : -1].decode("ascii", errors="ignore")
    if payload.count(":") != 1:
        return None
    packet_id_text, values_text = payload.split(":", 1)
    parts = values_text.split(",")
    if len(parts) != 7:
        return None

    try:
        packet = {
            "packet_id": int(packet_id_text),
            "lat": float(parts[0]),
            "lon": float(parts[1]),
            "speed": float(parts[2]),
            "course": float(parts[3]),
            "sats": int(parts[4]),
            "altitude": float(parts[5]),
            "hdop": float(parts[6]),
        }
    except ValueError:
        return None

    if not all(math.isfinite(v) for v in packet.values()):
        return None
    if not (-90 <= packet["lat"] <= 90 and -180 <= packet["lon"] <= 180):
        return None
    if packet["sats"] <= 0 or packet["hdop"] < 0:
        return None
    if packet["lat"] == 0 and packet["lon"] == 0:
        return None  # Typical no-fix value from the ESP32 firmware.
    return packet


def new_filters():
    return {key: KalmanFilter1D() for key in ("speed", "altitude", "course", "sats", "hdop")}


def predict_error(packet, filters):
    speed = filters["speed"].update(packet["speed"])
    altitude = filters["altitude"].update(packet["altitude"])
    course = filters["course"].update(packet["course"])
    sats = filters["sats"].update(packet["sats"])
    hdop = filters["hdop"].update(packet["hdop"])

    feature_dict = {
        "Speed_kmph_filtered": speed,
        "Altitude_m_filtered": altitude,
        "Course_deg_filtered": course,
        "Sats_filtered": sats,
        "HDOPs_filtered": hdop,
        "speed_sat": speed * sats,
        "altitude_sat_ratio": altitude / (sats + 1.0),
        "hdop_sat_ratio": hdop / (sats + 1.0),
    }
    # Enforce the exact feature order used when the model was trained.
    features = pd.DataFrame([feature_dict])[FEATURE_NAMES]
    prediction = float(model.predict(features)[0])
    if not math.isfinite(prediction) or prediction < 0:
        raise ValueError(f"Invalid predicted error: {prediction}")
    return prediction


def read_serial():
    global latest_data

    while True:
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as port:
                print("Serial connected")
                filters = new_filters()  # Reset on a new connection.

                while True:
                    raw = port.read_until(b">")
                    if not raw:
                        continue
                    packet = parse_packet(raw)
                    if packet is None:
                        print("Skipping invalid/incomplete GPS packet")
                        continue

                    try:
                        prediction = predict_error(packet, filters)
                    except Exception as exc:
                        # Do not present a fabricated 0-metre error on failure.
                        print(f"Prediction failed: {exc}")
                        continue

                    packet["prediction"] = prediction
                    with data_lock:
                        latest_data = packet
                    print(f"Packet {packet['packet_id']}: GPS error estimate {prediction:.3f} m")

        except (serial.SerialException, OSError) as exc:
            print(f"Serial connection error: {exc}; retrying in 2 seconds")
            time.sleep(2)


@app.route("/data")
def get_data():
    with data_lock:
        return jsonify(latest_data.copy())


if __name__ == "__main__":
    threading.Thread(target=read_serial, daemon=True).start()
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
