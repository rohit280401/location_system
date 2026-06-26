# Smart Farm IoT Dashboard & AI Fertilizer Recommendation System

An end-to-end IoT and Machine Learning based Smart Farming System designed for precision agriculture. The project continuously monitors environmental conditions, compares sensor readings with crop-specific threshold values, and uses a Machine Learning model to recommend fertilizers whenever nutrient levels deviate from their optimal ranges.

The complete system consists of:

- Edge Field Node
- Central Gateway
- Machine Learning Engine
- Interactive Web Dashboard

The system is designed to minimize communication overhead while maximizing reliability for real-world agricultural deployment.

---

# Features

## Real-Time Sensor Monitoring

The system continuously monitors:

- Temperature
- Humidity
- Soil Moisture
- Nitrogen (N)
- Phosphorus (P)
- Potassium (K)

using sensors connected to the field node.

---

## Crop-Based Decision Making

Each crop has its own environmental requirements stored inside

```
crop_profiles.json
```

The edge node compares live sensor values with these thresholds before transmitting data.

---

## Edge Computing

Instead of sending every sensor value continuously, the field node performs local decision making.

If:

- Environment is healthy
- NPK values are within limits

only essential information is transmitted.

If an abnormal condition is detected, complete sensor data is forwarded to the gateway.

This significantly reduces communication overhead.

---

## Machine Learning Fertilizer Recommendation

Whenever abnormal NPK values are detected, the gateway executes a trained Random Forest classifier.

Input Features include:

- Temperature
- Humidity
- Moisture
- Nitrogen
- Phosphorus
- Potassium

Output:

Recommended fertilizer for correcting soil nutrient imbalance.

---

## Interactive Dashboard

The Flask web interface automatically updates every few seconds and displays three operating states.

### Normal State

- Green dashboard
- Healthy environment
- No fertilizer recommendation required

### Warning State

- Yellow dashboard
- Environmental parameters outside acceptable range

### Critical State

- Red dashboard
- NPK imbalance detected
- AI fertilizer recommendation displayed

---

# System Architecture

```
                     Sensors
                        │
                        │
                Field Node
        (Edge Processing Unit)
                        │
                        │
       Local Threshold Comparison
                        │
        ┌───────────────┴──────────────┐
        │                              │
Normal Conditions              Abnormal Conditions
        │                              │
 Reduced Data                  Complete Sensor Data
        │                              │
        └───────────────┬──────────────┘
                        │
                LoRa / Serial
                        │
                 Gateway Server
                        │
         Random Forest ML Model
                        │
              Flask Web Server
                        │
               Web Dashboard
```

---

# Technology Stack

## Programming

- Python 3

## Backend

- Flask

## Machine Learning

- Scikit-Learn
- Pandas
- NumPy
- Joblib

## Hardware Communication

- PySerial
- Modbus
- SPI

## Frontend

- HTML
- CSS
- JavaScript

---

# Repository Structure

```
.
├── app.py
├── gateway_code.py
├── Field_code.py
├── crop_profiles.json
├── model.ipynb
├── fertilizer_model.joblib
├── data_scaler.joblib
├── label_encoder.joblib
├── Fertilizer Prediction.csv
└── templates
    └── index.html
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/SmartFarm.git

cd SmartFarm
```

---

## Install Dependencies

```bash
pip install flask
pip install pandas
pip install numpy
pip install scikit-learn
pip install joblib
pip install pyserial
```

For the Field Node:

```bash
pip install adafruit-circuitpython-dht
pip install minimalmodbus
pip install spidev
```

---

# Running the Machine Learning Model

Open

```
model.ipynb
```

Train the Random Forest classifier.

The notebook generates

```
fertilizer_model.joblib

data_scaler.joblib

label_encoder.joblib
```

These files are automatically used by the gateway.

---

# Running the Field Node

```bash
python Field_code.py
```

---

# Running the Gateway

```bash
python app.py
```

Open

```
http://localhost:5000
```

to access the dashboard.

---

# Automatic Startup After Power Failure

To ensure that the gateway automatically starts whenever power is restored, a **systemd** service is used.

Create the service file:

```bash
sudo nano /etc/systemd/system/smartfarm.service
```

Paste:

```ini
[Unit]
Description=Smart Farm Gateway
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/SmartFarm
ExecStart=/usr/bin/python3 /home/pi/SmartFarm/gateway_code.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Reload systemd:

```bash
sudo systemctl daemon-reload
```

Enable automatic startup:

```bash
sudo systemctl enable smartfarm.service
```

Start the service:

```bash
sudo systemctl start smartfarm.service
```

Check status:

```bash
sudo systemctl status smartfarm.service
```

Stop service:

```bash
sudo systemctl stop smartfarm.service
```

Restart service:

```bash
sudo systemctl restart smartfarm.service
```

Disable automatic startup:

```bash
sudo systemctl disable smartfarm.service
```

This ensures that after every reboot or power failure, the gateway automatically resumes operation without requiring manual intervention.

---

# Power Optimization

Several software optimizations were implemented to reduce power consumption.

## Edge Processing

The field node filters unnecessary sensor data locally.

Only abnormal conditions trigger complete packet transmission.

This reduces processor activity and communication time.

---

## Reduced Communication

LoRa transmissions are performed only when necessary.

Since wireless transmission consumes significantly more power than local computation, minimizing radio activity greatly improves battery life.

---

## Sleep Interval

The field node executes

```python
time.sleep(5)
```

between sensing cycles.

This reduces CPU utilization and overall power consumption.

---

# Current Consumption Observations

Current measurements were performed during different stages of system operation.

| Operation | Observation |
|-----------|-------------|
| Idle System | Lowest current consumption |
| Sensor Reading | Slight increase in current |
| LoRa Transmission | Highest current consumption |
| Machine Learning Prediction | Small increase due to CPU computation |

### Observation

LoRa communication draws comparatively more current than other system operations.

Wireless transmission is the most power-intensive activity in the entire system.

Therefore, edge filtering was implemented to reduce unnecessary LoRa transmissions and improve overall power efficiency.

---

# Troubleshooting

## Serial Port Busy

Find the process using the serial port:

```bash
sudo lsof /dev/ttyS0
```

Kill the process:

```bash
sudo kill <PID>
```

If required:

```bash
sudo kill -9 <PID>
```

---

## Flask Port Already in Use

Find the process:

```bash
sudo lsof -i :5000
```

Terminate it:

```bash
sudo kill -9 <PID>
```

---

# Design Highlights

- Edge Computing
- Machine Learning Integration
- Flask Web Server
- Dynamic Dashboard
- Automatic System Recovery using systemd
- Reduced LoRa Communication
- Low Power Operation
- Modular Architecture
- Real-Time Monitoring

---

# Future Improvements

- Cloud Integration
- MQTT Support
- AWS IoT Core Integration
- Mobile Application
- Solar Powered Deployment
- OTA Firmware Updates
- Predictive Crop Analytics
- Historical Data Visualization

---

# License

This project is intended for educational and research purposes.
