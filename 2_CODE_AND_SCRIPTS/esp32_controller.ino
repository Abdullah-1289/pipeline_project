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
// Modbus: make optional. If you install an ESP32 Modbus IP library, set
// USE_MODBUS to 1 and update the include below to the library header you have.
#ifndef USE_MODBUS
#define USE_MODBUS 1
#endif
#if USE_MODBUS
#include <ModbusTCPSlave.h> // Modbus TCP server/slave for ESP32
#endif
#ifndef USE_MODBUS_CLIENT
#define USE_MODBUS_CLIENT 0
#endif
#if USE_MODBUS_CLIENT
#include <SchneiderModbusTCP.h>
#endif
#include <OneWire.h>
#include <DallasTemperature.h>

// --- NETWORK CONFIGURATION ---
const char* ssid = "YOUR_WIFI_SSID";         // UPDATE THIS
const char* password = "YOUR_WIFI_PASSWORD"; // UPDATE THIS
const char* mqtt_server = "10.27.38.206";    // Raspberry Pi 5 IP
const int mqtt_port = 8883;                  // TLS Port
const char* mqtt_user = "naim";
const char* mqtt_pass = "1234";

// --- PIN ASSIGNMENTS ---
// Flow (hall) sensor
const int FLOW_PIN = 37; // YF-S201 pulses

// Pressure sensors (analog) - two sensors
const int PRESSURE_PINS[] = {6, 7}; // ADC-capable pins

// Temperature OneWire bus
#define ONE_WIRE_BUS 35

// Current sensors (analog) - two sensors
const int CURRENT_PINS[] = {40, 41};

// Float switches: tank A low/high then tank B low/high
const int FLOAT_A_LOW = 10;
const int FLOAT_A_HIGH = 11;
const int FLOAT_B_LOW = 12;
const int FLOAT_B_HIGH = 13;

// Pump relays and solenoids
const int PUMP1_RELAY_PIN = 16; // motor A
const int PUMP2_RELAY_PIN = 47; // motor B
const int SOLENOID_PIN = 20;    // valve between tanks

// --- CONSTANTS & CALIBRATION ---
#define ZERO_RAW 1850            // Calibrated zero for ACS712 (raw ADC)
#define SENSITIVITY 160.0        // Calibration factor (raw -> A)
#define MAX_SAFE_CURRENT 2.0     // Safety shut-off (Amps)
#define PUBLISH_INTERVAL 5000    // Publish data every 5 seconds
#define PULSES_PER_LITER 450.0   // YF-S201 pulses per liter (adjust as needed)

// Pressure sensor calibration (0.5V -> 0 PSI, 4.5V -> 100 PSI)
#define PRESSURE_V_MIN 0.5
#define PRESSURE_V_MAX 4.5
#define PRESSURE_PSI_MAX 100.0

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
#if USE_MODBUS
WiFiClientSecure espClient;
#else
WiFiClientSecure espClient;
#endif
PubSubClient client(espClient);

#if USE_MODBUS
WiFiServer mbServer(MODBUS_TCP_SLAVE_DEFAULT_PORT);
ModbusTCPSlave modbus;
// Holding registers array for Modbus master reads/writes
const uint8_t MB_HOLDINGS = 16;
uint16_t holdingRegisters[MB_HOLDINGS];
// mapped holding register indexes
const uint8_t HREG_TEMP = 0;
const uint8_t HREG_CURRENT = 1;
const uint8_t HREG_PRESSURE = 2;
const uint8_t HREG_FLOAT = 3;
const uint8_t HREG_PUMP = 4;
const uint8_t HREG_INTERVENTION = 5;
// extra registers
const uint8_t HREG_PHASE = 6;
const uint8_t HREG_VALVE = 7;
const uint8_t HREG_SAFETY = 8;
const uint8_t HREG_A_HIGH = 9;
const uint8_t HREG_B_LOW = 10;
#endif

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);
#if USE_MODBUS_CLIENT
SchneiderModbusTCP modbusClient;
// Modbus client target configuration (example)
const char* MODBUS_CLIENT_HOST = "192.168.3.131";
const uint16_t MODBUS_CLIENT_PORT = 503;
const uint16_t MODBUS_CLIENT_SLAVEID = 191; // device unit id
const uint16_t MODBUS_CLIENT_START_REG = 71; // starting register to read
const uint16_t MODBUS_CLIENT_REG_COUNT = 8;  // number of 16-bit registers to read
const unsigned long MODBUS_CLIENT_POLL_MS = 5000; // poll interval
unsigned long lastModbusClientPoll = 0;
#endif

