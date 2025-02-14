from django.db import models

class Event(models.Model):
    event_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    date = models.DateTimeField()
    vip_price = models.DecimalField(max_digits=6, decimal_places=2, default=150.00)
    standard_price = models.DecimalField(max_digits=6, decimal_places=2, default=50.00)
    seats = models.JSONField(default=dict)  # {'A1': 'available', 'B1': 'booked'}

    def __str__(self):
        return self.name



class PromoCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=5, decimal_places=2)
    total_supply = models.PositiveIntegerField()
    usage_count = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)  # New field to indicate active status

    def __str__(self):
        return self.code


    
    def is_valid(self):
        # Now simply return the active status.
        return self.active

    def save(self, *args, **kwargs):
        # Automatically update active status: deactivate if usage_count reaches or exceeds total_supply.
        if self.usage_count >= self.total_supply:
            self.active = False
        else:
            self.active = True
        super(PromoCode, self).save(*args, **kwargs)
