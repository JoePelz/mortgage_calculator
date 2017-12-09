from django.http import HttpResponse, HttpResponseNotFound


def payment_amount(request):
    if request.method != 'GET':
        return HttpResponseNotFound()

    return HttpResponse("Performing payment amount calculation")


def mortgage_amount(request):
    if request.method != 'GET':
        return HttpResponseNotFound()

    return HttpResponse("Performing mortgage amount calculation")


def interest_rate(request):
    if request.method != 'PATCH':
        return HttpResponseNotFound()

    return HttpResponse("Performing interest rate patch")
