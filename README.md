# Tactical Soldier Monitoring & Geospatial ML Error Correction System

An end-to-end, production-grade IoT and Machine Learning ecosystem engineered for real-time tactical asset tracking and high-precision geospatial telemetry correction.

The system captures micro-telemetry from a mobile **Hardware Node** (ESP32 via FreeRTOS + NavIC/GPS + LoRa), executes streaming statistical filtering and localized machine learning inference (`Scikit-Learn` + `Joblib`) on an **Edge Gateway Node (Raspberry Pi)** to predict and correct positional deviation errors, and displays live paths on an **Interactive Web Dashboard** featuring live Leaflet.js rendering and dynamic error-radius visual mapping.

---

## 🚀 Key Architectural Features

- **Asynchronous Multi-Tasking Edge Firmware:** The hardware transceiver leverages an ESP32 micro-controller configured with FreeRTOS. It separates blocking serial parsing tasks from telemetry broadcasting over mutually exclusive semaphore rings (`gpsMutex`), ensuring deterministic data loops.
- **Dual-Stage Geospatial Optimization:**
  - **Stage 1 (Statistical):** Implements a real-time, mathematical **Kalman Filter** directly on the Edge Gateway to dynamically smooth noisy raw latitude/longitude inputs.
  - **Stage 2 (Predictive):** Leverages an embedded machine learning pipeline trained to predict localized error bounds based on constellation geometries (`HDOP`, `Satellites in view`, `Speed`, and `Altitude`).
- **State-Driven Command HUD:** A modern web client constructed with a custom sci-fi/tactical visual system. It communicates via an active server polling cycle to render dynamic live track coordinates, calculate path bounding errors, and map real-time precision rings (green, orange, red) corresponding directly to ML deviation metrics.
- **Auto-Boot Unattended Fault Tolerance:** Fully automated system instantiation through custom `systemd` daemon controls, guaranteeing instantaneous platform initialization on field power recovery.

---

## 🗺️ System Topology & Telemetry Flow

```text
[ ESP32 Field Node ] (NavIC/GPS Array via FreeRTOS + Mutex Guards)
         │
         │ (Formatted Telemetry String: <ID:Lat,Lon,Spd,Crs,Sats,Alt,Hdp>)
         ▼
[ Hardware Telemetry Lines / LoRa Serial ]
         │
         │ (Non-blocking, background thread daemon connection)
         ▼
[ Raspberry Pi Edge Gateway ] ◄──► [ Production ML Pipeline ]
   (Flask Server + Kalman Engine)     (Pre-trained Regressor + Scaler Matrix)
         │
         ▼
[ Web Presentation Interface ] ──► (Active Polling / Dynamic Leaflet.js Mapping Matrix)
```

---

## 📦 Production Tech Stack

| Tier | Technologies Utilized |
|---|---|
| Hardware & FreeRTOS Layer | ESP32, HardwareSerial, FreeRTOS Semaphores, NMEA/NavIC Parser (TinyGPS++), LoRa |
| Infrastructure & Networking | Python 3, Flask Web Framework, Multi-threaded Workers, REST APIs, HTTP Requests |
| Machine Learning Pipeline | Jupyter, Pandas, NumPy, Scikit-Learn Regression Models, Joblib Serializers, OSRM API |
| Frontend/Presentation Layer | HTML5 Semantic Layout, Leaflet.js Mapping API, Share Tech Mono CSS HUD Styling |

---

## 📂 Repository Blueprint

```text
.
├── ESP_CODE/
│   └── soldier_monitoring_system.ino      # ESP32 Firmware (FreeRTOS Tasks & Mutex-Guarded GPS Loops)
│
├── DATA/
│   ├── csv_logging.py                     # Logs Telemetry Data from Serial to CSV
│   └── got_exact_data.py                  # Haversine Distance Calculation & OSRM Road Snapping
│
├── MODEL_TRAINING/
│   └── model.ipynb                        # ML Model Training, Feature Engineering & Evaluation
│
├── RPI/
│   └── rpi.py                             # Edge Gateway (Serial Processing, Kalman Filter & ML Inference)
│
├── WEBPAGE/
│   ├── app.py                             # Flask Web Application
│   └── templates/
│       └── index.html                     # Interactive Leaflet.js Tactical Dashboard
│
└── README.md
```
---

