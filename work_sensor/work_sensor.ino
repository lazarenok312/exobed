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

String deviceName = "esp8266";
String deviceStateEndpoint;

const char* version = "1.0.0";
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

#define DHTPIN D4     // Пин для подключения датчика DHT
#define DHTTYPE DHT11 // Тип датчика DHT (DHT11)
DHT dht(DHTPIN, DHTTYPE); // Инициализация датчика температуры и влажности


// Функция отправки данных с CSRF-токеном
void sendDataWithCSRFToken(String data) {
    HTTPClient http;
    // Запрос CSRF-токена
    http.begin(client, csrfTokenEndpoint);
    int httpResponseCode = http.GET();
    String csrfToken;

    // Если запрос прошел успешно, получаем CSRF-токен
    if (httpResponseCode > 0) {
        csrfToken = http.getString();
    } else {
        // В случае ошибки выводим сообщение
        Serial.print("Не удалось получить токен CSRF, код ошибки HTTP: ");
        Serial.println(httpResponseCode);
        return;
    }

    http.end(); // Завершаем соединение

    // Отправляем данные на сервер с заголовком CSRF-токена
    http.begin(client, serverUrl);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-CSRFToken", csrfToken);

    httpResponseCode = http.POST(data); // Отправляем POST-запрос с данными

    // Обрабатываем ответ от сервера
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

    http.end(); // Завершаем соединение
}

// Функция для получения состояния устройства с сервера Django
void getDeviceState() {
    HTTPClient http;

    if (http.begin(client, deviceStateEndpoint.c_str())) {
        int httpCode = http.GET();

        if (httpCode == 200) {
            String payload = http.getString();
            // Распарсить JSON и обновить переменные на устройстве
            DynamicJsonDocument doc(200);
            deserializeJson(doc, payload);

            // Получаем значения состояния устройства
            blocked = doc["blocked"];
            bool work = doc["work"];

            // Обновляем переменные состояния устройства
            updateDeviceState(work);

        } else {
            Serial.print("Ошибка получения состояния устройства: ");
            Serial.println(httpCode);
        }

        http.end();
    } else {
        Serial.println("Не удалось подключиться к серверу");
    }
}

void updateDeviceState(bool work) {

    if (work) {
        // Ваше действие при работающем устройстве
    } else {
        // Ваше действие при выключенном устройстве
    }
}

void setup() {
    Serial.begin(115200); // Инициализация последовательного порта
    SPIFFS.begin();

    dht.begin(); // Инициализация датчика DHT

    File configFile = SPIFFS.open("/config.json", "r");
    if (configFile) {
        // Чтение содержимого файла и установка имени устройства
        deviceName = configFile.readStringUntil('\n');
        configFile.close();
    }

    // Если файл не существует или не удалось прочитать имя, используется значение по умолчанию
    if (deviceName == "") {
        deviceName = "esp8266";
    }

    WiFiManager wifiManager; // Инициализация менеджера Wi-Fi

    // Добавление параметра для настройки имени устройства
    WiFiManagerParameter custom_device_name("device", "Имя устройства в нижнем регистре (device_name)", deviceName.c_str(), 40);
    wifiManager.addParameter(&custom_device_name);

    // Подключение к Wi-Fi сети или создание точки доступа с паролем
    if (!wifiManager.autoConnect("ESP8266_EXO", "exoadmin")) {
        Serial.println("Не удалось подключиться к Wi-Fi и создать точку доступа.");
        delay(1000);
        ESP.reset();
        delay(5000);
    }

    // Получение значения имени устройства из параметра WiFiManager
    deviceName = custom_device_name.getValue();

    // Обновление URL для состояния устройства с учетом имени устройства
    deviceStateEndpoint = "http://exobed.lazareub.beget.tech/device/" + deviceName + "/";

    Serial.println("Подключено к Wi-Fi"); // Вывод сообщения о подключении к Wi-Fi

    if (!SPIFFS.begin()) { // Инициализация файловой системы SPIFFS
        Serial.println("Не удалось инициализировать SPIFFS."); // Вывод сообщения об ошибке
        return;
    }
}

