import serial
import time
import threading
import numpy as np
import pandas as pd
from flask import Flask, jsonify
import joblib

# ------------------------------------------------
# Kalman Filter (Real-time)
# ------------------------------------------------
def kalman_filter(data, Q=1e-4, R=0.5):
    n = len(data)
    x_est = np.zeros(n)
    P = np.zeros(n)

    x_est[0] = data[0]
    P[0] = 1

    for k in range(1, n):
        x_pred = x_est[k-1]
        P_pred = P[k-1] + Q

        K = P_pred / (P_pred + R)
        x_est[k] = x_pred + K * (data[k] - x_pred)
        P[k] = (1 - K) * P_pred

    return x_est




SERIAL_PORT = '/dev/serial0'
BAUD_RATE = 9600

# -------------------- LOAD MODEL --------------------
model = joblib.load("gps_error_model.joblib")
FEATURE_NAMES = joblib.load("model_features.joblib")

print("? Model Loaded")
print("?? Features:", FEATURE_NAMES)

# -------------------- GLOBAL DATA --------------------
latest_data = {
    "packet_id": 0,
    "lat": 0,
    "lon": 0,
    "speed": 0,
    "altitude": 0,
    "course": 0,
    "sats": 0,
    "hdop": 0,
    "prediction": 0,
    "confidence": 0
}



def connect_serial():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
            time.sleep(2)
            ser.reset_input_buffer()
            print("? Serial Connected")
            return ser
        except:
            print("? Serial connect failed, retrying...")
            time.sleep(2)

ser = connect_serial()
def read_serial():
    global latest_data, ser


    while True:
        try:
            raw = ser.read_until(b'>').decode('utf-8', errors='ignore').strip()
            if '<' in raw:
                raw = raw[raw.index('<') + 1:]
            if raw.endswith('>'):
                raw = raw[:-1]
                
            raw_line = raw.strip()
            if not raw_line:
                continue
            print("?? PACKET:", raw_line)

                # ---------------- VALIDATION ----------------
            if ":" not in raw_line or raw_line.count(",") != 6:
                print("?? Corrupted packet:", raw_line)
                continue

            try:
                packet_id_str, data_part = raw_line.split(":")
                packet_id = int(packet_id_str)
                data = data_part.split(",")

                lat = float(data[0])
                lon = float(data[1])
                speed = float(data[2])
                course = float(data[3])
                sats = int(data[4])
                altitude = float(data[5])
                hdop = float(data[6])


            except:
                print("?? Conversion error:", raw_line)
                continue


                # ---------------- FEATURES ----------------
            feature_dict = {
                'Speed_kmph_filtered': speed,
                'Altitude_m_filtered': altitude,
                'Course_deg_filtered': course,
                'Sats_filtered': sats,
                'HDOPs_filtered': hdop,
                'speed_sat': speed * sats,
                'altitude_sat_ratio': altitude / (sats + 1),
                'hdop_sat_ratio': hdop / (sats + 1)
            }   

            features = pd.DataFrame([feature_dict])
            features = features[FEATURE_NAMES]

            print("? Features:\n", features)

                # ---------------- PREDICTION ----------------
            try:
                pred = float(model.predict(features)[0])
                
            except Exception as e:
                print("? Prediction error:", e)
                pred = 0, 

            print(f"?? Prediction: {pred:.3f}")

            latest_data = {
                "packet_id": packet_id,
                "lat": lat,
                "lon": lon,
                "speed": speed,
                "altitude": altitude,
                "course": course,
                "sats": sats,
                "hdop": hdop,
                "prediction": pred
                
            }

        except Exception as e:
            err = str(e)
            if  "device reports readiness" in err:
                continue
            print("? Serial error:", e)
            try:
                ser.close()
            except:
                pass
            time.sleep(2)
            ser = connect_serial()
            
# -------------------- FLASK APP --------------------
app = Flask(__name__)

@app.route("/data")
def get_data():
    return jsonify(latest_data)
    
# -------------------- MAIN --------------------
if __name__ == "__main__":
    t = threading.Thread(target=read_serial)
    t.daemon = True
    t.start()

    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader = False)
