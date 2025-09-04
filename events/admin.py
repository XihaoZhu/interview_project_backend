from django.contrib import admin
from .models import Event, EventException

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'type', 'parent')
    search_fields = ('id','note')

@admin.register(EventException)
class EventExceptionAdmin(admin.ModelAdmin):
    list_display = ('event', 'occurrence_date', 'exception_type')
    search_fields = ('event__title',)
