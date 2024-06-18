#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>
#include <FS.h>
#include <DNSServer.h>
#include <WiFiManager.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <TinyGPS++.h>
#include <FS.h>
#include <ESP8266httpUpdate.h>
#include <WebSocketsClient.h>

String deviceName = "esp8266";
String owner = "Unknown";
String deviceStateEndpoint;

WebSocketsClient webSocket;
const char* ws_host = "exobed.lazareub.beget.tech";
const int ws_port = 80;
String ws_path = "/ws/device/" + deviceName + "/";

const char* version = "1.0.1";
const char* firmwareFileName = "work_sensor.ino.bin";
const char* currentVersion = version;
const char* serverUrl = "http://exobed.lazareub.beget.tech/api/data/";
const char* csrfTokenEndpoint = "http://exobed.lazareub.beget.tech/get_csrf_token/";
const char* updateUrl = "http://exobed.lazareub.beget.tech/api/latest-firmware/";
const char* firmwareUrl = "http://exobed.lazareub.beget.tech/media/firmwares/work_sensor.ino.bin";

bool blocked = false;
String receivedCommand = "";

WiFiClient client;
HTTPClient http;
TinyGPSPlus gps;

#define DHTPIN D4     
#define DHTTYPE DHT11     
DHT dht(DHTPIN, DHTTYPE);


// Функция отправки данных с CSRF-токеном
void sendDataWithCSRFToken(String data) {
  HTTPClient http;
  http.begin(client, csrfTokenEndpoint);
  int httpResponseCode = http.GET();
  String csrfToken;

  if (httpResponseCode > 0) {
    csrfToken = http.getString();
  } else {
    Serial.print("Не удалось получить токен CSRF, код ошибки HTTP: ");
    Serial.println(httpResponseCode);
    return;
  }
  http.end();

  // Отправляем данные на сервер с заголовком CSRF-токена
  http.begin(client, serverUrl);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-CSRFToken", csrfToken);

  httpResponseCode = http.POST(data);

  if (httpResponseCode > 0) {
    Serial.print("\n");
    Serial.print("Код ответа HTTP: ");
    Serial.println(httpResponseCode);
    String response = http.getString();
    Serial.println(response);
  } else {
    Serial.print("Код ошибки: ");
    Serial.println(httpResponseCode);
  }

  http.end();
}

// Функция для получения состояния устройства с сервера Django
void getDeviceState() {
  HTTPClient http;

  if (http.begin(client, deviceStateEndpoint.c_str())) {
    int httpCode = http.GET();

    if (httpCode == 200) {
      String payload = http.getString();
      DynamicJsonDocument doc(200);
      deserializeJson(doc, payload);

      blocked = doc["blocked"];
      bool work = doc["work"];
      int power = doc["power"];

      if (work) {
        Serial.println("Устройство включено");
      } else {
        Serial.println("Устройство выключено");
      }

      Serial.print("Текущая мощность: ");
      Serial.println(power);

    } else {
      Serial.print("Ошибка получения состояния устройства: ");
      Serial.println(httpCode);
    }

    http.end();
  } else {
    Serial.println("Не удалось подключиться к серверу");
  }
}

void saveDeviceName(String name) {
  File configFile = SPIFFS.open("/config.json", "w");
  if (configFile) {
    configFile.println(name);
    configFile.close();
    Serial.print("Имя устройства '");
    Serial.print(name);
    Serial.println("' записано в память.");
    deviceName = name;
  } else {
    Serial.println("Ошибка сохранения имени устройства в файл.");
  }
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.println("WebSocket отключен");
      break;
    case WStype_CONNECTED:
      Serial.println("WebSocket подключен");
      break;
    case WStype_TEXT:
      Serial.printf("Получены данные: %s\n", payload);
      break;
  }
}

void setup() {
  Serial.begin(115200); 
  SPIFFS.begin();

  webSocket.begin(ws_host, ws_port, ws_path);
  webSocket.onEvent(webSocketEvent);

  dht.begin(); 

  File configFile = SPIFFS.open("/config.json", "r");
  if (configFile) {
    deviceName = configFile.readStringUntil('\n');
    configFile.close();
  }
  deviceName.trim();
  if (deviceName == "") {
    deviceName = "esp8266";
  }

  WiFiManager wifiManager;

  WiFiManagerParameter custom_device_name("device", "Имя устройства в нижнем регистре (device_name)", deviceName.c_str(), 40);
  WiFiManagerParameter custom_owner("owner", "ФИО владельца", owner.c_str(), 100);
  wifiManager.addParameter(&custom_device_name);
  wifiManager.addParameter(&custom_owner);


  // Подключение к Wi-Fi сети или создание точки доступа с паролем
  if (!wifiManager.autoConnect("ESP8266_EXO", "exoadmin")) {
    Serial.println("Не удалось подключиться к Wi-Fi и создать точку доступа.");
    delay(1000);
    ESP.reset();
    delay(5000);
  }

  deviceName = custom_device_name.getValue();
  owner = custom_owner.getValue();

  deviceStateEndpoint = "http://exobed.lazareub.beget.tech/device/" + deviceName + "/";

  Serial.println("Подключено к Wi-Fi"); 
  webSocket.begin(ws_host, ws_port, ws_path);
  webSocket.onEvent(webSocketEvent);

  if (!SPIFFS.begin()) {                                   
    Serial.println("Не удалось инициализировать SPIFFS."); 
    return;
  }

  saveDeviceName(deviceName);
}


