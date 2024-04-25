#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>
#include <FS.h>
#include <DNSServer.h>
#include <WiFiManager.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <TinyGPS++.h>
#include <WebSocketsClient.h>

const char* serverUrl = "http://exobed.lazareub.beget.tech/api/data/";
const char* csrfTokenEndpoint = "http://exobed.lazareub.beget.tech/get_csrf_token/";
const char* webSocketServer = "ws://your_websocket_server_address:port";

WiFiClient client;
HTTPClient http;
TinyGPSPlus gps;
WebSocketsClient webSocket;

String deviceName = "ESP8266";
#define DHTPIN D4     // Указываем пин, к которому подключен датчик
#define DHTTYPE DHT11 // Указываем тип датчика

DHT dht(DHTPIN, DHTTYPE);
bool ledState = false;

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
    switch(type) {
        case WStype_TEXT:
            Serial.printf("[WebSocket] Message: %s\n", payload);
            if (strcmp((char*)payload, "start") == 0) {
                digitalWrite(LED_BUILTIN, HIGH); // Включаем светодиод
                ledState = true;
            } else if (strcmp((char*)payload, "stop") == 0) {
                digitalWrite(LED_BUILTIN, LOW); // Выключаем светодиод
                ledState = false;
            }
            break;
    }
}


void sendDataWithCSRFToken(String data) {
    HTTPClient http;
    http.begin(client, csrfTokenEndpoint);
    int httpResponseCode = http.GET();
    String csrfToken;

    if (httpResponseCode > 0) {
        csrfToken = http.getString();
    } else {
        Serial.print("Failed to get CSRF token, HTTP error code: ");
        Serial.println(httpResponseCode);
        return;
    }

    http.end();

    http.begin(client, serverUrl);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-CSRFToken", csrfToken);

    httpResponseCode = http.POST(data);

    if (httpResponseCode > 0) {
        Serial.print("HTTP Response code: ");
        Serial.println(httpResponseCode);
        String response = http.getString();
        Serial.println(response);
    } else {
        Serial.print("Error code: ");
        Serial.println(httpResponseCode);
    }

    http.end();
}

void setup() {
    Serial.begin(115200);

    dht.begin(); // Инициализируем датчик DHT11
    pinMode(LED_BUILTIN, OUTPUT);

    WiFiManager wifiManager;

    WiFiManagerParameter custom_device_name("device", "Device Name", deviceName.c_str(), 40);
    wifiManager.addParameter(&custom_device_name);

    wifiManager.autoConnect("ESP8266_AP");

    deviceName = custom_device_name.getValue();

    Serial.println("Connected to WiFi");

    webSocket.begin("your_websocket_server_address", 80);
    webSocket.onEvent(webSocketEvent);

    if (!SPIFFS.begin()) {
        Serial.println("Failed to initialize SPIFFS");
        return;
    }
}

void loop() {

  webSocket.loop(); // Поддерживаем соединение по веб-сокету

   while (Serial.available() > 0) {
        gps.encode(Serial.read());
    }

    // Проверка наличия корректных данных GPS
    if (gps.location.isValid()) {
        // Получение широты и долготы
        float latitude = gps.location.lat();
        float longitude = gps.location.lng();

        // Вывод широты и долготы
        Serial.print("Широта: ");
        Serial.println(latitude, 6);  // 6 десятичных знаков для лучшей точности
        Serial.print("Долгота: ");
        Serial.println(longitude, 6);

        // Вы также можете извлечь высоту, скорость, курс и т. д. из объекта gps при необходимости
    } else {
        Serial.println("Данные GPS недоступны");
    }

    StaticJsonDocument<200> doc;

    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    Serial.print("Температура: ");
    Serial.print(temperature);
    Serial.print(" °C\t");

    Serial.print("Влажность: ");
    Serial.print(humidity);
    Serial.println(" %");

    int power = random(10, 99);
    int watt = random(100, 900);
    int volt = random(180, 240);
    bool work = true;
    int fan_speed = random(10, 2000);

    doc["name"] = deviceName;
    doc["temperature"] = temperature;
    doc["power"] = power;
    doc["watt"] = watt;
    doc["volt"] = volt;
    doc["work"] = work;
    doc["fan_speed"] = fan_speed;

    String jsonData;
    serializeJson(doc, jsonData);

    sendDataWithCSRFToken(jsonData);

    delay(60000);
}

void toggleLamp() {
    HTTPClient http;

    if (http.begin(client, serverUrl)) { 
        int httpCode = http.POST("");

        if (httpCode == 200) {
            Serial.println("Lamp toggled successfully");
            digitalWrite(D1, !digitalRead(D1));
        } else {
            Serial.print("Error toggling lamp: ");
            Serial.println(httpCode);
        }

        http.end();
    } else {
        Serial.println("Failed to connect to server");
    }
}