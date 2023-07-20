from django.shortcuts import render
from django.views.generic import ListView

from .models import Sensor


# Create your views here.
class SensorListView(ListView):
    model = Sensor
    template_name = 'sensor/sensor_list.html'
    context_object_name = 'sensors'
