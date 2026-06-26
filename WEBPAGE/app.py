from flask import Flask, jsonify, render_template
import requests
import threading
import time
import os
app = Flask(__name__)

RPI_URL = "http://192.168.137.10:5001/data"  # ← replace with your RPi's IP e.g. 192.168.x.x

latest_data = {
    "packet_id":  0,
    "lat":        0.0,
    "lon":        0.0,
    "speed":      0.0,
    "altitude":   0.0,
    "course":     0.0,
    "sats":       0,
    "hdop":       0.0,
    "prediction": 0.0,
    "time":       "--:--:--"
}

# -------------------------------
# POLL RPi EVERY SECOND
# -------------------------------
def poll_rpi():
    global latest_data
    while True:
        try:
            res  = requests.get(RPI_URL, timeout=2)
            data = res.json()

            latest_data = {
                "packet_id":  data.get("packet_id", 0),
                "lat":        data.get("lat", 0.0),
                "lon":        data.get("lon", 0.0),
                "speed":      data.get("speed", 0.0),
                "altitude":   data.get("altitude", 0.0),
                "course":     data.get("course", 0.0),
                "sats":       int(data.get("sats", 0)),
                "hdop":       data.get("hdop", 0.0),
                "prediction": data.get("prediction", 0.0),
                "time":       time.strftime("%H:%M:%S")
            }
            print(f"✅ PKT {latest_data['packet_id']} | "
                  f"{latest_data['lat']}, {latest_data['lon']} | "
                  f"err={latest_data['prediction']:.3f}m")

        except Exception as e:
            print("❌ RPi fetch failed:", e)

        time.sleep(1)

# -------------------------------
# ROUTES
# -------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def get_data():
    return jsonify(latest_data)

# -------------------------------
# MAIN
if __name__ == "__main__":
    threading.Thread(target=poll_rpi, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)