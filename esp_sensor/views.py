from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Sensor


# Create your views here.
class SensorListView(ListView):
    model = Sensor
    template_name = 'sensor/sensor_list.html'
    context_object_name = 'sensors'


class SensorDetailView(DetailView):
    model = Sensor
    template_name = 'sensor/sensor_detail.html'
    context_object_name = 'sensor'


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
