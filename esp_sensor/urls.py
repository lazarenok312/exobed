from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('', SensorListView.as_view(), name='sensor_list'),
    path('sensors/<int:pk>/', SensorDetailView.as_view(), name='sensor_detail'),

    path('sensor-logs/<int:sensor_id>/', views.stream_sensor_logs, name='sensor_logs'),
    path('search/', views.search_sensors, name='search_sensors'),
    path('update_sensor_power/<int:sensor_id>/', views.update_sensor_power, name='update_sensor_power'),
    path('block_toggle/<int:sensor_id>/', views.block_toggle, name='block_toggle'),
    path('toggle_start/<int:sensor_id>/', views.toggle_start, name='toggle_start'),
    path('download-logs/<slug:device_slug>/', views.download_logs, name='download_logs'),
    path('sensor-detail-ajax/<int:sensor_id>/', sensor_detail_ajax, name='sensor_detail_ajax'),
    path('sensor/<int:pk>/', SensorDetailView.as_view(), name='sensor_detail'),
    path('sensor/<int:pk>/delete/', SensorDeleteView.as_view(), name='sensor_delete'),
    path('get_csrf_token/', get_csrf_token, name='get_csrf_token'),

    path('device/<slug:slug>/', DeviceStatus.as_view(), name='device_status'),
    path('esp_update/', views.esp_update, name='esp_update'),

    path('api/data/', views.receive_data, name='receive_data'),
    path('api/sensor_logs/<int:sensor_id>/', SensorLogsAPIView.as_view(), name='sensor_logs_api'),
    path('api/sensor_logs_volt/<int:sensor_id>/', SensorLogsVoltAPIView.as_view(), name='sensor_logs_volt_api'),
    path('api/latest-firmware/', get_latest_firmware, name='latest_firmware'),
    path('api/download-firmware/<str:version>/', download_firmware, name='download_firmware'),

    path('esp_update/', views.esp_update, name='esp_update'),

    path('confirm_sensor/<int:sensor_id>/', ConfirmSensorView.as_view(), name='confirm_sensor'),
]
