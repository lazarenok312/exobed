from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.views.generic import View
from .models import Sensor, SensorLog
from django.core.paginator import Paginator
import json
import time
from django.template.loader import render_to_string


class SensorListView(ListView):
    model = Sensor
    template_name = 'sensor/sensor_list.html'
    context_object_name = 'sensors'
    paginate_by = 6

    def get_queryset(self):
        return Sensor.objects.order_by('id')


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

        return JsonResponse({'success': True, 'power_changed': previous_power != sensor.power})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sensor = self.get_object()
        logs = sensor.sensorlog_set.all().order_by('-timestamp')
        paginator = Paginator(logs, 10)  # Здесь 10 - количество логов на странице
        page_number = self.request.GET.get('page')
        page_logs = paginator.get_page(page_number)
        context['logs'] = page_logs
        context['sensor_id'] = sensor.id

        if logs.exists():
            context['latest_log'] = logs.last()
        else:
            context['latest_log'] = None
        return context

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


def block_toggle(request, sensor_id):
    sensor = get_object_or_404(Sensor, pk=sensor_id)
    sensor.blocked = not sensor.blocked
    sensor.save()
    redirect_url = request.META.get('HTTP_REFERER') or reverse(
        'home')
    return HttpResponseRedirect(redirect_url)


def download_logs(request, device_slug):
    # Получаем объект Sensor по его slug
    sensor = get_object_or_404(Sensor, slug=device_slug)

    logs = SensorLog.objects.filter(sensor=sensor)  # Получаем все логи для данного датчика

    # Здесь вы можете создать строку с данными в нужном формате, используя функцию render_to_string
    # Например, если вы хотите сгенерировать CSV файл:
    csv_data = render_to_string('logs/csv_template.txt', {'logs': logs})

    # Используйте имя устройства для формирования имени файла
    filename = f'{sensor.name}_logs.csv'

    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def update_sensor_power(request, sensor_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        power = request.POST.get('power')

        sensor = Sensor.objects.get(pk=sensor_id)
        previous_power = sensor.power
        sensor.power = power
        sensor.save()

        log_type = 'Изменение мощности'
        SensorLog.objects.create(sensor=sensor, log_type=log_type, previous_power=previous_power,
                                 previous_watt=sensor.watt, previous_volt=sensor.volt)

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'error': 'This endpoint only accepts AJAX requests'}, status=400)


def stream_sensor_logs(request, sensor_id):
    if not sensor_id:
        return HttpResponseBadRequest("No sensor_id provided")

    response = HttpResponse(content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'

    def get_sensor_logs(sensor_id):
        logs = SensorLog.objects.filter(sensor_id=sensor_id).order_by('timestamp')
        data = [[log.timestamp.timestamp() * 1000, log.previous_watt] for log in logs]
        return data

    def generate():
        while True:
            logs = get_sensor_logs(sensor_id)
            yield "data: %s\n\n" % json.dumps(logs)
            time.sleep(1)

    response.streaming_content = generate()
    return response


class SensorLogsAPIView(View):
    def get(self, request, *args, **kwargs):
        sensor_id = self.kwargs['sensor_id']
        logs = SensorLog.objects.filter(sensor_id=sensor_id).order_by('timestamp')
        data = [[log.timestamp.timestamp() * 1000, log.previous_watt] for log in logs]
        return JsonResponse(data, safe=False)


class SensorLogsVoltAPIView(View):
    def get(self, request, *args, **kwargs):
        sensor_id = self.kwargs['sensor_id']
        logs = SensorLog.objects.filter(sensor_id=sensor_id).order_by('timestamp')
        data = [[log.timestamp.timestamp() * 1000, log.previous_volt] for log in logs]
        return JsonResponse(data, safe=False)


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
