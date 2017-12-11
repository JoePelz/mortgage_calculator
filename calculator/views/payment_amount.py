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
    payment_amount = PaymentAmountView(rate_per_year)
    return payment_amount.get(request)


class PaymentAmountView:
    def __init__(self, interest_rate):
        self.operation = "Payment Amount"
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
        #   askingprice: float
        #   downpayment: float
        #   paymentschedule: (weekly | biweekly | monthly),
        #   amortizationperiod: float

        # extract variables
        askingPrice = request.GET.get('askingprice', None)
        downPayment = request.GET.get('downpayment', None)
        paymentSchedule = request.GET.get('paymentschedule', '').lower()
        amortizationPeriod = request.GET.get('amortizationperiod', None)

        # required parameters were present
        if askingPrice is None:
            self.errors.append("missing parameter 'askingprice'")
        if downPayment is None:
            self.errors.append("missing parameter 'downpayment'")
        if not paymentSchedule:
            self.errors.append("missing parameter 'paymentschedule'")
        if amortizationPeriod is None:
            self.errors.append("missing parameter 'amortizationperiod'")

        if self.errors:
            raise ValueError()

        params = {
            'askingprice': askingPrice,
            'downpayment': downPayment,
            'paymentschedule': paymentSchedule,
            'amortizationperiod': amortizationPeriod
        }
        return params

    def validate(self, params):
        # Validation:
        #   downpayment must be at least 5% of the first $500k plus 10% of any amount above $500k (so $50k on a $750k mortgage)
        #   paymentschedule must be 'weekly', 'biweekly', or 'monthly'
        #   amortizationperiod must be between 5 and 25 years. Expressed as years

        # validate askingPrice and potentially exit early
        try:
            askingPrice = float(params['askingprice'])
        except:
            self.errors.append("askingprice must be a number")
            raise ValueError()

        # validate downPayment
        try:
            downPayment = float(params['downpayment'])
        except:
            self.errors.append("downpayment must be a number")
            downPayment = 0
        else:
            min_down = askingPrice * 0.05
            if askingPrice > 500000:
                min_down += (askingPrice - 500000) * 0.1

            if downPayment < min_down:
                self.errors.append("downpayment too low for askingprice. Must be at least ${}".format(min_down))

        # validate paymentSchedule
        if params['paymentschedule'] not in ('weekly', 'biweekly', 'monthly'):
            self.errors.append("paymentschedule must be one of 'weekly', 'biweekly', or 'monthly'")

        # validate amortizationPeriod
        try:
            amortizationPeriod = float(params['amortizationperiod'])
        except:
            self.errors.append("amortizationperiod must be a number")
            amortizationPeriod = 0
        else:
            if not (5 <= amortizationPeriod <= 25):
                self.errors.append("amortizationperiod must be between 5 and 25 years")

        if self.errors:
            raise ValueError()
        valid_params = {
            'askingprice': askingPrice,
            'downpayment': downPayment,
            'paymentschedule': params['paymentschedule'],
            'amortizationperiod': amortizationPeriod
        }
        return valid_params

    def calculate(self, downpayment, askingprice, paymentschedule, amortizationperiod):
        # Return:
        #   Payment amount per scheduled payment

        down_percent = downpayment / askingprice
        if down_percent < 0.1:
            insurance_rate = 0.0315
        elif down_percent < 0.15:
            insurance_rate = 0.024
        elif down_percent < 0.2:
            insurance_rate = 0.018
        else:
            insurance_rate = 0
        # no insurance for mortgages over 1 million
        if (askingprice - downpayment) > 1e6:
            insurance_rate = 0

        if paymentschedule == 'weekly':
            payments = int(round(amortizationperiod * 52.177457))
            rate_per_period = self.rate_per_year / 52.177457
        elif paymentschedule == 'biweekly':
            payments = int(round(amortizationperiod * 52.177457 / 2))
            rate_per_period = self.rate_per_year / 52.177457 / 2
        else:
            payments = int(round(amortizationperiod * 12))
            rate_per_period = self.rate_per_year / 12

        # payment formula: P = L[c(1 + c)^n]/[(1 + c)^n - 1]
        c = rate_per_period
        L = (askingprice - downpayment) * (1 + insurance_rate)
        n = payments
        payment = L * (c * (1 + c) ** n) / ((1 + c) ** n - 1)
        return payment

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