// --- GLOBAL VARIABLES ---
float temperatures[2] = {0,0};
float pressures[2] = {0,0};
float currents[2] = {0,0};
// no float array; read individual pins
bool pumpRunning1 = false; // motor A
bool pumpRunning2 = false; // motor B
bool systemIntervention = false;
unsigned long lastPublish = 0;

// --- MODBUS REGISTER MAPPING ---
const int REG_TEMP = 100;
const int REG_CURRENT = 101;
const int REG_PRESSURE = 102;
const int REG_FLOAT = 103;        // tank A low float
const int REG_PUMP = 104;
const int REG_INTERVENTION = 105;
const int REG_PHASE = 106;        // transfer phase A→B or B→A
const int REG_VALVE = 107;        // valve opening flag
const int REG_SAFETY = 108;       // safety trip/intervention
const int REG_A_HIGH = 109;       // tank A high float
const int REG_B_LOW = 110;        // tank B low float

// Flow measurement
volatile unsigned long flowPulseCount = 0;
unsigned long lastFlowCalc = 0;
float flow_lpm = 0.0;

// --- FLOW INTERRUPT HANDLER ---
void IRAM_ATTR flowPulse() {
  flowPulseCount++;
}

// --- WIFI / MQTT helpers ---
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
  String message;
  for (unsigned int i = 0; i < length; i++) message += (char)payload[i];
  Serial.printf("Message arrived [%s] %s\n", topic, message.c_str());

  if (String(topic) == "ics/security/intervention") {
    if (message.indexOf("SHUTDOWN") >= 0) {
      systemIntervention = true;
      digitalWrite(PUMP1_RELAY_PIN, LOW);
      digitalWrite(PUMP2_RELAY_PIN, LOW);
      Serial.println("!! EMERGENCY: SHUTDOWN");
    } else if (message.indexOf("RESET") >= 0) {
      systemIntervention = false;
      Serial.println(">> Security Reset");
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

#if USE_MODBUS_CLIENT
// helper: convert 16-bit value to two hex bytes appended to String
void appendHex16(String &s, uint16_t v) {
  char buf[5];
  sprintf(buf, "%04X", v);
  s += buf;
}

void pollModbusClient() {
  unsigned long now = millis();
  if (now - lastModbusClientPoll < MODBUS_CLIENT_POLL_MS) return;
  lastModbusClientPoll = now;

  String payload = "{";
  payload += "\"host\":\"" + String(MODBUS_CLIENT_HOST) + "\",";
  payload += "\"regs_hex\":";
  payload += "\"";

  bool anyOk = false;
  for (uint16_t r = 0; r < MODBUS_CLIENT_REG_COUNT; ++r) {
    uint16_t regIndex = MODBUS_CLIENT_START_REG + r;
    uint16_t value = 0;
    bool ok = modbusClient.readHoldingRegister16(MODBUS_CLIENT_HOST, MODBUS_CLIENT_PORT, MODBUS_CLIENT_SLAVEID, regIndex, value);
    if (ok) {
      anyOk = true;
      appendHex16(payload, value);
    } else {
      // append zeros if read fails to keep offsets
      appendHex16(payload, 0);
    }
    delay(10); // small gap between reads
  }

  payload += "\"";
  payload += ",\"ok\":" + String(anyOk ? 1 : 0);
  payload += "}";

  client.publish("ics/modbus/raw", payload.c_str());
  Serial.print("Published Modbus raw: "); Serial.println(payload);
}
#endif

// --- SENSOR READ HELPERS ---
float readPressure(int pin) {
  int raw = analogRead(pin);
  float v = raw * (3.3f / 4095.0f); // ADC to voltage
  float psi = (v - PRESSURE_V_MIN) / (PRESSURE_V_MAX - PRESSURE_V_MIN) * PRESSURE_PSI_MAX;
  if (psi < 0) psi = 0;
  float pa = psi * 6894.76f;
  return pa; // Pascals
}

float readCurrent(int pin) {
  int raw = analogRead(pin);
  float amp = (raw - ZERO_RAW) / SENSITIVITY;
  return amp;
}

void readTemps() {
  sensors.requestTemperatures();
  int count = sensors.getDeviceCount();
  for (int i = 0; i < count && i < 2; ++i) {
    temperatures[i] = sensors.getTempCByIndex(i);
  }
}

// --- PUMP CONTROL LOGIC ---

// safety constants
#define VALVE_OPEN_DELAY 500      // ms to wait after commanding solenoid
#define FLOAT_DEBOUNCE_MS 300     // ignore float chatter for this period

// finite state machine phases
enum SystemPhase {
  TRANSFER_A_TO_B,
  TRANSFER_B_TO_A
};

static SystemPhase currentPhase = TRANSFER_A_TO_B;
static unsigned long valveTimer = 0;
static bool valveOpening = false;
static unsigned long lastFloatChange = 0;

// helper for hard safety layer
void checkHardSafety(bool a_low, bool a_high, bool b_low, bool b_high) {
  // disallow both pumps running simultaneously
  if (pumpRunning1 && pumpRunning2) {
    pumpRunning1 = pumpRunning2 = false;
    systemIntervention = true;
    Serial.println("!! Safety: both pumps commanded ON - forcing shutdown");
  }
  // disallow both low‑level switches active (nobody has water)
  if (a_low && b_low) {
    pumpRunning1 = pumpRunning2 = false;
    systemIntervention = true;
    Serial.println("!! Safety: both tanks empty - forcing shutdown");
  }
  // additional current detection already exists in loop(); could add more here if desired
}

// state‑machine based pump/valve controller with interlocks & debounce
void updatePumps(bool a_low, bool a_high, bool b_low, bool b_high) {
  unsigned long now = millis();

  // float debounce: ignore rapid changes
  if (now - lastFloatChange < FLOAT_DEBOUNCE_MS) {
    // simply re‑write relays to hold previous state and return early
    digitalWrite(PUMP1_RELAY_PIN, pumpRunning1 ? HIGH : LOW);
    digitalWrite(PUMP2_RELAY_PIN, pumpRunning2 ? HIGH : LOW);
    return;
  }

  // if any float changed, restart debounce timer
  static bool prev_a_low = false, prev_a_high = false, prev_b_low = false, prev_b_high = false;
  if (a_low != prev_a_low || a_high != prev_a_high || b_low != prev_b_low || b_high != prev_b_high) {
    lastFloatChange = now;
    prev_a_low = a_low;
    prev_a_high = a_high;
    prev_b_low = b_low;
    prev_b_high = b_high;
  }

  // emergency override
  if (systemIntervention) {
    pumpRunning1 = pumpRunning2 = false;
    digitalWrite(SOLENOID_PIN, LOW);
    return;
  }

  // hard safety checks independent of phase
  checkHardSafety(a_low, a_high, b_low, b_high);

  switch (currentPhase) {
    case TRANSFER_A_TO_B:
      // start conditions for A->B
      if (!pumpRunning1 && !pumpRunning2) {
        if (!a_low && !b_high) {                      // source not empty & dest not full
          digitalWrite(SOLENOID_PIN, HIGH);           // request valve open
          valveTimer = now;
          valveOpening = true;
          // remain in this state until delay expires
        }
      }
      // after delay, energize pump
      if (valveOpening && now - valveTimer >= VALVE_OPEN_DELAY) {
        pumpRunning1 = true;
        valveOpening = false;
      }
      // stop condition
      if (pumpRunning1 && a_low) {
        pumpRunning1 = false;
        digitalWrite(SOLENOID_PIN, LOW);
        currentPhase = TRANSFER_B_TO_A;
      }
      break;

    case TRANSFER_B_TO_A:
      // start conditions for B->A (no valve)
      if (!pumpRunning1 && !pumpRunning2) {
        if (!b_low && !a_high) {                      // source B has water and A not full
          pumpRunning2 = true;
        }
      }
      // stop condition
      if (pumpRunning2 && (b_low || a_high)) {
        pumpRunning2 = false;
        currentPhase = TRANSFER_A_TO_B;
      }
      break;
  }

  digitalWrite(PUMP1_RELAY_PIN, pumpRunning1 ? HIGH : LOW);
  digitalWrite(PUMP2_RELAY_PIN, pumpRunning2 ? HIGH : LOW);
}

void setup() {
  Serial.begin(115200);

  // Pins
  pinMode(FLOW_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(FLOW_PIN), flowPulse, RISING);

  // float switches
  pinMode(FLOAT_A_LOW, INPUT_PULLUP);
  pinMode(FLOAT_A_HIGH, INPUT_PULLUP);
  pinMode(FLOAT_B_LOW, INPUT_PULLUP);
  pinMode(FLOAT_B_HIGH, INPUT_PULLUP);

  // pumps and solenoid
  pinMode(PUMP1_RELAY_PIN, OUTPUT);
  pinMode(PUMP2_RELAY_PIN, OUTPUT);
  pinMode(SOLENOID_PIN, OUTPUT);

  digitalWrite(PUMP1_RELAY_PIN, LOW);
  digitalWrite(PUMP2_RELAY_PIN, LOW);
  digitalWrite(SOLENOID_PIN, LOW);

  // Sensors
  sensors.begin();

  // WiFi & MQTT TLS
  setup_wifi();
  espClient.setCACert(ca_cert);
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // Modbus (optional)
#if USE_MODBUS
  mbServer.begin();
  modbus.configureHoldingRegisters(holdingRegisters, MB_HOLDINGS);
#endif

  lastFlowCalc = millis();
  lastPublish = millis();

  Serial.println("ESP32-S3 System Initialized (multi-sensor)");
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  // Read sensors
  readTemps();

  // read pressure sensors
  for (unsigned int i = 0; i < sizeof(PRESSURE_PINS)/sizeof(int); ++i) {
    pressures[i] = readPressure(PRESSURE_PINS[i]); // Pa
  }
  // read current sensors
  for (unsigned int i = 0; i < sizeof(CURRENT_PINS)/sizeof(int); ++i) {
    currents[i] = readCurrent(CURRENT_PINS[i]); // A
  }
  // read float switches individually
  bool a_low = digitalRead(FLOAT_A_LOW) == LOW;
  bool a_high = digitalRead(FLOAT_A_HIGH) == LOW;
  bool b_low = digitalRead(FLOAT_B_LOW) == LOW;
  bool b_high = digitalRead(FLOAT_B_HIGH) == LOW;

  // serial debug output
  Serial.print("Temps (C): ");
  Serial.print(temperatures[0],2);
  Serial.print(", ");
  Serial.println(temperatures[1],2);
  Serial.print("Pressures (Pa): ");
  Serial.print(pressures[0],1);
  Serial.print(", ");
  Serial.println(pressures[1],1);
  Serial.print("Currents (A): ");
  Serial.print(currents[0],3);
  Serial.print(", ");
  Serial.println(currents[1],3);
  Serial.print("Flow (L/min): ");
  Serial.println(flow_lpm,2);
  Serial.print("Floats A(low,high): "); Serial.print(a_low); Serial.print(","); Serial.println(a_high);
  Serial.print("Floats B(low,high): "); Serial.print(b_low); Serial.print(","); Serial.println(b_high);
  Serial.print("PumpA:"); Serial.print(pumpRunning1);
  Serial.print(" PumpB:"); Serial.print(pumpRunning2);
  Serial.print(" Solenoid:"); Serial.println(digitalRead(SOLENOID_PIN));


  unsigned long now = millis();
  if (now - lastFlowCalc >= 1000) {
    noInterrupts();
    unsigned long pulses = flowPulseCount;
    flowPulseCount = 0;
    interrupts();

    flow_lpm = (pulses / PULSES_PER_LITER) * 60.0f;
    lastFlowCalc = now;
  }

  // Safety: if any current > MAX_SAFE_CURRENT -> stop pumps
  for (unsigned int i = 0; i < sizeof(CURRENT_PINS)/sizeof(int); ++i) {
    if (fabs(currents[i]) > MAX_SAFE_CURRENT) {
      pumpRunning1 = pumpRunning2 = false;
      systemIntervention = true;
      Serial.println("!! Overcurrent detected - stopping pumps and raising intervention");
      break;
    }
  }

  updatePumps(a_low, a_high, b_low, b_high);

  // Update Modbus holding registers (use sensor 0 as primary)
#if USE_MODBUS
  holdingRegisters[HREG_TEMP] = (uint16_t)(temperatures[0] * 100); // centi-deg C
  holdingRegisters[HREG_CURRENT] = (uint16_t)(currents[0] * 1000); // milli-amps
  holdingRegisters[HREG_PRESSURE] = (uint16_t)(pressures[0] / 100); // Pa/100
  holdingRegisters[HREG_FLOAT] = a_low ? 1 : 0; // tank A low float
  holdingRegisters[HREG_PUMP] = (pumpRunning1 || pumpRunning2) ? 1 : 0;
  holdingRegisters[HREG_INTERVENTION] = systemIntervention ? 1 : 0;
  // additional registers
  holdingRegisters[HREG_PHASE] = (uint16_t)currentPhase;
  holdingRegisters[HREG_VALVE] = valveOpening ? 1 : 0;
  holdingRegisters[HREG_SAFETY] = systemIntervention ? 1 : 0;
  holdingRegisters[HREG_A_HIGH] = a_high ? 1 : 0;
  holdingRegisters[HREG_B_LOW] = b_low ? 1 : 0;

  // Accept and poll Modbus TCP clients
  WiFiClient mbClient = mbServer.available();
  if (mbClient) {
    modbus.poll(mbClient);
    // Master write handling: if the master writes to holdingRegisters,
    // inspect values here and act on them (e.g., update pump setpoints)
  }
#endif

  // Publish telemetry periodically
  if (now - lastPublish > PUBLISH_INTERVAL) {
    String payload = "{";
    payload += "\"temperatures\":[";
    for (unsigned int i = 0; i < 2; ++i) {
      if (i) payload += ",";
      payload += String(temperatures[i], 2);
    }
    payload += "],";

    payload += "\"pressures_pa\":[";
    for (unsigned int i = 0; i < 2; ++i) {
      if (i) payload += ",";
      payload += String(pressures[i], 1);
    }
    payload += "],";

    payload += "\"currents_a\":[";
    for (unsigned int i = 0; i < 2; ++i) {
      if (i) payload += ",";
      payload += String(currents[i], 3);
    }
    payload += "],";

    payload += "\"flow_lpm\":" + String(flow_lpm, 2) + ",";

    payload += "\"floats\":[";
    // A_low, A_high, B_low, B_high
    payload += String(a_low ? 1 : 0);
    payload += "," + String(a_high ? 1 : 0);
    payload += "," + String(b_low ? 1 : 0);
    payload += "," + String(b_high ? 1 : 0);
    payload += "],";
    payload += "\"phase\":" + String((int)currentPhase) + ",";
    payload += "\"valve_opening\":" + String(valveOpening ? 1 : 0) + ",";
    payload += "\"safety_trip\":" + String(systemIntervention ? 1 : 0) + ",";
    payload += "\"a_high\":" + String(a_high ? 1 : 0) + ",";
    payload += "\"b_low\":" + String(b_low ? 1 : 0) + ",";
    payload += "\"pump1\":" + String(pumpRunning1 ? 1 : 0) + ",";
    payload += "\"pump2\":" + String(pumpRunning2 ? 1 : 0) + ",";
    payload += "\"intervention\":" + String(systemIntervention ? 1 : 0);
    payload += "}";

    client.publish("ics/telemetry/data", payload.c_str());
    Serial.print("Data Published: ");
    Serial.println(payload);

    lastPublish = now;
  }

  delay(100);
}
