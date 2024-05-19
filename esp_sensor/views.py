from django.views.generic import View, ListView, DetailView, DeleteView
from django.views.decorators.csrf import csrf_exempt

from django.db.models import Q
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.middleware.csrf import get_token
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest, StreamingHttpResponse, \
    FileResponse

from datetime import datetime
import json
import time
import os
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


# Класс для отображения списка датчиков
class SensorListView(ListView):
    model = Sensor
    template_name = 'sensor/sensor_list.html'
    context_object_name = 'sensors'
    paginate_by = 8

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by('name', 'owner', '-blocked', '-date_added')
        queryset = queryset.prefetch_related('sensorlog_set')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        sensors = context['sensors']

        confirmed_sensors = [sensor for sensor in queryset if sensor.confirmed]

        for sensor in confirmed_sensors:
            latest_log = sensor.sensorlog_set.last()
            if latest_log:
                sensor.last_updated = latest_log.timestamp
            else:
                sensor.last_updated = sensor.date_added

        unconfirmed_sensors = [sensor for sensor in queryset if not sensor.confirmed]

        for sensor in unconfirmed_sensors:
            latest_log = sensor.sensorlog_set.last()
            if latest_log:
                sensor.last_updated = latest_log.timestamp
            else:
                sensor.last_updated = sensor.date_added

        context['confirmed_sensors'] = confirmed_sensors
        context['unconfirmed_sensors'] = unconfirmed_sensors
        return context


class ConfirmSensorView(View):
    def get(self, request, sensor_id):
        sensor = get_object_or_404(Sensor, pk=sensor_id)
        sensor.confirmed = True
        sensor.save()
        return redirect('sensor_list')


# Класс для отображения подробной информации о датчике
class SensorDetailView(DetailView):
    model = Sensor
    template_name = 'sensor/sensor_detail.html'
    context_object_name = 'sensor'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.prefetch_related('sensorlog_set').all()

    def post(self, request, *args, **kwargs):
        sensor = self.get_object()
        previous_power = sensor.power
        previous_watt = sensor.watt
        previous_volt = sensor.volt
        sensor.work = not sensor.work
        sensor.save()

        log_type = 'Включение' if sensor.work else 'Выключение'
        SensorLog.objects.create(sensor=sensor, log_type=log_type, previous_power=previous_power,
                                 previous_watt=previous_watt, previous_volt=previous_volt)

        return JsonResponse(
            {'success': True, 'power_changed': previous_power != sensor.power, 'current_power': sensor.power})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sensor = self.get_object()
        logs = sensor.sensorlog_set.all().order_by('-timestamp')
        paginator = Paginator(logs, 10)
        page_number = self.request.GET.get('page')
        page_logs = paginator.get_page(page_number)
        context['logs'] = page_logs
        context['sensor_id'] = sensor.id

        temperature = sensor.temperature
        fan_speed = sensor.fan_speed
        context['temperature'] = temperature
        context['fan_speed'] = fan_speed

        self.add_warnings_to_context(sensor, context)
        self.add_recommendations_to_context(sensor, context)

        if logs.exists():
            context[
                'latest_log'] = logs.first()
        else:
            context['latest_log'] = None

        return context

    def add_warnings_to_context(self, sensor, context):
        warnings = []

        previous_temperatures = self.request.session.get('previous_temperatures', [])
        temperature = sensor.temperature
        fan_speed = sensor.fan_speed

        if previous_temperatures:
            last_three_temperatures = previous_temperatures[-3:]
            if all(temp > last_three_temperatures[i - 1] for i, temp in
                   enumerate(last_three_temperatures[1:], start=1)):
                warnings.append('Температура постоянно растет.')
        else:
            warnings.append('Начало отслеживания температуры.')

        previous_temperatures.append(temperature)
        self.request.session['previous_temperatures'] = previous_temperatures

        if temperature is not None and temperature > 80:
            warnings.append('Высокая температура устройства')
        if fan_speed is not None and fan_speed < 100:
            warnings.append('Низкая скорость кулера')

        context['warnings'] = warnings

    def add_recommendations_to_context(self, sensor, context):
        recommendations = []

        previous_powers = self.request.session.get('previous_powers', [])

        power = sensor.power
        previous_powers.append(power)
        self.request.session['previous_powers'] = previous_powers

        if len(previous_powers) >= 5 and all(p > 90 for p in previous_powers[-5:]):
            recommendations.append('Мощность устройства долгое время превышает 90%. Рекомендуется снизить мощность.')

        context['recommendations'] = recommendations

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            logs_html = self.render_logs_to_html(context['logs'])
            num_pages = context['logs'].paginator.num_pages
            return JsonResponse(
                {'logs_html': logs_html, 'has_next': context['logs'].has_next(), 'num_pages': num_pages})
        else:
            return super().render_to_response(context, **response_kwargs)

    def render_logs_to_html(self, logs):
        return ''.join([self.render_log_to_html(log) for log in logs])

    def render_log_to_html(self, log):
        russian_months = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 5: 'мая', 6: 'июня',
            7: 'июля', 8: 'августа', 9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        month = russian_months[log.timestamp.month]
        html = f"""
            <li>{log.log_type} - {log.timestamp.strftime('%d')} {month} {log.timestamp.strftime('%Y г. %H:%M')}</li>
            <li>Мощность: {log.previous_power}%</li>
            """
        if log.previous_watt:
            html += f"<li>{log.previous_watt} Watt | {log.previous_volt} Volt</li>"
        html += "<hr class='dark horizontal my-0'>"
        return html

    @staticmethod
    def get_sensor_logs(sensor_id):
        logs = SensorLog.objects.filter(sensor_id=sensor_id).order_by('timestamp')
        data = [[log.timestamp.timestamp() * 1000, log.previous_watt] for log in logs]
        return data


