from django.urls import path
from .views import EventListCreateView, EventDetailView, PromoCodeListCreateView

urlpatterns = [
    path('events/', EventListCreateView.as_view(), name='event-list'),
    path('events/<int:pk>/', EventDetailView.as_view(), name='event-detail'),
    path('promocodes/', PromoCodeListCreateView.as_view(), name='promocode-list-create'),
]
