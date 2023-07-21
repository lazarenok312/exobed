from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path('', SensorListView.as_view(), name='sensor_list'),
    path('search/', views.search_sensors, name='search_sensors'),
]
