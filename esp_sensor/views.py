from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Sensor
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging


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

        # Открываем файл логов и заменяем значения на текстовые сообщения
        with open('sqlite3.log', 'r') as log_file:
            logs = log_file.readlines()
            logs = [log.replace('True', 'Датчик включен').replace('False', 'Датчик выключен') for log in logs]

        context['logs'] = logs

        return context

    def post(self, request, *args, **kwargs):
        sensor = self.get_object()
        previous_work_state = sensor.work  # Запоминаем предыдущее состояние датчика
        sensor.work = not sensor.work
        sensor.save()

        # Запись лога внутри метода post с использованием вашего собственного логгера
        logger = logging.getLogger('your_custom_logger')

        if sensor.work:
            log_message = f"Датчик {sensor.name} включен."
        else:
            log_message = f"Датчик {sensor.name} выключен."

        logger.info(log_message)

        return JsonResponse({'success': True})


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

# @csrf_exempt
# def update_sensor(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             sensor_id = data.get('id')
#             if sensor_id is not None:
#                 sensor = Sensor.objects.get(pk=sensor_id)
#                 sensor.name = data.get('name', sensor.name)
#                 sensor.slug = data.get('slug', sensor.slug)
#                 sensor.description = data.get('description', sensor.description)
#                 sensor.owner = data.get('owner', sensor.owner)
#                 sensor.inclusions = data.get('inclusions', sensor.inclusions)
#                 sensor.power = data.get('power', sensor.power)
#                 sensor.work = data.get('work', sensor.work)
#                 sensor.save()
#                 return JsonResponse({'success': True, 'message': 'Sensor updated successfully.'})
#             else:
#                 return JsonResponse({'success': False, 'message': 'Sensor ID not provided.'})
#         except Exception as e:
#             return JsonResponse({'success': False, 'message': str(e)})
#     else:
#         return JsonResponse({'success': False, 'message': 'Invalid request method.'})
