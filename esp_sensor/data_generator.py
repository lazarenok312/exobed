import random
import os
import django
import time
import faker

fake = faker.Faker()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exobed.settings')
django.setup()
from esp_sensor.models import Sensor

def generate_random_data(sensor):
    sensor.owner = fake.name()
    sensor.power = round(random.uniform(10, 90))
    sensor.watt = round(random.uniform(100, 900))
    sensor.volt = round(random.uniform(180, 230))
    sensor.temperature = round(random.uniform(0, 100))
    sensor.fan_speed = round(random.uniform(100, 2000))
    sensor.save()

def create_or_get_sensor(sensor_name):
    sensor, created = Sensor.objects.get_or_create(name=sensor_name, defaults={'slug': sensor_name})
    return sensor

def generate_data_for_batch(start_index, end_index):
    for i in range(start_index, end_index):
        sensor_name = f"Sensor_{i+1}"
        sensor = create_or_get_sensor(sensor_name)
        generate_random_data(sensor)

def main():
    while True:
        batch_size = 10  # Размер пакета
        total_sensors = Sensor.objects.count()
        for start_index in range(0, total_sensors, batch_size):
            end_index = min(start_index + batch_size, total_sensors)
            generate_data_for_batch(start_index, end_index)
            print(f"Данные успешно сгенерированы для датчиков с {start_index + 1} по {end_index}")
            time.sleep(60)  # Подождать некоторое время перед обработкой следующего пакета
        print("Все данные успешно сгенерированы")
        time.sleep(600)  # Подождать перед следующим циклом

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Произошла ошибка:", e)
