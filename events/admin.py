from django.contrib import admin
from .models import Event, EventException

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent','id')
    search_fields = ('id','note')
    actions= ['delete_selected']

@admin.register(EventException)
class EventExceptionAdmin(admin.ModelAdmin):
    list_display = ('sub_id','event', 'occurrence_time', 'exception_type')
    search_fields = ('event__title',)
