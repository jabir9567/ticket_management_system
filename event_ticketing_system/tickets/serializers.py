from rest_framework import serializers
from .models import Booking, Event, Reservation

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    seats = serializers.JSONField()

    class Meta:
        model = Event
        fields = ['event_id', 'name', 'date', 'vip_price', 'standard_price', 'seats']
        
class ReservationSerializer(serializers.ModelSerializer):
    expires_at = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = '__all__'  # This includes all reservation details along with expires_at

    def get_expires_at(self, obj):
        return obj.expires_at