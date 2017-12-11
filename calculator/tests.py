from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from .models import InterestRate
import json


class InterestRateModelTests(TestCase):

    def test_get_rate_at_time(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        now = timezone.now()

        self.assertEqual(InterestRate.get_rate_at_time(now), Decimal("0.025"))

        # populate database
        InterestRate.objects.bulk_create([
            InterestRate(rate=Decimal("0.01"), since=now + timedelta(hours=-2)),
            InterestRate(rate=Decimal("0.02"), since=now + timedelta(hours=-1)),
            InterestRate(rate=Decimal("0.03"), since=now + timedelta(hours=0)),
            InterestRate(rate=Decimal("0.04"), since=now + timedelta(hours=1)),
            InterestRate(rate=Decimal("0.05"), since=now + timedelta(hours=2))])

        self.assertEqual(InterestRate.get_rate_at_time(now), Decimal("0.03"))

        self.assertEqual(InterestRate.get_rate_at_time(now + timedelta(seconds=1)), Decimal("0.03"))
        self.assertEqual(InterestRate.get_rate_at_time(now + timedelta(seconds=-1)), Decimal("0.02"))
        self.assertEqual(InterestRate.get_rate_at_time(now + timedelta(hours=1)), Decimal("0.04"))
        self.assertEqual(InterestRate.get_rate_at_time(now + timedelta(hours=-1, seconds=-1)), Decimal("0.01"))

    def test_payment_amount_methods(self):
        response = self.client.get(reverse('calculator:payment amount'))
        self.assertEqual(response.status_code, 400)
        response = self.client.post(reverse('calculator:payment amount'))
        self.assertEqual(response.status_code, 405)
        response = self.client.patch(reverse('calculator:payment amount'))
        self.assertEqual(response.status_code, 405)

    def test_payment_amount(self):
        now = timezone.now()
        self.assertEqual(InterestRate.get_rate_at_time(now), Decimal("0.025"))
        querystring = '?askingprice=500000&downpayment=80000&paymentschedule=weekly&amortizationperiod=15'
        response = self.client.get(reverse('calculator:payment amount') + querystring)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data.get('result'), 'success')
        self.assertAlmostEqual(data.get('response'), 655.00, places=2)

        # amortization period out of range
        querystring = '?askingprice=500000&downpayment=80000&paymentschedule=weekly&amortizationperiod=4'
        response = self.client.get(reverse('calculator:payment amount') + querystring)
        self.assertEqual(response.status_code, 400)
        querystring = '?askingprice=500000&downpayment=80000&paymentschedule=weekly&amortizationperiod=26'
        response = self.client.get(reverse('calculator:payment amount') + querystring)
        self.assertEqual(response.status_code, 400)
        # payment schedule invalid
        querystring = '?askingprice=500000&downpayment=80000&paymentschedule=daily&amortizationperiod=15'
        response = self.client.get(reverse('calculator:payment amount') + querystring)
        self.assertEqual(response.status_code, 400)
        # downpayment too small
        querystring = '?askingprice=500000&downpayment=10000&paymentschedule=biweekly&amortizationperiod=15'
        response = self.client.get(reverse('calculator:payment amount') + querystring)
        self.assertEqual(response.status_code, 400)

    def test_mortgage_amount_methods(self):
        response = self.client.get(reverse('calculator:mortgage amount'))
        self.assertEqual(response.status_code, 400)
        response = self.client.post(reverse('calculator:mortgage amount'))
        self.assertEqual(response.status_code, 405)
        response = self.client.patch(reverse('calculator:mortgage amount'))
        self.assertEqual(response.status_code, 405)

    def test_mortgage_amount(self):
        now = timezone.now()
        self.assertEqual(InterestRate.get_rate_at_time(now), Decimal("0.025"))
        querystring = '?paymentamount=1500&downpayment=80000&paymentschedule=biweekly&amortizationperiod=5'
        response = self.client.get(reverse('calculator:mortgage amount') + querystring)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data.get('result'), 'success')
        self.assertAlmostEqual(data.get('response'), 271972.13, places=2)

        # amortization period out of range
        querystring = '?paymentamount=1500&downpayment=80000&paymentschedule=biweekly&amortizationperiod=4'
        response = self.client.get(reverse('calculator:mortgage amount') + querystring)
        self.assertEqual(response.status_code, 400)
        querystring = '?paymentamount=1500&downpayment=80000&paymentschedule=biweekly&amortizationperiod=26'
        response = self.client.get(reverse('calculator:mortgage amount') + querystring)
        self.assertEqual(response.status_code, 400)
        # payment schedule invalid
        querystring = '?paymentamount=1500&downpayment=80000&paymentschedule=annual&amortizationperiod=5'
        response = self.client.get(reverse('calculator:mortgage amount') + querystring)
        self.assertEqual(response.status_code, 400)
        # no downpayment
        querystring = '?paymentamount=2000&paymentschedule=monthly&amortizationperiod=15'
        response = self.client.get(reverse('calculator:mortgage amount') + querystring)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data.get('result'), 'success')
        self.assertAlmostEqual(data.get('response'), 299944.87, places=2)

    def test_interest_rate_methods(self):
        response = self.client.get(reverse('calculator:interest rate'))
        self.assertEqual(response.status_code, 405)
        response = self.client.post(reverse('calculator:interest rate'))
        self.assertEqual(response.status_code, 405)
        response = self.client.patch(reverse('calculator:interest rate'))
        self.assertEqual(response.status_code, 400)

    def test_interest_rate(self):
        now = timezone.now()
        self.assertEqual(InterestRate.get_rate_at_time(now), Decimal("0.025"))

        request_data = json.dumps({'interestrate': 0.05})
        response = self.client.patch(reverse('calculator:interest rate'), data=request_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data.get('result'), 'success')
        self.assertEqual(data.get('response', {}).get('new_rate'), '0.0500000')
        self.assertEqual(data.get('response', {}).get('old_rate'), '0.025')

        now = timezone.now()
        self.assertEqual(InterestRate.get_rate_at_time(now), Decimal("0.05"))
