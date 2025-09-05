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

            dtstart = event.start_time
            
            rule = rrulestr(event.repeat_rule, dtstart=dtstart)

            occurrences = rule.between(start_time,end_time, inc=True)

            #because it was timestamp we stored instead of time and date, so calculate duration to get end time
            duration = event.end_time - event.start_time

            for occ_start in occurrences:
                if is_naive(occ_start):
                    occ_start = make_aware(occ_start, timezone=timezone.utc)

                occ_end = occ_start + duration

                # check for exceptions
                exception = event.exceptions.filter(occurrence_date=occ_start).first()
                if exception:
                    if exception.exception_type == "skip":
                        continue
                    elif exception.exception_type == "modify":
                        occ_start = exception.new_start_time or occ_start
                        occ_end   = exception.new_end_time   or occ_end

                occurrences_list.append({
                    "id": event.id,
                    "occurrence_id": f"{event.id}_{int(occ_start.timestamp())}",
                    "title": exception.new_title if exception and exception.new_title else event.title,
                    "note": exception.new_note if exception and exception.new_note else event.note,
                    "link": exception.new_link if exception and exception.new_link else event.link,
                    "extra_info": exception.new_extra_info if exception and exception.new_extra_info else event.extra_info,
                    "start_time": occ_start,
                    "end_time": occ_end,
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