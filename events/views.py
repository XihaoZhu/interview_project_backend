from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime,parse_date
from django.utils.timezone import make_aware, get_default_timezone, is_aware, make_naive, is_naive    
from datetime import timezone
from rest_framework import status
from dateutil import rrule
from datetime import datetime, time
from zoneinfo import ZoneInfo   
from dateutil.rrule import rrulestr
from django.shortcuts import get_object_or_404

from .models import Event, EventException
from .serializers import EventSerializer, EventExceptionSerializer


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    queryset = Event.objects.all()

    #take start and end time to filter and return events
    def list(self, request, *args, **kwargs):

        event_type = request.query_params.get("type", None)
        start_time = request.query_params.get("start")
        end_time = request.query_params.get("end")
        user_tz = request.query_params.get("timezone")

        if not (start_time and end_time and user_tz):
            return Response(
            {"error": "'start', 'end' and 'timezone' query parameters are required."},
            status=status.HTTP_400_BAD_REQUEST
        )
        
        start_time = parse_date(start_time)
        end_time   = parse_date(end_time)
        user_tz = ZoneInfo(user_tz)

        if not (start_time and end_time and user_tz):
            return Response(
                {"error": "Invalid 'start_time' or 'end_time' date format."},
                status=status.HTTP_400_BAD_REQUEST
            ) 
        
        #UTC time transformation
        start_time = make_aware(datetime.combine(start_time, time.min), user_tz)
        end_time = make_aware(datetime.combine(end_time, time.max), user_tz)
        
        start_time = start_time.astimezone(timezone.utc)
        end_time = end_time.astimezone(timezone.utc)


        #single events within range    
        events_list = Event.objects.filter(
            repeat_rule='',
            start_time__lte=end_time,
            end_time__gte=start_time
        )

        #Now filter by type if provided
        if event_type:
            events_list = events_list.filter(type=event_type)

        #repeating events
        rrule_events = Event.objects.exclude(repeat_rule__isnull=True).exclude(repeat_rule__exact='')
        
        if event_type:
            rrule_events = rrule_events.filter(type=event_type)
        
        occurrences_list = []

        for event in rrule_events:

            # To handle the day light saving time change, my idea is to transform the event start time to the event local timezone, then let rrule parse the rule.
            localTimezone = event.buid_timeZone if event.buid_timeZone else 'UTC'
            localStart = event.start_time.astimezone(ZoneInfo(localTimezone))
            
            rule = rrulestr(event.repeat_rule, dtstart=localStart)

            occurrences = rule.between(start_time.astimezone(ZoneInfo(localTimezone)),end_time.astimezone(ZoneInfo(localTimezone)), inc=True)

            #because it was timestamp we stored instead of time and date, so calculate duration to get end time
            duration = event.end_time - event.start_time

            for occ_start in occurrences:
                
                occ_start = occ_start.astimezone(timezone.utc)
                occ_end = occ_start + duration

                # check for exceptions
                exception = event.exceptions.filter(occurrence_time=occ_start).first()
                if exception:
                    if exception.exception_type == "skip":
                        continue

                occurrences_list.append({
                    "parent": exception.event if exception else event,
                    "sub_id": exception.sub_id if exception else None,
                    "occurrence_id": f"{event.id}_{int(occ_start.timestamp())}",
                    "title": exception.new_title if exception and exception.new_title else event.title,
                    "note": exception.new_note if exception and exception.new_note else event.note,
                    "link": exception.new_link if exception and exception.new_link else event.link,
                    "extra_info": exception.new_extra_info if exception and exception.new_extra_info else event.extra_info,
                    "start_time": exception.new_start_time if exception and exception.new_start_time else occ_start,
                    "end_time": exception.new_end_time if exception and exception.new_end_time else occ_end,
                    "type": exception.new_type if exception and exception.new_type else event.type,
                })

        #serialize and return
        serializer = self.get_serializer(list(events_list)+occurrences_list, many=True)
        return Response(serializer.data)
 
    #Create, validate and save new event        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        event = serializer.save()

        return Response(
            self.get_serializer(event).data,
            status=status.HTTP_201_CREATED
        )
    
    #update existing event
    def partial_update(self, request, *args, **kwargs):
        mutable_data = request.data.copy()
        for field in ['id', 'created_at', 'updated_at']:
            mutable_data.pop(field, None)
        return super().partial_update(request, *args, **kwargs, data=mutable_data)                                                                                                                                                                                                                                                                                                      

    #delete cann just use the default destroy method                                                                                                       

'''My logic for handling exceptions for repeating events.
    it's regular for create of both skip and modify type.   
    but for delete function, you can't delete skip as it's not shown in the list
    and for modify, delete it I will just change the type to skip so it won't be selectable too
    hhhhhhhhhhh
    '''

class EventExceptionViewSet(viewsets.ModelViewSet):
    serializer_class = EventExceptionSerializer
    queryset = EventException.objects.all()

    def create(self, request, *args, **kwargs):

        data = request.data.copy()

        occurrence_time = data.get("occurrence_time")
        if not occurrence_time:
            return Response({"error": "occurrence_time is required, need it to target which one"}, status=400)
        
        event_id = data.get("mother_id")
        if not event_id:
            return Response({"error": "You need a mother event to create exception"}, status=400)

        event = get_object_or_404(Event, id=event_id)

        for field, default in [
        ("new_start_time", event.start_time),
        ("new_end_time", event.end_time),
        ("new_title", event.title),
        ("new_description", event.note),
        ("new_link", event.link),
        ("new_extra_info", event.extra_info),
        ("new_note", event.note),
        ("new_type", event.type)
    ]:
            if data.get(field) is None:
                data[field] = default

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(event=event)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        mutable_data = request.data.copy()
        for field in ['sub_id', 'modified_at']:
            mutable_data.pop(field, None)
        return super().partial_update(request, *args, **kwargs, data=mutable_data)   
# the destroy method remains original, maybe admin can use it for some reason   