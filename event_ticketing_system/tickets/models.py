from django.db import models
from django.utils import timezone
from events.models import Event
from decimal import Decimal

class Booking(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=50)
    tickets = models.JSONField()  # e.g., [{'type': 'VIP', 'quantity': 2}]
    seat_selection = models.JSONField()  # e.g., ['A1', 'A2']
    promo_code = models.CharField(max_length=20, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    cancellation_insurance = models.BooleanField(default=False)

class Reservation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=50)
    tickets = models.JSONField()
    seat_selection = models.JSONField()
    promo_code = models.CharField(max_length=20, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=8, decimal_places=2)
    cancellation_insurance = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def expires_at(self):
        return self.created_at + timezone.timedelta(minutes=1) #set timer for 10 minute
    
    def is_expired(self):
        return timezone.now() > self.expires_at
#todo
'''implement feature of adding seats by mapping as VIP & standard. Book tier wise'''