from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import Event
from .serializers import EventSerializer
from rest_framework.exceptions import ValidationError

class EventModelTest(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="Normal Event",
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            type="meeting",
        )

    def test_start_before_end(self):
        data = {
            "title": "Invalid Event",
            "start": self.event.start_time,
            "end": self.event.end_time,
            "type": "meeting",
        }
        serializer = EventSerializer(data=data)
        self.assertTrue(serializer.is_valid)

    def test_start_after_end(self):
        """ileagal case with end time before start time"""
        start = timezone.now()
        end = start - timedelta(hours=1)
        
        data = {
            "title": "Invalid Event",
            "start_time": start,
            "end_time": end,
            "type": "meeting",
        }

        serializer = EventSerializer(data=data)

        with self.assertRaises(ValidationError):
            (serializer.is_valid(raise_exception=True)
            )