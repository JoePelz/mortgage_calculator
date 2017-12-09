from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from .models import InterestRate


class InterestRateModelTests(TestCase):

    def test_get_rate_at_time(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        now = timezone.now()

        self.assertEqual(InterestRate.get_rate_at_time(now), Decimal("0.025"))

        InterestRate.objects.create(rate=Decimal("0.01"), since=now + timedelta(hours=-2))
        InterestRate.objects.create(rate=Decimal("0.02"), since=now + timedelta(hours=-1))
        InterestRate.objects.create(rate=Decimal("0.03"), since=now + timedelta(hours=0))
        InterestRate.objects.create(rate=Decimal("0.04"), since=now + timedelta(hours=1))
        InterestRate.objects.create(rate=Decimal("0.05"), since=now + timedelta(hours=2))

        self.assertEqual(InterestRate.get_rate_at_time(now), Decimal("0.03"))

        self.assertEqual(InterestRate.get_rate_at_time(now + timedelta(seconds=1)), Decimal("0.03"))
        self.assertEqual(InterestRate.get_rate_at_time(now + timedelta(seconds=-1)), Decimal("0.02"))
        self.assertEqual(InterestRate.get_rate_at_time(now + timedelta(hours=1)), Decimal("0.04"))
        self.assertEqual(InterestRate.get_rate_at_time(now + timedelta(hours=-1, seconds=-1)), Decimal("0.01"))
