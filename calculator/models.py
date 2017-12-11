from django.db import models
from django.utils import timezone
from decimal import Decimal


class InterestRate(models.Model):
    # Decimal instead of float to ensure precise representation
    rate = models.DecimalField(max_digits=8, decimal_places=7)
    # Start time of the period where this interest rate is in effect
    since = models.DateTimeField(default=timezone.now)

    @staticmethod
    def get_rate_at_time(time):
        interest_rate = InterestRate.objects.filter(
            since__lte=time).order_by('-since', '-id')[0]
        rate = interest_rate.rate
        return rate

    def __str__(self):
        return "{0:0.2f}%".format(self.rate * 100)
