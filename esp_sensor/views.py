from django.shortcuts import render, get_object_or_404
from django.views.generic import View, ListView, DetailView, DeleteView
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest, StreamingHttpResponse
from django.urls import reverse, reverse_lazy
from .models import Sensor, SensorLog
from django.core.paginator import Paginator
import json
import time
from django.template.loader import render_to_string
from .data_generator import generate_random_data

def some_view(request):
    generate_random_data()

# Класс для отображения списка датчиков
class SensorListView(ListView):
    model = Sensor
    template_name = 'sensor/sensor_list.html'
    context_object_name = 'sensors'
    paginate_by = 8

    def get_queryset(self):
        return Sensor.objects.order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sensors = context['sensors']
        for sensor in sensors:
            latest_log = sensor.sensorlog_set.last()
            if latest_log:
                sensor.last_updated = latest_log.timestamp
            else:
                sensor.last_updated = sensor.date_added
        return context


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

# Функция для переключения состояния блокировки датчика
def block_toggle(request, sensor_id):
    sensor = get_object_or_404(Sensor, pk=sensor_id)
    sensor.blocked = not sensor.blocked
    sensor.save()
    redirect_url = request.META.get('HTTP_REFERER') or reverse(
        'home')
    return HttpResponseRedirect(redirect_url)


# Функция для загрузки логов датчика в формате CSV
def download_logs(request, device_slug):
    sensor = get_object_or_404(Sensor, slug=device_slug)

    logs = SensorLog.objects.filter(sensor=sensor)
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
