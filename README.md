# Mortgage Calculator

Written in:
 * Python3
 * Powered by Django
 * Persistant storage in SQLite (by default)

Code locations:
* calculation logic for each endpoint is in `/calculator/views/*`
* routing is done in `/calculator/urls.py`
* tests are in `/calculator/tests.py`

Decisions and Assumptions:
* Number of payments is rounded to the nearest whole number
* Insurance is applied on the asking price AFTER subtracting the down payment.
* Natural rate of 52.177457 weeks per year
* Since downpayment is an optional field for mortgage amount:
    * The minimum down payment requirement is not considered.
    * Mortgage insurance can not be accurately calculated and is ignored.
