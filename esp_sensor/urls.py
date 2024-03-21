from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('', SensorListView.as_view(), name='sensor_list'),
    path('sensors/<int:pk>/', SensorDetailView.as_view(), name='sensor_detail'),
    path('api/sensor_logs/<int:sensor_id>/', SensorLogsAPIView.as_view(), name='sensor_logs_api'),
    path('api/sensor_logs_volt/<int:sensor_id>/', SensorLogsVoltAPIView.as_view(), name='sensor_logs_volt_api'),
    path('search/', views.search_sensors, name='search_sensors'),
    # path('sensor/<int:sensor_id>/stream_logs/', views.stream_sensor_logs, name='stream_sensor_logs'),
    path('update_sensor_power/<int:sensor_id>/', views.update_sensor_power, name='update_sensor_power'),
    path('block_toggle/<int:sensor_id>/', views.block_toggle, name='block_toggle'),
    path('download-logs/<slug:device_slug>/', download_logs, name='download_logs'),
]
