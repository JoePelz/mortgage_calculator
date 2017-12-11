from django.urls import path

from calculator.views import payment_amount, mortgage_amount, interest_rate

app_name = 'calculator'

urlpatterns = [
    path('payment-amount', payment_amount.request, name='payment amount'),
    path('mortgage-amount', mortgage_amount.request, name='mortgage amount'),
    path('interest-rate', interest_rate.request, name='interest rate'),
]