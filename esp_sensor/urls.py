from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path('', SensorListView.as_view(), name='sensor_list'),
    path('sensors/<int:pk>/', views.SensorDetailView.as_view(), name='sensor_detail'),
    path('search/', views.search_sensors, name='search_sensors'),
    # path('update/', views.update_sensor, name='update')
]
