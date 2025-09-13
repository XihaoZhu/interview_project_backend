from rest_framework import serializers
from .models import Event, EventException


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'parent', 'occurrence_time']

    def validate(self, attrs):
        start = attrs.get("start_time") or getattr(self.instance, "start_time", None)
        end = attrs.get("end_time") or getattr(self.instance, "end_time", None)

        if start and end and end <= start:
            raise serializers.ValidationError("end_time must be later than start_time。")

        tz = attrs.get("buid_timeZone") or getattr(self.instance, "buid_timeZone", None)
        if not tz:
            raise serializers.ValidationError("buid_timeZone is required")

        rrule = attrs.get("repeat_rule") or getattr(self.instance, "repeat_rule", None)
        if rrule:
            if not rrule.strip().upper().startswith("FREQ="):
                raise serializers.ValidationError("repeat_rule must start with 'FREQ='")

        return attrs


class EventExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventException
        read_only_fields = ['modified_at','event','sub_id']
        fields = '__all__'

    def validate(self, attrs):
        # new start
        new_start = attrs.get("new_start_time")
        new_end = attrs.get("new_end_time")

        # partial_update 
        if self.instance:
            if new_start is None:
                new_start = self.instance.new_start_time or self.instance.event.start_time
            if new_end is None:
                new_end = self.instance.new_end_time or self.instance.event.end_time
        else:  # create
            event = self.context.get("event")
            if new_start is None:
                new_start = event.start_time
            if new_end is None:
                new_end = event.end_time

        # time validyation
        if new_start and new_end and new_start >= new_end:
            raise serializers.ValidationError("new_start_time must be before new_end_time")

        return attrs