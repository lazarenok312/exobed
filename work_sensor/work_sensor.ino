#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>
#include <FS.h>
#include <DNSServer.h>
#include <WiFiManager.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <TinyGPS++.h>
#include <WebSocketsClient.h>

String deviceName = "ESP8266"; // Имя устройства по умолчанию

const char* serverUrl = "http://exobed.lazareub.beget.tech/api/data/";
const char* csrfTokenEndpoint = "http://exobed.lazareub.beget.tech/get_csrf_token/";
String deviceStateEndpoint = "http://exobed.lazareub.beget.tech/device/esp8266/";

// Инициализация клиента Wi-Fi, HTTP, GPS и WebSocket
WiFiClient client;
HTTPClient http;
TinyGPSPlus gps;
WebSocketsClient webSocket;

#define DHTPIN D4     // Пин для подключения датчика DHT
#define DHTTYPE DHT11 // Тип датчика DHT (DHT11)
DHT dht(DHTPIN, DHTTYPE); // Инициализация датчика температуры и влажности
bool ledState = false; // Переменная для состояния светодиода
bool blocked = false; // Переменная для состояния блокировки устройства

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
        Serial.print("Failed to get CSRF token, HTTP error code: ");
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
        Serial.print("HTTP Response code: ");
        Serial.println(httpResponseCode);
        String response = http.getString();
        Serial.println(response);
    } else {
        Serial.print("Error code: ");
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
            Serial.print("Error getting device state: ");
            Serial.println(httpCode);
        }

        http.end();
    } else {
        Serial.println("Failed to connect to server");
    }
}

void updateDeviceState(bool work) {
    // Здесь вы можете использовать значения work 
    // для принятия решений или изменения поведения устройства
    // Например:

    if (work) {
        // Ваше действие при работающем устройстве
    } else {
        // Ваше действие при выключенном устройстве
    }
}

void setup() {
    Serial.begin(115200); // Инициализация последовательного порта

    dht.begin(); // Инициализация датчика DHT
    pinMode(LED_BUILTIN, OUTPUT); // Настройка пина светодиода

    WiFiManager wifiManager; // Инициализация менеджера Wi-Fi

    // Добавление параметра для настройки имени устройства
    WiFiManagerParameter custom_device_name("device", "Device Name", deviceName.c_str(), 40);
    wifiManager.addParameter(&custom_device_name);

    wifiManager.autoConnect("ESP8266_AP"); // Автоматическое подключение к Wi-Fi сети

    deviceName = custom_device_name.getValue(); // Получение значения имени устройства

    Serial.println("Connected to WiFi"); // Вывод сообщения о подключении к Wi-Fi

    if (!SPIFFS.begin()) { // Инициализация файловой системы SPIFFS
        Serial.println("Failed to initialize SPIFFS"); // Вывод сообщения об ошибке
        return;
    }
}

void loop() {
    while (Serial.available() > 0) { // Проверка доступности данных в последовательном порту
        gps.encode(Serial.read()); // Обработка данных GPS
    }

    // Получение состояния устройства с сервера Django
    getDeviceState();

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
        Serial.println("Данные GPS недоступны"); // Вывод сообщения о недоступности данных GPS
    }

    StaticJsonDocument<200> doc; // Создание JSON-документа

    float temperature = dht.readTemperature(); // Получение температуры
    float humidity = dht.readHumidity(); // Получение влажности

    // Вывод значений температуры и влажности
    Serial.print("Температура: ");
    Serial.print(temperature);
    Serial.print(" °C\t");
    Serial.print("Влажность: ");
    Serial.print(humidity);
    Serial.println(" %");

    int power = random(10, 99); // Генерация случайной мощности
    int watt = random(100, 900); // Генерация случайной мощности
    int volt = random(180, 240); // Генерация случайного напряжения
    int fan_speed = random(10, 2000); // Генерация скорости вентилятора

    // Проверяем, заблокировано ли устройство
    if (!blocked) {
      Serial.println("Устройство доступно!!!");
        // Заполнение JSON-документа данными
        doc["name"] = deviceName;
        doc["temperature"] = temperature;
        doc["power"] = power;
        doc["watt"] = watt;
        doc["volt"] = volt;
        doc["work"] = true;
        doc["fan_speed"] = fan_speed;

        String jsonData; // Создание строки для JSON-данных
        serializeJson(doc, jsonData); // Сериализация JSON-документа в строку

        sendDataWithCSRFToken(jsonData); // Отправка данных на сервер
    } else {
        // Устройство заблокировано, мигаем светодиодом
        Serial.println("Устройство заблокировано!!!");
        digitalWrite(LED_BUILTIN, HIGH); // Включаем светодиод
        delay(500); // Задержка
        digitalWrite(LED_BUILTIN, LOW); // Выключаем светодиод
        delay(500); // Задержка
    }

    delay(30000); // Задержка 30 секунд
}
