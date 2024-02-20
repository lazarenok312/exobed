from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Sensor, SensorLog, SensorData
import json
from django.http import JsonResponse


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

        power_data = SensorData.objects.filter(sensor=sensor).order_by('timestamp')
        print(power_data)
        power_values = [{'timestamp': str(item.timestamp), 'value': item.value} for item in power_data]
        context['logs'] = logs
        context['power_data'] = power_values

        return context

    def post(self, request, *args, **kwargs):
        sensor = self.get_object()
        previous_work_state = sensor.work
        previous_power = sensor.power
        previous_watt = sensor.watt
        previous_volt = sensor.volt
        sensor.work = not sensor.work
        sensor.save()

        if previous_power != sensor.power:
            log_type = 'Изменение мощности'
            SensorLog.objects.create(sensor=sensor, log_type=log_type, previous_power=previous_power)
        elif previous_watt != sensor.watt:
            log_type = 'Изменение мощности'
            SensorLog.objects.create(sensor=sensor, log_type=log_type, previous_watt=previous_watt)
        elif previous_volt != sensor.volt:
            log_type = 'Изменение напряжения'
            SensorLog.objects.create(sensor=sensor, log_type=log_type, previous_volt=previous_volt)

        log_type = 'Включение' if sensor.work else 'Выключение'
        SensorLog.objects.create(sensor=sensor, log_type=log_type, previous_power=previous_power,
                                 previous_watt=previous_watt, previous_volt=previous_volt)

        logs = SensorLog.objects.filter(sensor=sensor)
        for log in logs:
            print(log.previous_watt)

        return JsonResponse({'success': True, 'power_changed': previous_power != sensor.power})


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
