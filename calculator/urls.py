from django.urls import path

from calculator import views

app_name = 'calculator'

urlpatterns = [
    path('payment-amount', views.payment_amount, name='payment amount'),
    path('mortgage-amount', views.mortgage_amount, name='mortgage amount'),
    path('interest-rate', views.interest_rate, name='interest rate'),
]