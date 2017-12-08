from django.db import models


class InterestRate(models.Model):
    # Decimal instead of float to ensure precise representation
    rate = models.DecimalField(max_digits=8, decimal_places=5)