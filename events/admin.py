from django.contrib import admin
from .models import Event, EventException

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent')
    search_fields = ('id','note')

@admin.register(EventException)
class EventExceptionAdmin(admin.ModelAdmin):
    list_display = ('event', 'occurrence_date', 'exception_type')
    search_fields = ('event__title',)
