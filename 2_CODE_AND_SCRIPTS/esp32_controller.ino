/*
 * ESP32-S3 Water Treatment Controller
 * Features: 
 * - MQTT over TLS (Security Node Integration)
 * - Modbus TCP Server (SCADA Integration)
 * - Automated Tank Management & Safety Logic
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ModbusIP_ESP8266.h> // Common library for Modbus TCP
#include <OneWire.h>
#include <DallasTemperature.h>

// --- NETWORK CONFIGURATION ---
const char* ssid = "YOUR_WIFI_SSID";         // UPDATE THIS
const char* password = "YOUR_WIFI_PASSWORD"; // UPDATE THIS
const char* mqtt_server = "10.27.38.206";    // Raspberry Pi 5 IP
const int mqtt_port = 8883;                  // TLS Port
const char* mqtt_user = "naim";
const char* mqtt_pass = "1234";

// --- PIN ASSIGNMENTS (Revised to avoid conflicts) ---
#define FLOAT_PIN 12        
#define PUMP_RELAY_PIN 7     
#define CURRENT_SENSOR_PIN 37
#define PRESSURE_PIN 4      
#define ONE_WIRE_BUS 1       

// --- CONSTANTS & CALIBRATION ---
#define ZERO_RAW 1850        // Calibrated zero for current sensor
#define SENSITIVITY 160.0    // A/V sensitivity
#define MAX_SAFE_CURRENT 2.0 // Safety shut-off (Amps)
#define MAX_PRESSURE_V 2.5   // Safety shut-off (Volts)
#define PUBLISH_INTERVAL 5000 // Publish data every 5 seconds

// --- CA CERTIFICATE (Mosquitto TLS) ---
const char* ca_cert = 
"-----BEGIN CERTIFICATE-----\n"
"MIIFfzCCA2egAwIBAgIUGSkMc19jQgszlVpJFPDW2k8vPcYwDQYJKoZIhvcNAQEL\n"
"BQAwTjELMAkGA1UEBhMCVVMxDjAMBgNVBAgMBVN0YXRlMQ0wCwYDVQQHDARDaXR5\n"
"MQwwCgYDVQQKDANJb1QxEjAQBgNVBAMMCUN1c3RvbSBDQTAgFw0yNjAxMjcxMzI4\n"
"MzRaGA8yMTI2MDEwMzEzMjgzNFowTjELMAkGA1UEBhMCVVMxDjAMBgNVBAgMBVN0\n"
"YXRlMQ0wCwYDVQQHDARDaXR5MQwwCgYDVQQKDANJb1QxEjAQBgNVBAMMCUN1c3Rv\n"
"bSBDQTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAI3wL30/SMTsalEO\n"
"5REyR5r5BV800zrKOp9FvOF5r1yqqygPVWdDPN9QT8M+yaipPxSJ+5V92BiLhDuv\n"
"6BNR9aD/3+UVdoHmg6ocGHNqmtY4aQS780bZbuEWGvMlRLoaJrwb7BjUUh8uijbR\n"
"XOmfAkgWJmeW2BuXf3Owa73ZKMzbbKB8PnqI7rIBxZEV242ymMpUyjSmcBINWIyj\n"
"nGVT6bOcgMs8d4DsQjmrB6sT6/a/Zg+Y8iTwvGMM2ZK6OITfapuLd8LVu84LMnXy\n"
"KY0wwLcw4QzIpo+KoeFvD1JvuAJy+7PYmr4/YNrwSLMG7L4xJkZgLhzz+XJDOXnB\n"
"WXTcbrepoTPI6v6nMUmio3zRvJPUO0bzZIs2IOP2Ooq4OJfa/A8vuVqMPeh/60Gw\n"
"Oh/KsCUlep93oqu9Mhi16/FzfT87SxvLSre2kcqcv3arw1xOOiaR/On6WyR/LfwY\n"
"itzm2VxrxamZGpOzdk2sa45aXTAgZ3yXgwA8iCJsV1vn7JOXyblVy6v/nq7VISrz\n"
"kby2FtgYt1/bOTKGDeM8jq8q8tklkI0KbOQc1Vje9rQb803Rt+RxHLjhO1p6giQZ\n"
"Vtp+A5psM+oss7NqoBNGfnZB8WmlUssU2B+N5lnYECNB5CgZ2KuyZ/2k97uYP7an\n"
"h5IDHCLYpCP43tcqrJdjvkQ8lyDRAgMBAAGjUzBRMB0GA1UdDgQWBBQvEepiIBcs\n"
"b58GJjuvCq1SUZy+ETAfBgNVHSMEGDAWgBQvEepiIBcsb58GJjuvCq1SUZy+ETAP\n"
"BgNVHRMBAf8EBTADAQH/MA0GCSqGSIb3DQEBCwUAA4ICAQBO30262LjoeWdH1UL/\n"
"9ySXelLY1LrlGzpqymDTlLk0+nFQ9Yan+YjquRt515NiG/O0o8SpGNRTKliZfMT5\n"
"952IcKGNWkSbl0Hr8AwQtS4AfTvrxCc7cgStTtFXdG0CeiJU7mWlwhkHWwn/2yWE\n"
"0e2BC8+rPpC2cUf2k37+dYS5Wt4J2gI6i4c3d2tsh5QFLfXG96OUWxWSYtjZLIHu\n"
"UtuXDF5BsHkvNcPHgH/V3XHfusIA48PpjeI+K0luDY8qF4Nyh5zvNIVAJx3XL049\n"
"VvjXq7kLKrAL2xA0qgG+hbc9PY8+B+P8viHpl590fxoRUtZthiKy4qAOifzJNDjp\n"
"oGdE8JKzB8mDSrYVtmWGKmF4euoLpOeknBb/x9hXhBSFiRzynM7LFJx3S8xOqPAL\n"
"T1Q3y9/fvoUQKGRTck9fLee8Y3SWP8QZr05xAHw2v35YVJoqo3xqwjV4nZ8HIzps\n"
"2zD2utH7YdFfrYjrhzSa+koEx9bmnpe8Qta5kPuh9HB4B6LZDFp+FwJpGpJq0LKi\n"
"WvT5Uc6qNmj24kMS/88ZYJXYkjWeDqa6qOEsvD2M30uFXigG/AEwOTKiZvB6qapL\n"
"062xosrG29n3KlwT2EjT6V8qQLSB7sTUQOL3LRXLo+Oi2r2nchUOGasfdGW+oBgE\n"
"uBUPSZKbSpvJg9w+knQgNrnz1g==\n"
"-----END CERTIFICATE-----";

// --- OBJECTS ---
WiFiClientSecure espClient;
PubSubClient client(espClient);
ModbusIP mb;
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// --- GLOBAL VARIABLES ---
float temperature = 0;
float currentAmps = 0;
float pressureVolts = 0;
int floatState = 0;
bool pumpRunning = false;
bool systemIntervention = false;
unsigned long lastPublish = 0;

// --- MODBUS REGISTER MAPPING ---
// Use Input Registers (Read-only for Master)
const int REG_TEMP = 100;
const int REG_CURRENT = 101;
const int REG_PRESSURE = 102;
const int REG_FLOAT = 103;
const int REG_PUMP = 104;
const int REG_INTERVENTION = 105;

// --- FUNCTIONS ---

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);

  // Security Intervention Logic
  if (String(topic) == "ics/security/intervention") {
    if (message == "SHUTDOWN") {
      systemIntervention = true;
      digitalWrite(PUMP_RELAY_PIN, LOW); // Force Stop
      Serial.println("!! EMERGENCY: AI Security Node triggered SHUTDOWN");
    } else if (message == "RESET") {
      systemIntervention = false;
      Serial.println(">> Security Reset: Resuming normal operation");
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32S3_Controller", mqtt_user, mqtt_pass)) {
      Serial.println("connected");
      client.subscribe("ics/security/intervention");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  // GPIO Setup
  pinMode(FLOAT_PIN, INPUT_PULLUP);
  pinMode(PUMP_RELAY_PIN, OUTPUT);
  digitalWrite(PUMP_RELAY_PIN, LOW); // Start OFF

  // Sensors Setup
  sensors.begin();
  
  // WiFi & TLS Setup
  setup_wifi();
  espClient.setCACert(ca_cert);
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // Modbus Setup
  mb.server();
  mb.addIreg(REG_TEMP);
  mb.addIreg(REG_CURRENT);
  mb.addIreg(REG_PRESSURE);
  mb.addIreg(REG_FLOAT);
  mb.addIreg(REG_PUMP);
  mb.addIreg(REG_INTERVENTION);

  Serial.println("ESP32-S3 System Initialized");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  mb.task(); // Modbus handling

  // 1. READ SENSORS
  sensors.requestTemperatures();
  temperature = sensors.getTempCByIndex(0);
  
  int currentRaw = analogRead(CURRENT_SENSOR_PIN);
  currentAmps = (currentRaw - ZERO_RAW) / SENSITIVITY;
  
  int pressureRaw = analogRead(PRESSURE_PIN);
  pressureVolts = pressureRaw * (3.3 / 4095.0);
  
  floatState = digitalRead(FLOAT_PIN); // LOW = Water High (Tank Full)

  // 2. SAFETY & PUMP LOGIC
  bool isWaterHigh = (floatState == LOW);
  bool isOverCurrent = (currentAmps > MAX_SAFE_CURRENT);
  bool isOverPressure = (pressureVolts > MAX_PRESSURE_V);

  if (systemIntervention) {
    // Blocked by AI Security Node
    pumpRunning = false;
  } else if (isWaterHigh || isOverCurrent || isOverPressure) {
    pumpRunning = false;
  } else {
    // Normal level control: if tank not high, pump can run
    // (Assuming a simple float-based fill logic)
    pumpRunning = true;
  }

  digitalWrite(PUMP_RELAY_PIN, pumpRunning ? HIGH : LOW);

  // 3. UPDATE MODBUS REGISTERS
  mb.Ireg(REG_TEMP, (int)(temperature * 100)); // Precise to 0.01C
  mb.Ireg(REG_CURRENT, (int)(currentAmps * 1000)); // Precise to 1mA
  mb.Ireg(REG_PRESSURE, (int)(pressureVolts * 1000)); // Precise to 1mV
  mb.Ireg(REG_FLOAT, floatState == LOW ? 1 : 0);
  mb.Ireg(REG_PUMP, pumpRunning ? 1 : 0);
  mb.Ireg(REG_INTERVENTION, systemIntervention ? 1 : 0);

  // 4. PUBLISH TELEMETRY
  if (millis() - lastPublish > PUBLISH_INTERVAL) {
    String payload = "{";
    payload += "\"temperature\":" + String(temperature) + ",";
    payload += "\"current\":" + String(currentAmps, 3) + ",";
    payload += "\"pressure\":" + String(pressureVolts, 3) + ",";
    payload += "\"float_high\":" + String(floatState == LOW ? "true" : "false") + ",";
    payload += "\"pump_on\":" + String(pumpRunning ? "true" : "false") + ",";
    payload += "\"intervention\":" + String(systemIntervention ? "true" : "false");
    payload += "}";
    
    client.publish("ics/telemetry/data", payload.c_str());
    
    // Debug Output
    Serial.print("Data Published: ");
    Serial.println(payload);
    
    lastPublish = millis();
  }

  delay(100); // Small delay for stability
}
