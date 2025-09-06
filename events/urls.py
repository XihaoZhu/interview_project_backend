from django.urls import path
from .views import EventViewSet
from .views import EventExceptionViewSet

urlpatterns = [
    path('events/', EventViewSet.as_view({'get': 'list','post':'create'}), name='get_events'),
    path('modify_event/<int:pk>/', EventViewSet.as_view({'put':'partial_update','delete':'destroy'}), name='modify_event'),
    path('exceptions/', EventExceptionViewSet.as_view({'post': 'create'}), name='create_exception'),           
    path('exceptions/<int:pk>/', EventExceptionViewSet.as_view({'patch': 'partial_update'}), name='update_exception'), 
]