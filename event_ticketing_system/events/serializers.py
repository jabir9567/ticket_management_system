from rest_framework import serializers
from .models import Event, PromoCode

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = ['id', 'code', 'discount_type', 'discount_value', 'total_supply', 'usage_count']   