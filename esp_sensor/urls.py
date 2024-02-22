from django.urls import path
from . import views
from .views import SensorDetailView, SensorListView, SensorLogsAPIView

urlpatterns = [
    path('', SensorListView.as_view(), name='sensor_list'),
    path('sensors/<int:pk>/', SensorDetailView.as_view(), name='sensor_detail'),
    path('api/sensor_logs/<int:sensor_id>/', SensorLogsAPIView.as_view(), name='sensor_logs_api'),
    path('search/', views.search_sensors, name='search_sensors'),
    path('sensor/<int:sensor_id>/stream_logs/', views.stream_sensor_logs, name='stream_sensor_logs'),
]