## 🔋 Low-Power Consumption & Autonomous Resiliency Design

To support field operations where assets rely on limited battery configurations, the architecture implements specialized hardware and software power management techniques:

### 1. Telemetry Duty-Cycle Optimization & Compute Mitigation

- **Interval-Based Active LoRa Bursts:** Radio transmission accounts for the highest power consumption on an embedded node. The hardware firmware limits transmission to structured cycles using `vTaskDelay`, moving the peripheral into an idle state between loops to conserve battery.
- **Deterministic Filtering at the Edge:** Positional computing is split across the topology. The edge node bypasses structural calculation and focuses on low-overhead formatting, shifting mathematical data calculations to the plugged gateway.

### 2. Auto-Boot Resilience Configuration (systemd Integration)

To recover seamlessly from field power drops or reboots without manual intervention, a dedicated system service monitors the runtime gateway processes.

Configure the service definition file at `/etc/systemd/system/tactical_gps.service`:

```ini
[Unit]
Description=Tactical GPS Gateway & Predictive Analytics Engine
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/tactical-gps-repo
ExecStart=/usr/bin/python3 rpi.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Apply properties to load and lock the process configuration on boot:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tactical_gps.service
sudo systemctl start tactical_gps.service
```

---

## 🛠️ Real-World Engineering Hurdles & Structural Troubleshooting

### 1. Hardware Initialization Risk & Live Deployment Vulnerabilities

**The Problem:** Deploying, mounting, and verifying active tracking hardware inside a field configuration to aggregate structural telemetry is risky. Sensor drops, unstable physical connections, and transient power issues can interrupt data streams, rendering standard validation setups highly fragile.

**The Engineering Fix:** Engineered a decoupled data logging system (`csv_logging.py`) with explicit string length protection (`len(parts) == 11`) and runtime block flushing (`file.flush()`). This safeguarded in-flight telemetric logs from corruption during sudden hardware dropouts, turning raw telemetry collections into reproducible training sets.

### 2. Raw Sensor Deviations vs. OSRM Road-Snapping Engine Limitations

**The Problem:** In open-field testing, raw GPS reading vectors fluctuate based on atmospheric boundaries or satellite geometry constraints. Attempting to pass raw coordinates straight into the Open Source Routing Machine (OSRM) API caused erratic snapping logic, because noisy reading coordinates deviated too far from valid road nodes.

**The Engineering Fix:** Implemented a multi-stage software fix (`got_exact_data.py` & `rpi.py`). Raw inputs are processed through a mathematical Kalman Filter to smooth coordinate noise. Next, a custom Haversine Distance Calculator estimates physical error distances in meters. This filtered vector is used to train a predictive model (`gps_error_model.joblib`), ensuring clean geospatial snapping bounding criteria before hitting the OSRM endpoint.

### 3. Peripheral Device Contention (USART Bus Lock / Device Busy Error)

**The Problem:** During iterative runtime restarts, serial data hooks often threw a critical `SerialException: [Errno 16] Device or resource busy`. This occurred because orphaned background worker execution lines held persistent file descriptor locks on target hardware interfaces (`/dev/serial0` or `/dev/ttyS0`).

**The Engineering Fix:** Resolved the port lock dynamically by utilizing system state checkers to identify and eliminate the parent PID before rebooting execution trees:

```bash
# Step A: Identify the exact Process ID locking the target UART bus
sudo lsof /dev/serial0

# Step B: Purge the conflicting process line to unlock the interface
sudo kill -9 <PID_RESULT>

# Step C: Reclaim bound Flask sockets if network ports hang on restart
sudo lsof -i :5001
sudo kill -9 <PID_RESULT>
```

---

## 💡 Key Design Patterns Highlighted

- **Asynchronous Thread Concurrency:** Separates hardware I/O bottlenecks by isolating the serial listener routine onto a dedicated Python `threading.Thread`. This keeps the main web serving block entirely non-blocking and highly responsive.
- **Decoupled Idempotent States:** Employs functional frontend polling routines that fetch telemetric slices every 1–2 seconds. The client remains state-agnostic, updating map matrices dynamically based strictly on incoming data properties.
