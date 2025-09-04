from rest_framework import serializers
from .models import Event, EventException


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


class EventExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventException
        fields = '__all__'
