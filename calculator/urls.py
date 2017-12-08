from django.urls import path

from calculator import views

app_name = 'property'

urlpatterns = [
    path('payment-amount', views.model1, name='payment amount'),
    path('mortgage-amount', views.model2, name='mortgage amount'),
    path('interest-rate', views.model3, name='interest rate'),
]