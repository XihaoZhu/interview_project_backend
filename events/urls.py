from django.urls import path
from .views import EventViewSet

urlpatterns = [
    path('get_events/', EventViewSet.as_view({'get': 'list','post':'create'}), name='get_events'),
    path('modify_event/<int:pk>/', EventViewSet.as_view({'get': 'retrieve','put':'update','delete':'destroy'}), name='modify_event'),
]