void UpdatesFirmware() {
  Serial.println("Проверка обновлений...");

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(client, updateUrl);
    int httpCode = http.GET();

    if (httpCode == HTTP_CODE_OK) {
      String payload = http.getString();
      DynamicJsonDocument doc(1024);
      deserializeJson(doc, payload);

      const char* latestVersion = doc["version"];
      String relativeFirmwareUrl = doc["url"];

      String firmwareUrl;
      if (relativeFirmwareUrl.startsWith("http://") || relativeFirmwareUrl.startsWith("https://")) {
        firmwareUrl = relativeFirmwareUrl;
      } else {
        firmwareUrl = "http://exobed.lazareub.beget.tech/media/firmwares/" + relativeFirmwareUrl;
      }

      if (String(latestVersion) != String(currentVersion)) {
        Serial.println("Доступна новая версия прошивки: " + String(latestVersion));
        Serial.println("Закачиваю прошивку: " + firmwareUrl);

        Serial.print("Уровень сигнала Wi-Fi: ");
        Serial.println(WiFi.RSSI());

        t_httpUpdate_return ret = ESPhttpUpdate.update(client, firmwareUrl.c_str(), currentVersion);

        switch (ret) {
          case HTTP_UPDATE_FAILED:
            Serial.printf("HTTP_UPDATE_FAILED Error (%d): %s\n", ESPhttpUpdate.getLastError(), ESPhttpUpdate.getLastErrorString().c_str());
            break;

          case HTTP_UPDATE_NO_UPDATES:
            Serial.println("HTTP_UPDATE_NO_UPDATES");
            break;

          case HTTP_UPDATE_OK:
            Serial.println("HTTP_UPDATE_OK");
            break;
        }
      } else {
        Serial.println("Прошивка актуальна");
      }
    } else {
      Serial.printf("HTTP request failed with error code: %d\n", httpCode);
    }

    http.end();
  } else {
    Serial.println("Нет подключения к Wi-Fi");
  }
}

void loop() {
  while (Serial.available() > 0) {  // Проверка доступности данных в последовательном порту
    gps.encode(Serial.read());      // Обработка данных GPS
  }

  webSocket.loop();

  if (WiFi.status() == WL_CONNECTED) {
    getDeviceState();
    UpdatesFirmware();

    if (gps.location.isValid()) {
      float latitude = gps.location.lat();
      float longitude = gps.location.lng();

      Serial.print("Широта: ");
      Serial.println(latitude, 6);
      Serial.print("Долгота: ");
      Serial.println(longitude, 6);

    } else {
      Serial.println("Данные GPS недоступны"); 
    }

    StaticJsonDocument<200> doc; 
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();       

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("Ошибка чтения данных с датчика! Генерация случайных значений.");
      temperature = random(30, 35); 
      humidity = random(30, 70);  
    }

    Serial.print("----------------------------------------------------------");
    Serial.print("\n");
    Serial.print("Температура: ");
    Serial.print(temperature);
    Serial.print(" °C  |\t");
    Serial.print("Влажность: ");
    Serial.print(humidity);
    Serial.println(" %");
    Serial.print("----------------------------------------------------------");
    Serial.print("\n");


    if (!blocked) {
      IPAddress ip = WiFi.localIP();

      int power = 60;
      int watt = random(550, 600);
      int volt = random(210, 225);
      int fan_speed = random(1000, 1500);
      String ip_address = ip.toString();
      String mac_address = WiFi.macAddress();
      Serial.print("IP адрес: ");
      Serial.println(ip.toString());
      Serial.print("MAC адрес: ");
      Serial.print(mac_address);
      Serial.print("\n");
      Serial.print("----------------------------------------------------------");
      Serial.print("\n");
      Serial.println("Устройство доступно!!!");
      Serial.print("\n");

      doc["name"] = deviceName;
      doc["temperature"] = temperature;
      doc["power"] = power;
      doc["watt"] = watt;
      doc["volt"] = volt;
      doc["work"] = true;
      doc["fan_speed"] = fan_speed;
      doc["ip_address"] = ip_address;
      doc["mac_address"] = mac_address;
      doc["version"] = version;
      doc["owner"] = owner;

      String jsonData;
      serializeJson(doc, jsonData);
      sendDataWithCSRFToken(jsonData);
    } else {
      Serial.println("Устройство заблокировано!!!");
    }
  } else {
    Serial.println("Нет подключения к Wi-Fi"); 
  }
  delay(60000);
}

void handleCommand(String command) {
  command.trim();

  Serial.print("Получена команда: ");
  Serial.println(command);

  if (command == "resetwifi") {
    Serial.println("Сброс настроек Wi-Fi...");
    WiFiManager wifiManager;     
    wifiManager.resetSettings(); 
    Serial.println("Wi-Fi настройки сброшены.");
  } else {
    Serial.println("Неизвестная команда."); 
  }
}

void serialEvent() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      handleCommand(receivedCommand);
      receivedCommand = ""; 
    } else {
      receivedCommand += c;
    }
  }
}