class SensorDeleteView(DeleteView):
    model = Sensor
    template_name = 'sensor/sensor_detail.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Sensor, pk=self.kwargs.get('pk'))

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse_lazy('sensor_list')


def block_toggle(request, sensor_id):
    sensor = get_object_or_404(Sensor, pk=sensor_id)
    sensor.blocked = not sensor.blocked
    sensor.save()

    redirect_url = request.META.get('HTTP_REFERER') or reverse('home')
    return HttpResponseRedirect(redirect_url)


def toggle_start(request, sensor_id):
    sensor = get_object_or_404(Sensor, pk=sensor_id)
    sensor.start = not sensor.start
    sensor.save()

    redirect_url = request.META.get('HTTP_REFERER') or reverse('home')
    return HttpResponseRedirect(redirect_url)


# Функция для загрузки логов датчика в формате CSV
def download_logs(request, device_slug):
    sensor = get_object_or_404(Sensor, slug=device_slug)

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

    logs = SensorLog.objects.filter(sensor=sensor)
    if start_date and end_date:
        logs = logs.filter(timestamp__range=(start_date, end_date))

    csv_data = render_to_string('logs/csv_template.txt', {'logs': logs})
    filename = f'{sensor.name}_logs.csv'

    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# Функция для обработки AJAX запроса с подробной информацией о датчике
def sensor_detail_ajax(request, sensor_id):
    sensor = Sensor.objects.get(pk=sensor_id)
    data = {
        'watt': sensor.watt,
        'volt': sensor.volt,
        'work': sensor.work,
        'temperature': sensor.temperature,
        'fan_speed': sensor.fan_speed,
    }
    return JsonResponse(data)


# Функция для обновления данных датчика (мощности) через AJAX
def update_sensor_power(request, sensor_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        power = request.POST.get('power')

        sensor = Sensor.objects.get(pk=sensor_id)
        previous_power = sensor.power
        sensor.power = power
        sensor.save()

        log_type = 'Изменение мощности'
        log_entry = SensorLog.objects.create(sensor=sensor, log_type=log_type,
                                             previous_power=previous_power,
                                             previous_watt=sensor.watt, previous_volt=sensor.volt)

        log_entry.previous_power = sensor.power
        log_entry.save()

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'error': 'This endpoint only accepts AJAX requests'}, status=400)


