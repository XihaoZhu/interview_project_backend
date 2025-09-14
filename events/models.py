from django.db import models
from django.utils import timezone

class Event(models.Model):
    """
    Thre regular event model
    I build creat and modify time too even I don't plan to use it here as it's for interview purpose. 
    """
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200, blank=False) 
    link = models.URLField(blank=True, null=True)
    note = models.TextField(blank=True)
    extra_info = models.CharField(blank=True, null=True,max_length=30)
    start_time = models.DateTimeField()
    buid_timeZone = models.CharField(max_length=50, blank=False, default="UTC")
    end_time = models.DateTimeField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    occurrence_time = models.DateTimeField()
    type = models.CharField(choices=[("meeting", "meeting"), ("event", "event"),("first_appointment", "first_appointment"),("presentation", "presentation")], max_length=50)
    sub_id = models.TextField(blank=True,null=True)

    # for rrule
    repeat_rule = models.TextField(blank=True, null=True)

    # if this event is an occurrence of a repeating event
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="occurrences"
    )

    def save(self, *args, **kwargs):
        if not self.occurrence_time:
            self.occurrence_time = self.start_time
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class EventException(models.Model):
    """
    I didn't come up with the idea I searched for how people handle exceptions for repeating events. :P
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="exceptions")

    sub_id = models.AutoField(primary_key=True)

    occurrence_time = models.DateTimeField(null=True,blank=True) 

    exception_type = models.CharField(
        max_length=20,
        choices=[("skip", "Skip"), ("modify", "Modify")]
    )

    new_start_time = models.DateTimeField(null=True, blank=True)
    new_end_time = models.DateTimeField(null=True, blank=True)
    new_title = models.CharField(max_length=200, blank=True, null=True)
    new_description = models.TextField(blank=True, null=True)
    new_link = models.URLField(blank=True, null=True)
    new_extra_info = models.CharField(max_length=30, blank=True, null=True)
    new_note = models.TextField(blank=True, null=True)
    new_type = models.CharField(choices=[("meeting", "meeting"), ("event", "event"),("first time appointment", "first time appointment"),("presentation", "presentation")], max_length=50, blank=True, null=True)
    apply_range = models.CharField(choices=[("This time", "This time"), ("This and future", "This and future"),("All time","All time")],default="This time")

    modified_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.event.title} exception on {self.occurrence_time}"
