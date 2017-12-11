from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.utils import timezone
from calculator.models import InterestRate


def error_response(errors):
    response_data = {
        'result': 'error',
        'errors': errors
    }
    response = JsonResponse(response_data)
    response.status_code = 400  # Bad Request
    return response


def success_response(operation, parameters, response):
    response_data = {
        'result': 'success',
        'request': operation,
        'request_params': parameters,
        'response': response
    }
    return JsonResponse(response_data)


def payment_amount(request):
    # Methods accepted:
    #   GET
    # Expected parameters:
    #   askingprice: float
    #   downpayment: float
    #   paymentschedule: (weekly | biweekly | monthly),
    #   amortizationperiod: float
    # Validation:
    #   downpayment must be at least 5% of the first $500k plus 10% of any amount above $500k (so $50k on a $750k mortgage)
    #   paymentschedule must be 'weekly', 'biweekly', or 'monthly'
    #   amortizationperiod must be between 5 and 25 years. Expressed as years
    # Return:
    #   Payment amount per scheduled payment

    if request.method != 'GET':
        return HttpResponseNotAllowed(permitted_methods=['GET'])

    # extract variables
    askingPrice = request.GET.get('askingprice', None)
    downPayment = request.GET.get('downpayment', None)
    paymentSchedule = request.GET.get('paymentschedule', '').lower()
    amortizationPeriod = request.GET.get('amortizationperiod', None)

    # required parameters were present
    if askingPrice is None:
        return error_response(["missing parameter 'askingprice'"])
    if downPayment is None:
        return error_response(["missing parameter 'downpayment'"])
    if not paymentSchedule:
        return error_response(["missing parameter 'paymentschedule'"])
    if amortizationPeriod is None:
        return error_response(["missing parameter 'amortizationperiod'"])

    # validation
    try:
        askingPrice = float(askingPrice)
    except:
        return error_response(["askingprice must be a number"])
    try:
        downPayment = float(downPayment)
    except:
        return error_response(["downpayment must be a number"])
    min_down = askingPrice * 0.05
    if askingPrice > 500000:
        min_down += (askingPrice - 500000) * 0.1
    if downPayment < min_down:
        return error_response(["downpayment too low for askingprice. Must be at least ${}".format(min_down)])

    if paymentSchedule not in ('weekly', 'biweekly', 'monthly'):
        return error_response(["paymentschedule must be one of 'weekly', 'biweekly', or 'monthly'"])
    try:
        amortizationPeriod = float(amortizationPeriod)
    except:
        return error_response(["amortizationperiod must be a number"])
    if not (5 <= amortizationPeriod <= 25):
        return error_response(["amortizationperiod must be between 5 and 25 years"])

    # calculation
    down_percent = downPayment / askingPrice
    if down_percent < 0.1:
        insurance_rate = 0.0315
    elif down_percent < 0.15:
        insurance_rate = 0.024
    elif down_percent < 0.2:
        insurance_rate = 0.018
    else:
        insurance_rate = 0
    # no insurance for mortgages over 1 million
    if (askingPrice - downPayment) > 1e6:
        insurance_rate = 0

    now = timezone.now()
    rate_per_year = float(InterestRate.get_rate_at_time(now))
    if paymentSchedule == 'weekly':
        payments = int(round(amortizationPeriod * 52.177457))
        rate_per_period = rate_per_year / 52.177457
    elif paymentSchedule == 'biweekly':
        payments = int(round(amortizationPeriod * 52.177457 / 2))
        rate_per_period = rate_per_year / 52.177457 / 2
    else:
        payments = int(round(amortizationPeriod * 12))
        rate_per_period = rate_per_year / 12

    # payment formula: P = L[c(1 + c)^n]/[(1 + c)^n - 1]
    c = rate_per_period
    L = (askingPrice - downPayment) * (1 + insurance_rate)
    n = payments
    payment = L * (c * (1+c)**n) / ((1+c)**n - 1)

    return success_response('payment_amount', {}, payment)


def mortgage_amount(request):
    # Methods accepted:
    #   GET
    # Expected parameters:
    #   paymentamount: float
    #   downpayment: float (optional),
    #   paymentschedule: (weekly | biweekly | monthly),
    #   amortizationperiod: float
    # Validation:
    #   amortizationperiod must be between 5 and 25 years. Expressed as years.
    #   paymentschedule must be 'weekly', 'biweekly', or 'monthly'
    # Return:
    #   Maximum mortgage that can be taken out
    if request.method != 'GET':
        return HttpResponseNotAllowed(permitted_methods=['GET'])

    # extract variables
    paymentAmount = request.GET.get('paymentamount', None)
    downPayment = request.GET.get('downpayment', '0')
    paymentSchedule = request.GET.get('paymentschedule', '').lower()
    amortizationPeriod = request.GET.get('amortizationperiod', None)

    # required parameters were present
    if paymentAmount is None:
        return error_response(["missing parameter 'paymentamount'"])
    if not paymentSchedule:
        return error_response(["missing parameter 'paymentschedule'"])
    if amortizationPeriod is None:
        return error_response(["missing parameter 'amortizationperiod'"])

    # validation
    try:
        paymentAmount = float(paymentAmount)
    except:
        return error_response(["paymentamount must be a number"])
    try:
        downPayment = float(downPayment)
    except:
        return error_response(["downpayment must be a number"])
    if paymentSchedule not in ('weekly', 'biweekly', 'monthly'):
        return error_response(["paymentschedule must be one of 'weekly', 'biweekly', or 'monthly'"])
    try:
        amortizationPeriod = float(amortizationPeriod)
    except:
        return error_response(["amortizationperiod must be a number"])
    if not (5 <= amortizationPeriod <= 25):
        return error_response(["amortizationperiod must be between 5 and 25 years"])

    #calculation
    now = timezone.now()
    rate_per_year = float(InterestRate.get_rate_at_time(now))
    if paymentSchedule == 'weekly':
        total_payments = int(round(amortizationPeriod * 52.177457))
        rate_per_period = rate_per_year / 52.177457
    elif paymentSchedule == 'biweekly':
        total_payments = int(round(amortizationPeriod * 52.177457 / 2))
        rate_per_period = rate_per_year / 52.177457 / 2
    else:
        total_payments = int(round(amortizationPeriod * 12))
        rate_per_period = rate_per_year / 12

    # payment formula: P = L[c(1 + c)^n]/[(1 + c)^n - 1]
    c = rate_per_period
    n = total_payments
    P = paymentAmount
    L = P * ((1 + c) ** n - 1) / (c * (1 + c) ** n)

    mortgage = L + downPayment

    # or, if we calculate mortgage insurance:
    # mortgage = L / (1 + insurance_rate) + downPayment

    return success_response('mortgage_amount', {}, mortgage)


def interest_rate(request):
    # Methods accepted:
    #   PATCH
    # Expected parameters:
    #   interestrate: string (numbers)
    # Validation:
    #   interestrate must be >= 0
    # Return:
    #   message including old and new interest rates
    if request.method != 'PATCH':
        return HttpResponseNotAllowed(permitted_methods=['PATCH'])

    return HttpResponse("Performing interest rate patch")
