from django.test import TestCase
from .models import *
from django.core.files.uploadedfile import SimpleUploadedFile


class CityModelTest(TestCase):

    def setUp(self):
        self.country = Country.objects.create(name="Test Country")
        self.city = City.objects.create(name="Test City")
        self.city.country.add(self.country)

    def test_city_creation(self):
        self.assertEqual(self.city.name, "Test City")
        self.assertIn(self.country, self.city.country.all())

    def test_city_str(self):
        self.assertEqual(str(self.city), "Test City")


class SensorModelTest(TestCase):

    def setUp(self):
        self.country = Country.objects.create(name="Test Country")
        self.city = City.objects.create(name="Test City")
        self.sensor = Sensor.objects.create(
            name="Test Sensor",
            description="Test Description",
            owner="Test Owner",
            inclusions=5,
            power=10,
            watt=20,
            volt=220,
            work=True,
            blocked=False,
            start=False,
            temperature=25.5,
            fan_speed=1000,
            ip_address="192.168.0.1",
            mac_address="00:1B:44:11:3A:B7",
            confirmed=True,
            version="1.0",
            processing_time=10.5
        )
        self.sensor.country.add(self.country)
        self.sensor.city.add(self.city)

    def test_sensor_creation(self):
        self.assertEqual(self.sensor.name, "Test Sensor")
        self.assertEqual(self.sensor.description, "Test Description")
        self.assertEqual(self.sensor.owner, "Test Owner")
        self.assertEqual(self.sensor.inclusions, 5)
        self.assertEqual(self.sensor.power, 10)
        self.assertEqual(self.sensor.watt, 20)
        self.assertEqual(self.sensor.volt, 220)
        self.assertEqual(self.sensor.work, True)
        self.assertEqual(self.sensor.blocked, False)
        self.assertEqual(self.sensor.start, False)
        self.assertEqual(self.sensor.temperature, 25.5)
        self.assertEqual(self.sensor.fan_speed, 1000)
        self.assertEqual(self.sensor.ip_address, "192.168.0.1")
        self.assertEqual(self.sensor.mac_address, "00:1B:44:11:3A:B7")
        self.assertEqual(self.sensor.confirmed, True)
        self.assertEqual(self.sensor.version, "1.0")
        self.assertEqual(self.sensor.processing_time, 10.5)
        self.assertIn(self.country, self.sensor.country.all())
        self.assertIn(self.city, self.sensor.city.all())

    def test_sensor_str(self):
        self.assertEqual(str(self.sensor), "Test Sensor")

    def test_sensor_slug(self):
        self.assertEqual(self.sensor.slug, "test-sensor")


class SensorLogModelTest(TestCase):

    def setUp(self):
        self.sensor = Sensor.objects.create(name="Test Sensor")
        self.sensor_log = SensorLog.objects.create(
            sensor=self.sensor,
            log_type="Test Log Type",
            previous_power=10,
            previous_watt=20,
            previous_volt=220
        )

    def test_sensor_log_creation(self):
        self.assertEqual(self.sensor_log.sensor, self.sensor)
        self.assertEqual(self.sensor_log.log_type, "Test Log Type")
        self.assertEqual(self.sensor_log.previous_power, 10)
        self.assertEqual(self.sensor_log.previous_watt, 20)
        self.assertEqual(self.sensor_log.previous_volt, 220)

    def test_sensor_log_str(self):
        self.assertIn("Test Sensor", str(self.sensor_log))
        self.assertIn("Test Log Type", str(self.sensor_log))


class FirmwareModelTest(TestCase):

    def setUp(self):
        self.firmware = Firmware.objects.create(
            version="1.0",
            file=SimpleUploadedFile("firmware.bin", b"file_content")
        )

    def test_firmware_creation(self):
        self.assertEqual(self.firmware.version, "1.0")
        self.assertEqual(self.firmware.file.name, "firmware.bin")

    def test_firmware_str(self):
        self.assertEqual(str(self.firmware), "1.0")
