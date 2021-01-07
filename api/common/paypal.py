import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oel.settings")  # noqa
django.setup()  # noqa

import requests
from django.conf import settings
from api.models import Product, Plan


def session():
    resp = requests.post(
        f'{settings.PAYPAL_API}/v1/oauth2/token',
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        data={'grant_type': 'client_credentials'}
    )
    resp = resp.json()
    access_token = resp['access_token']

    def paypal_api(method, path, data=None, request_id=None):
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        if request_id:
            headers['PayPal-Request-Id'] = request_id
        resp = getattr(requests, method)(
            f'{settings.PAYPAL_API}{path}',
            headers=headers,
            json=data
        )
        status_code = resp.status_code
        if resp.ok:
            return status_code, resp.json()
        raise Exception(
            f'Unexpected status code: STATUS_CODE: {status_code}, RESPONSE: {resp.json()}')

    return paypal_api


def setup_product():
    paypal_api = session()
    status_code, resp = paypal_api('post', '/v1/catalogs/products', {
        "name": "On Error Log",
        "description": "Software Monitoriing Service",
        "type": "SERVICE",
        "category": "SOFTWARE",
        "image_url": "https://example.com/streaming.jpg",
        "home_url": "https://example.com/home"
    }, request_id='create_product_onerrorlog')
    product_id = resp['id']
    product, _ = Product.objects.get_or_create(name='onerrorlog')
    product.display = 'On Error Log'
    product.paypal_product_id = product_id
    product.save()
    print(f'product_id: {product_id}')

    status_code, resp = paypal_api('post', '/v1/billing/plans', {
        "product_id": product_id,
        "name": "Basic Plan",
        "description": "Basic plan",
        "billing_cycles": [
            {
                "frequency": {
                    "interval_unit": "MONTH",
                    "interval_count": 1
                },
                "tenure_type": "TRIAL",
                "sequence": 1,
                "total_cycles": 1
            },
            {
                "frequency": {
                    "interval_unit": "MONTH",
                    "interval_count": 1
                },
                "tenure_type": "REGULAR",
                "sequence": 2,
                "total_cycles": 12,
                "pricing_scheme": {
                    "fixed_price": {
                        "value": "5",
                        "currency_code": "USD"
                    }
                }
            }
        ],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "setup_fee": {
                "value": "0",
                "currency_code": "USD"
            },
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3
        },
        "taxes": {
            "percentage": "0",
            "inclusive": True
        }
    }, request_id='create_plan_onerrorlog_basic')
    plan, _ = Plan.objects.get_or_create(name='basic', product=product)
    plan.display = 'Basic'
    plan.paypal_plan_id = resp["id"]
    plan.save()
    print(f'plan_id: {resp["id"]}')


if __name__ == "__main__":
    setup_product()
