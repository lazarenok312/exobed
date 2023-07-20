from django.urls import path
from .views import SensorListView

from . import views
urlpatterns = [
    path('', SensorListView.as_view(), name='sensor_list'),
]