from django.http import HttpResponse, HttpResponseNotFound


def payment_amount(request):
    if request.method != 'GET':
        return HttpResponseNotFound()

    return HttpResponse("No content")


def mortgage_amount(request):
    if request.method != 'GET':
        return HttpResponseNotFound()

    return HttpResponse("No content")


def interest_rate(request):
    if request.method != 'PATCH':
        return HttpResponseNotFound()

    return HttpResponse("No content")
