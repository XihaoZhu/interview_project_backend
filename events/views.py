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
            localStart = event.start_time.astimezone(user_tz)
            rule = rrulestr(event.repeat_rule, dtstart=localStart)

            #occurrences
            occurrences = rule.between(
                start_time.astimezone(user_tz),
                end_time.astimezone(user_tz),
                inc=True
            )
            
            duration = event.end_time - event.start_time
            exceptions = list(event.exceptions.all())

            # sort exceptions
            all_exceptions = sorted(exceptions, key=lambda ex: (
                {'All time': 1, 'This and future': 2, 'This time': 3}[ex.apply_range],
                ex.modified_at or datetime.min
            ),reverse=True)

            # what we need
            final_occurrences = []

            for i, occ_start in enumerate(occurrences):
                occ_start = occ_start.astimezone(timezone.utc)
                occ_end = occ_start + duration
                occurrence_time = occ_start
                applied_sub_id = None
                applied_exception = None  

                for ex in all_exceptions:
                    if applied_exception:
                        if applied_exception.apply_range == "This time":
                            break
                        elif applied_exception.apply_range in ("This and future", "All time") and ex.apply_range in ("This          and future", "All time"):
                            break
                    if ex.exception_type == "skip":
                        if ex.apply_range == "This time" and occ_start == ex.occurrence_time:
                            occ_start = occ_end = None
                            applied_sub_id = ex.sub_id
                            occurrence_time = ex.occurrence_time
                            applied_exception = ex
                            break
                        elif ex.apply_range == "This and future" and occ_start >= ex.occurrence_time:
                            occ_start = occ_end = None
                            applied_sub_id = ex.sub_id
                            applied_exception = ex
                            break
                        elif ex.apply_range == "All time":
                            occ_start = occ_end = None
                            applied_sub_id = ex.sub_id
                            applied_exception = ex
                            break
                    elif ex.exception_type == "modify":
                        if ex.apply_range == "This time" and occ_start == ex.occurrence_time:
                            occ_start = ex.new_start_time
                            occ_end = ex.new_end_time
                            applied_sub_id = ex.sub_id
                            occurrence_time = ex.occurrence_time
                            applied_exception = ex
                            break
                        elif ex.apply_range in ("This and future", "All time") and occ_start >= ex.occurrence_time:
                            delta = ex.new_start_time - ex.occurrence_time
                            occ_start += delta
                            occ_end += delta
                            applied_sub_id = ex.sub_id
                            applied_exception = ex
                            break
                        
                if occ_start is None or occ_end is None:
                    continue
                
                final_occurrences.append({
                    "parent": event,
                    "sub_id": applied_sub_id,
                    "occurrence_time": occurrence_time,
                    "title": event.title,
                    "note": event.note,
                    "link": event.link,
                    "extra_info": event.extra_info,
                    "start_time": occ_start,
                    "end_time": occ_end,
                    "type": event.type,
                })


            occurrences_list.extend(final_occurrences)

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
        
        event_id = data.get("mother_id")

        if not event_id:
            return Response({"error": "You need a mother event to create exception"}, status=400)

        event = get_object_or_404(Event, id=event_id)

        defaults = {
            "new_start_time": event.start_time,
            "new_end_time": event.end_time,
            "new_title": event.title,
            "new_description": event.note,
            "new_link": event.link,
            "new_extra_info": event.extra_info,
            "new_note": event.note,
            "new_type": event.type,
        }

        for key, value in defaults.items():
            data.setdefault(key, value)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(event=event)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        mutable_data = request.data.copy()
        for field in ['sub_id', 'occurrence_time','event', 'modified_at']:
            mutable_data.pop(field, None)

        return super().partial_update(request, *args, **kwargs, data=mutable_data)   
# the destroy method remains original, maybe admin can use it for some reason   