from django.utils import timezone
from django.http import JsonResponse, HttpResponseNotAllowed
from calculator.models import InterestRate


def request(request):
    # Methods accepted:
    #   GET
    if request.method != 'GET':
        return HttpResponseNotAllowed(permitted_methods=['GET'])

    now = timezone.now()
    rate_per_year = float(InterestRate.get_rate_at_time(now))
    mortgage_amount = MortgageAmountView(rate_per_year)
    return mortgage_amount.get(request)


class MortgageAmountView:
    def __init__(self, interest_rate):
        self.operation = "Mortgage Amount"
        self.params = {}
        self.rate_per_year = interest_rate
        self.errors = []

    def error_response(self, errors):
        response_data = {
            'result': 'error',
            'request': self.operation,
            'request_params': self.params,
            'errors': errors
        }
        response = JsonResponse(response_data)
        response.status_code = 400  # Bad Request
        return response

    def success_response(self, response):
        response_data = {
            'result': 'success',
            'request': self.operation,
            'request_params': self.params,
            'response': response
        }
        return JsonResponse(response_data)

    def decode_params(self, request):
        # Expected parameters:
        #   paymentamount: float
        #   downpayment: float (optional),
        #   paymentschedule: (weekly | biweekly | monthly),
        #   amortizationperiod: float

        # extract variables
        payment_amount = request.GET.get('paymentamount', None)
        down_payment = request.GET.get('downpayment', '0')
        payment_schedule = request.GET.get('paymentschedule', '').lower()
        amortization_period = request.GET.get('amortizationperiod', None)

        # required parameters were present
        if payment_amount is None:
            self.errors.append("missing parameter 'paymentamount'")
        if not payment_schedule:
            self.errors.append("missing parameter 'paymentschedule'")
        if amortization_period is None:
            self.errors.append("missing parameter 'amortizationperiod'")

        if self.errors:
            raise ValueError()

        params = {
            'paymentamount': payment_amount,
            'downpayment': down_payment,
            'paymentschedule': payment_schedule,
            'amortizationperiod': amortization_period
        }
        return params

    def validate(self, params):
        # Validation:
        #   downpayment must be at least 5% of the first $500k plus 10% of any amount above $500k (so $50k on a $750k mortgage)
        #   paymentschedule must be 'weekly', 'biweekly', or 'monthly'
        #   amortizationperiod must be between 5 and 25 years. Expressed as years

        # validate payment amount
        try:
            payment_amount = float(params['paymentamount'])
        except:
            self.errors.append("paymentamount must be a number")
            payment_amount = 0

        # validate down payment
        try:
            down_payment = float(params['downpayment'])
        except:
            self.errors.append("downpayment must be a number")
            down_payment = 0

        # validate payment schedule
        if params['paymentschedule'] not in ('weekly', 'biweekly', 'monthly'):
            self.errors.append("paymentschedule must be one of 'weekly', 'biweekly', or 'monthly'")

        # validate amortization period
        try:
            amortization_period = float(params['amortizationperiod'])
        except:
            self.errors.append("amortizationperiod must be a number")
            amortization_period = 0
        else:
            if not (5 <= amortization_period <= 25):
                self.errors.append("amortizationperiod must be between 5 and 25 years")

        if self.errors:
            raise ValueError()

        valid_params = {
            'paymentamount': payment_amount,
            'downpayment': down_payment,
            'paymentschedule': params['paymentschedule'],
            'amortizationperiod': amortization_period
        }
        return valid_params

    def calculate(self, downpayment, paymentamount, paymentschedule, amortizationperiod):
        # Return:
        #   Maximum mortgage that can be taken out

        if paymentschedule == 'weekly':
            total_payments = int(round(amortizationperiod * 52.177457))
            rate_per_period = self.rate_per_year / 52.177457
        elif paymentschedule == 'biweekly':
            total_payments = int(round(amortizationperiod * 52.177457 / 2))
            rate_per_period = self.rate_per_year / 52.177457 / 2
        else:
            total_payments = int(round(amortizationperiod * 12))
            rate_per_period = self.rate_per_year / 12

        # payment formula: P = L[c(1 + c)^n]/[(1 + c)^n - 1]
        c = rate_per_period
        n = total_payments
        P = paymentamount
        L = P * ((1 + c) ** n - 1) / (c * (1 + c) ** n)

        mortgage = L + downpayment

        # or, if we calculate mortgage insurance:
        # mortgage = L / (1 + insurance_rate) + downPayment

        return mortgage

    def get(self, request):
        try:
            raw_params = self.decode_params(request)
            self.params = self.validate(raw_params)
            result = self.calculate(**self.params)
        except:
            # Log exceptions here
            return self.error_response(self.errors)

        if self.errors:
            return self.error_response(self.errors)
        return self.success_response(result)
