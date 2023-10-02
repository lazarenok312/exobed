from django import forms
from .models import Sensor

class SensorWorkForm(forms.ModelForm):
    class Meta:
        model = Sensor
        fields = ['work']