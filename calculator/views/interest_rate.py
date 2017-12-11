from decimal import Decimal
import json
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.utils import timezone
from calculator.models import InterestRate


def request(request):
    # Methods accepted:
    #   PATCH
    if request.method != 'PATCH':
        return HttpResponseNotAllowed(permitted_methods=['PATCH'])

    now = timezone.now()
    rate_per_year = float(InterestRate.get_rate_at_time(now))
    interest_rate = InterestRateView(rate_per_year)
    return interest_rate.patch(request)


class InterestRateView:
    def __init__(self, interest_rate):
        self.operation = "Interest Rate"
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
        # Return:
        #   message including old and new interest rates
        response_data = {
            'result': 'success',
            'request': self.operation,
            'request_params': self.params,
            'response': {
                'old_rate': self.rate_per_year,
                'new_rate': response
            }
        }
        return JsonResponse(response_data)

    def decode_params(self, request):
        # Expected parameters:
        #   interestrate: string (numbers)
        data = json.loads(request.body.decode('utf-8'))
        if 'interestrate' in data:
            rate = data['interestrate']
        else:
            self.errors.append("missing parameter: 'interestrate'")
            raise ValueError()

        return rate

    def validate(self, raw_rate):
        # Validation:
        #   interestrate must be >= 0
        try:
            rate = round(Decimal(raw_rate), 7)
        except:
            self.errors.append("interestrate must be a number")
            rate = Decimal(0)
        else:
            if rate < 0:
                self.errors.append("interestrate must be positive")
            elif rate >= 10:
                self.errors.append("rate cannot exceed 1000%")

        if self.errors:
            raise ValueError()
        return rate

    def update_model(self, new_rate):
        record = InterestRate(rate=new_rate)
        record.full_clean()
        record.save()
        return str(new_rate)

    def patch(self, request):
        try:
            raw_rate = self.decode_params(request)
            new_rate = self.validate(raw_rate)
            self.params['interestrate'] = str(new_rate)
            result = self.update_model(new_rate)
        except:
            # Log exceptions here
            return self.error_response(self.errors)

        if self.errors:
            return self.error_response(self.errors)
        return self.success_response(result)
