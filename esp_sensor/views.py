from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Sensor, SensorLog
from django.http import JsonResponse, HttpResponse
from django.views.generic import View
import json

class SensorListView(ListView):
    model = Sensor
    template_name = 'sensor/sensor_list.html'
    context_object_name = 'sensors'
    paginate_by = 6


class SensorDetailView(DetailView):
    model = Sensor
    template_name = 'sensor/sensor_detail.html'
    context_object_name = 'sensor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sensor = self.get_object()
        logs = SensorLog.objects.filter(sensor=sensor)
        context['logs'] = logs
        context['sensor_id'] = sensor.id  # передача sensor_id в контекст
        return context

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

    def get_sensor_logs(self, sensor_id):
        logs = SensorLog.objects.filter(sensor_id=sensor_id).order_by('timestamp')
        data = [[log.timestamp.timestamp() * 1000, log.previous_watt] for log in logs]
        return data


def stream_sensor_logs(request):
    sensor_id = request.GET.get('sensor_id')  # Получаем sensor_id из параметров запроса
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
            time.sleep(1)  # или любой другой интервал обновления

    response.streaming_content = generate()
    return response


class SensorLogsAPIView(View):
    def get(self, request, *args, **kwargs):
        sensor_id = self.kwargs['sensor_id']
        logs = SensorLog.objects.filter(sensor_id=sensor_id).order_by('timestamp')
        data = [[log.timestamp.timestamp() * 1000, log.previous_watt] for log in logs]
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
