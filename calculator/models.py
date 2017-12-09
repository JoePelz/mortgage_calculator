from django.db import models
from django.utils import timezone


class InterestRate(models.Model):
    # Decimal instead of float to ensure precise representation
    rate = models.DecimalField(max_digits=8, decimal_places=7)
    # Start time of the period where this interest rate is in effect
    since = models.DateTimeField(default=timezone.now)
