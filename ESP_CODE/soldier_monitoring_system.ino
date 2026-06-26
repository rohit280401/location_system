#include <TinyGPS++.h>

TinyGPSPlus gps;

#define RXD2 16
#define TXD2 17
#define RXD1 26
#define TXD1 25

HardwareSerial navicSerial(2);
HardwareSerial LoRaSerial(1);

SemaphoreHandle_t gpsMutex;

uint32_t packet_id = 0;

// Shared variables (Initialized to 0)
double latitude = 0, longitude = 0;
double g_speed = 0, g_altitude = 0, g_course = 0, g_hdop = 0;
int g_sats = 0;

// ====================== GPS TASK ======================
void gpsTask(void *pvParameters) {
  while (1) {
    while (navicSerial.available() > 0) {
      gps.encode(navicSerial.read());
    }

    // Check if a full NEMA sentence was processed
    if (gps.location.isUpdated()) {
      if (xSemaphoreTake(gpsMutex, portMAX_DELAY)) {
        
        latitude  = gps.location.lat();
        longitude = gps.location.lng();
        g_speed   = gps.speed.kmph();
        g_altitude = gps.altitude.meters();
        g_course  = gps.course.deg();
        g_sats    = gps.satellites.value();
        g_hdop    = gps.hdop.hdop();

        xSemaphoreGive(gpsMutex);
      }
    }
    vTaskDelay(pdMS_TO_TICKS(10)); 
  }
}

// ====================== LORA TASK ======================
void loraTask(void *pvParameters) {
  char packet[150];

  while (1) {
    double lat, lon, spd, alt, crs, hdp;
    int sat;

    // Safely copy global values to local variables
    if (xSemaphoreTake(gpsMutex, portMAX_DELAY)) {
      lat = latitude;
      lon = longitude;
      spd = g_speed;
      alt = g_altitude;
      crs = g_course;
      sat = g_sats;
      hdp = g_hdop;
      xSemaphoreGive(gpsMutex);
    }

    packet_id++;

    // FIX: Match the order of variables to the format string exactly
    // Format: <ID:Lat,Lon,Spd,Crs,Sats,Alt,Hdop>
    snprintf(packet, sizeof(packet),
             "<%lu:%.6f,%.6f,%.2f,%.2f,%d,%.2f,%.2f>",
             (unsigned long)packet_id, lat, lon, spd, crs, sat, alt, hdp);

    LoRaSerial.println(packet);
    
    Serial.print("Sent: ");
    Serial.println(packet);

    vTaskDelay(pdMS_TO_TICKS(1000)); // Send every 1 seconds
  }
}

void setup() {
  Serial.begin(115200);

  navicSerial.begin(115200, SERIAL_8N1, RXD2, TXD2);
  LoRaSerial.begin(9600, SERIAL_8N1, RXD1, TXD1);

  gpsMutex = xSemaphoreCreateMutex();

  xTaskCreatePinnedToCore(gpsTask, "GPSTask", 4096, NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(loraTask, "LoRaTask", 4096, NULL, 1, NULL, 0); 
}

void loop() {
  // FreeRTOS handles the rest
}