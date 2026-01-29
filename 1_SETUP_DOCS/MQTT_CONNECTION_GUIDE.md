# MQTT over TLS Connection Guides

## Connection Details
- **Broker IP**: `10.133.148.197`
- **TLS Port**: `8883`
- **MQTT User**: `naim`
- **MQTT Password**: `1234`

## 1. ESP32-S3 Connection (Arduino/ESP-IDF)

You should use `WiFiClientSecure` to connect.

### CA Certificate (PEM Format)
Copy this content into your code as a string or a file:

```text
-----BEGIN CERTIFICATE-----
MIIFfzCCA2egAwIBAgIUGSkMc19jQgszlVpJFPDW2k8vPcYwDQYJKoZIhvcNAQEL
BQAwTjELMAkGA1UEBhMCVVMxDjAMBgNVBAgMBVN0YXRlMQ0wCwYDVQQHDARDaXR5
MQwwCgYDVQQKDANJb1QxEjAQBgNVBAMMCUN1c3RvbSBDQTAgFw0yNjAxMjcxMzI4
MzRaGA8yMTI2MDEwMzEzMjgzNFowTjELMAkGA1UEBhMCVVMxDjAMBgNVBAgMBVN0
YXRlMQ0wCwYDVQQHDARDaXR5MQwwCgYDVQQKDANJb1QxEjAQBgNVBAMMCUN1c3Rv
bSBDQTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAI3wL30/SMTsalEO
5REyR5r5BV800zrKOp9FvOF5r1yqqygPVWdDPN9QT8M+yaipPxSJ+5V92BiLhDuv
6BNR9aD/3+UVdoHmg6ocGHNqmtY4aQS780bZbuEWGvMlRLoaJrwb7BjUUh8uijbR
XOmfAkgWJmeW2BuXf3Owa73ZKMzbbKB8PnqI7rIBxZEV242ymMpUyjSmcBINWIyj
nGVT6bOcgMs8d4DsQjmrB6sT6/a/Zg+Y8iTwvGMM2ZK6OITfapuLd8LVu84LMnXy
KY0wwLcw4QzIpo+KoeFvD1JvuAJy+7PYmr4/YNrwSLMG7L4xJkZgLhzz+XJDOXnB
WXTcbrepoTPI6v6nMUmio3zRvJPUO0bzZIs2IOP2Ooq4OJfa/A8vuVqMPeh/60Gw
Oh/KsCUlep93oqu9Mhi16/FzfT87SxvLSre2kcqcv3arw1xOOiaR/On6WyR/LfwY
itzm2VxrxamZGpOzdk2sa45aXTAgZ3yXgwA8iCJsV1vn7JOXyblVy6v/nq7VISrz
kby2FtgYt1/bOTKGDeM8jq8q8tklkI0KbOQc1Vje9rQb803Rt+RxHLjhO1p6giQZ
Vtp+A5psM+oss7NqoBNGfnZB8WmlUssU2B+N5lnYECNB5CgZ2KuyZ/2k97uYP7an
h5IDHCLYpCP43tcqrJdjvkQ8lyDRAgMBAAGjUzBRMB0GA1UdDgQWBBQvEepiIBcs
b58GJjuvCq1SUZy+ETAfBgNVHSMEGDAWgBQvEepiIBcsb58GJjuvCq1SUZy+ETAP
BgNVHRMBAf8EBTADAQH/MA0GCSqGSIb3DQEBCwUAA4ICAQBO30262LjoeWdH1UL/
9ySXelLY1LrlGzpqymDTlLk0+nFQ9Yan+YjquRt515NiG/O0o8SpGNRTKliZfMT5
952IcKGNWkSbl0Hr8AwQtS4AfTvrxCc7cgStTtFXdG0CeiJU7mWlwhkHWwn/2yWE
0e2BC8+rPpC2cUf2k37+dYS5Wt4J2gI6i4c3d2tsh5QFLfXG96OUWxWSYtjZLIHu
UtuXDF5BsHkvNcPHgH/V3XHfusIA48PpjeI+K0luDY8qF4Nyh5zvNIVAJx3XL049
VvjXq7kLKrAL2xA0qgG+hbc9PY8+B+P8viHpl590fxoRUtZthiKy4qAOifzJNDjp
oGdE8JKzB8mDSrYVtmWGKmF4euoLpOeknBb/x9hXhBSFiRzynM7LFJx3S8xOqPAL
T1Q3y9/fvoUQKGRTck9fLee8Y3SWP8QZr05xAHw2v35YVJoqo3xqwjV4nZ8HIzps
2zD2utH7YdFfrYjrhzSa+koEx9bmnpe8Qta5kPuh9HB4B6LZDFp+FwJpGpJq0LKi
WvT5Uc6qNmj24kMS/88ZYJXYkjWeDqa6qOEsvD2M30uFXigG/AEwOTKiZvB6qapL
062xosrG29n3KlwT2EjT6V8qQLSB7sTUQOL3LRXLo+Oi2r2nchUOGasfdGW+oBgE
uBUPSZKbSpvJg9w+knQgNrnz1g==
-----END CERTIFICATE-----
```

### Arduino Snippet
```cpp
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "10.133.148.197";

const char* ca_cert = 
"-----BEGIN CERTIFICATE-----\n"
"... (Paste the CA CRT content here) ...\n"
"-----END CERTIFICATE-----";

WiFiClientSecure espClient;
PubSubClient client(espClient);

void setup() {
  espClient.setCACert(ca_cert);
  client.setServer(mqtt_server, 8883);
  // ... rest of setup ...
}

void loop() {
  if (!client.connected()) {
    client.connect("ESP32-S3-Client", "naim", "1234");
  }
  client.loop();
}
```

## 2. SCADA Dashboard (Laptop)

If using **MQTTX** or similar tools:
1.  Set **Host** to `10.133.148.197`.
2.  Set **Port** to `8883`.
3.  Set **Protocol** to `mqtts://`.
4.  Enable **SSL/TLS**.
5.  Set **SSL Secure** to `ON`.
6.  Select **CA File** and provide the `ca.crt` file.
7.  Enter **Username**: `naim`, **Password**: `1234`.

## 3. Python (paho-mqtt)
```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.tls_set(ca_certs="ca.crt")
client.username_pw_set("naim", "1234")
client.connect("10.133.148.197", 8883)
client.loop_forever()
```
