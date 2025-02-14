from django.urls import path
from .views import ReserveTicketView, ConfirmPaymentView, CheckSeatAvailabilityView, CancelTicketView, TicketListView

urlpatterns = [
    path('reserve/', ReserveTicketView.as_view(), name='reserve-ticket'),
    path('confirm/', ConfirmPaymentView.as_view(), name='confirm-payment'),
    # path('release-expired/', ReleaseExpiredReservationsView.as_view(), name='release-expired-reservations'),

    path('events/<str:event_id>/seats/', CheckSeatAvailabilityView.as_view(), name='check_seat_availability'),
    path('tickets/cancel/', CancelTicketView.as_view(), name='cancel_ticket'),
    path('tickets/', TicketListView.as_view(), name='ticket-list-all'),

]