# Функция для потоковой передачи логов датчика
def stream_sensor_logs(request, sensor_id):
    if not sensor_id:
        return HttpResponseBadRequest("No sensor_id provided")

    # Функция-генератор для получения логов датчика
    def generate_logs(sensor_id):
        while True:
            logs = SensorLog.objects.filter(sensor_id=sensor_id).order_by('timestamp')
            for log in logs:
                yield "data: %s\n\n" % json.dumps({
                    'log_type': log.log_type,
                    'timestamp': log.timestamp,
                    'previous_power': log.previous_power,
                    'previous_watt': log.previous_watt,
                    'previous_volt': log.previous_volt
                })
            time.sleep(1)

    # Возвращаем потоковый HTTP-ответ
    response = StreamingHttpResponse(generate_logs(sensor_id), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    return response


# Класс API для получения логов датчика
class SensorLogsAPIView(View):
    def get(self, request, *args, **kwargs):
        sensor_id = self.kwargs['sensor_id']
        logs = SensorLog.objects.filter(sensor_id=sensor_id).order_by('timestamp')
        data = [[log.timestamp.timestamp() * 1000, log.previous_watt] for log in logs]
        return JsonResponse(data, safe=False)


# Класс API для получения логов напряжения датчика
class SensorLogsVoltAPIView(View):
    def get(self, request, *args, **kwargs):
        sensor_id = self.kwargs['sensor_id']
        logs = SensorLog.objects.filter(sensor_id=sensor_id).order_by('timestamp')
        data = [[log.timestamp.timestamp() * 1000, log.previous_volt] for log in logs]
        return JsonResponse(data, safe=False)


# Функция для поиска датчиков
def search_sensors(request):
    query = request.GET.get('q')

    if query:
        sensors = Sensor.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(owner__icontains=query) |
            Q(country__name__icontains=query) |
            Q(city__name__icontains=query) |
            Q(inclusions__icontains=query)
        ).distinct()
    else:
        sensors = Sensor.objects.all()

    return render(request, 'sensor/search_results.html', {'sensors': sensors, 'query': query})


@csrf_exempt
def receive_data(request):
    if request.method == 'POST':
        start_time = time.time()
        try:
            data = json.loads(request.body)
            name = data.get('name', '')
            temperature = data.get('temperature', 0.0)
            humidity = data.get('humidity', 0.0)
            inclusions = data.get('inclusions', 0)
            power = data.get('power', 0)
            watt = data.get('watt', 0)
            volt = data.get('volt', 0)
            work = data.get('work', False)
            blocked = data.get('blocked', False)
            fan_speed = data.get('fan_speed', 0)
            ip_address = data.get('ip_address', '')
            mac_address = data.get('mac_address', '')
            version = data.get('version', '')
            owner = data.get('owner', '')

            sensor, created = Sensor.objects.get_or_create(name=name)
            sensor.temperature = temperature
            sensor.humidity = humidity
            sensor.inclusions = inclusions
            sensor.power = power
            sensor.watt = watt
            sensor.volt = volt
            sensor.work = work
            sensor.blocked = blocked
            sensor.fan_speed = fan_speed
            sensor.ip_address = ip_address
            sensor.mac_address = mac_address
            sensor.version = version
            sensor.owner = owner
            sensor.timestamp = timezone.now()

            end_time = time.time()
            processing_time = round((end_time - start_time) * 1000, 2)

            sensor.processing_time = processing_time
            sensor.save()

            threshold = timedelta(minutes=5)
            time_since_last_update = timezone.now() - sensor.timestamp
            if time_since_last_update > threshold:
                sensor.work = True
                sensor.save()

            return HttpResponse(f'Новые данные приняты на сервер. Время обработки: {processing_time:.2f} мс')
        except Exception as e:
            return HttpResponse(f'Ошибка при обработке данных: {e}', status=500)

    return HttpResponse('Отказано!')


class DeviceStatus(APIView):
    def get(self, request, slug):
        try:
            sensor = Sensor.objects.get(slug=slug)

            device_status = {
                "name": sensor.name,
                "blocked": sensor.blocked,
                "work": sensor.work,
            }

            return Response(device_status, status=status.HTTP_200_OK)
        except Sensor.DoesNotExist:
            return Response({"error": "Устройство не найдено"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Произошла ошибка: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_csrf_token(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrf_token': csrf_token})


def esp_update(request):
    if request.method == 'POST':
        firmware_file = request.FILES['firmware']
        device_name = os.path.splitext(firmware_file.name)[0]
        firmware_path = os.path.join(settings.MEDIA_ROOT, 'firmwares', f'{device_name}.bin')
        version = request.POST.get('firmware_version', '')

        os.makedirs(os.path.dirname(firmware_path), exist_ok=True)

        with open(firmware_path, 'wb+') as destination:
            for chunk in firmware_file.chunks():
                destination.write(chunk)

        actual_filename = f'{device_name}.bin'
        firmware = Firmware(version=version, file=actual_filename)
        firmware.save()

        messages.success(request, 'Прошивка успешно загружена')
        return redirect('sensor_list')
    return redirect('sensor_list')


def get_latest_firmware(request):
    try:
        latest_firmware = Firmware.objects.latest('uploaded_at')
        filename = latest_firmware.file.name
        return JsonResponse({'version': latest_firmware.version, 'url': filename})
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Прошивки не найдены'}, status=404)


def download_firmware(request, version):
    firmware = get_object_or_404(Firmware, version=version)
    return FileResponse(firmware.file)