void saveDeviceName(String name) {
    // Сохранение имени устройства в файл
    File configFile = SPIFFS.open("/config.json", "w");
    if (configFile) {
        configFile.println(name);
        configFile.close();
    } else {
        Serial.println("Ошибка сохранения имени устройства в файл.");
    }
}

void checkForUpdates() {
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
      const char* firmwareUrl = doc["url"];

      Serial.println("Получена информация о версии прошивки:");
      Serial.print("Новая версия: ");
      Serial.println(latestVersion);
      Serial.print("URL прошивки: ");
      Serial.println(firmwareUrl);

      if (String(latestVersion) != String(currentVersion)) {
        Serial.println("Доступна новая версия прошивки: " + String(latestVersion));
        Serial.println("Качаю прошивку с: " + String(firmwareUrl));

        t_httpUpdate_return ret = ESPhttpUpdate.update(client, firmwareUrl, currentVersion);

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
  }
}

void updateFirmware() {
    Serial.println("Загрузка прошивки...");

    t_httpUpdate_return ret = ESPhttpUpdate.update(client, firmwareUrl, currentVersion);
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
}

void loop() {
    while (Serial.available() > 0) { // Проверка доступности данных в последовательном порту
        gps.encode(Serial.read()); // Обработка данных GPS
    }

    // Получение состояния устройства с сервера Django
    getDeviceState();
    // Проверка обновлений
    checkForUpdates();

    // Загрузка прошивки
    updateFirmware();

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

    } else {
        Serial.println("Данные GPS недоступны"); // Вывод сообщения о недоступности данных GPS
    }

    StaticJsonDocument<200> doc; // Создание JSON-документа

    float temperature = dht.readTemperature(); // Получение температуры
    float humidity = dht.readHumidity(); // Получение влажности

    Serial.print("-----------------------------");
    Serial.print("\n");
    Serial.print("Температура: ");
    Serial.print(temperature);
    Serial.print(" °C\t");
    Serial.print("Влажность: ");
    Serial.print(humidity);
    Serial.println(" %");
    Serial.print("-----------------------------");
    Serial.print("\n");

    
    if (!blocked) {
      IPAddress ip = WiFi.localIP(); // Получаем IP-адрес

      int power = random(10, 99);
      int watt = random(100, 900);
      int volt = random(180, 240);
      int fan_speed = random(10, 2000);
      String ip_address = ip.toString();
      String mac_address = WiFi.macAddress();
      Serial.print("IP адрес: ");
      Serial.println(ip.toString());
      Serial.print("\n");
      Serial.print("MAC адрес: ");
      Serial.print(mac_address);
      Serial.print("\n");
      Serial.print("-----------------------------");
      Serial.print("\n");
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

      String jsonData; // Создание строки для JSON-данных
      serializeJson(doc, jsonData); // Сериализация JSON-документа в строку

      sendDataWithCSRFToken(jsonData); // Отправка данных на сервер
    } else {
        // Устройство заблокировано, мигаем светодиодом
        Serial.println("Устройство заблокировано!!!");
    }
    delay(60000); // Задержка 30 секунд
}

void handleCommand(String command) {
    command.trim();

    Serial.print("Получена команда: ");
    Serial.println(command);

    if (command == "resetwifi") {
        Serial.println("Сброс настроек Wi-Fi...");
        WiFiManager wifiManager; // Создание объекта WiFiManager
        wifiManager.resetSettings(); // Сброс настроек Wi-Fi
        Serial.println("Wi-Fi настройки сброшены.");
    } else {
        Serial.println("Неизвестная команда."); // Обработка неизвестной команды
    }
}

void serialEvent() {
    // Обработка событий последовательного порта
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n') {
            // Запуск обработки команды при получении символа новой строки
            handleCommand(receivedCommand);
            receivedCommand = ""; // Сброс строки для следующей команды
        } else {
            receivedCommand += c; // Добавление символа к текущей команде
        }
    }
}
