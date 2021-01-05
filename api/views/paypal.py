from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.common.paypal import session, PRODUCTS
from rest_framework import status
from api.models import Subscription
from django.db import transaction


ONERRORLOG = PRODUCTS['onerrorlog']


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subscription(request):
    org_user = request.org_user
    org = org_user.org
    subscription_info = request.data

    if 'id' not in subscription_info:
        return Response(
            'Payload missing required field: id',
            status=status.HTTP_400_BAD_REQUEST
        )

    subscription_id = subscription_info['id']

    if 'product' not in subscription_info:
        return Response(
            'Payload missing required field: product',
            status=status.HTTP_400_BAD_REQUEST
        )

    product_name = subscription_info['product']

    if product_name not in PRODUCTS:
        return Response(
            'Incorrect value for field: product',
            status=status.HTTP_400_BAD_REQUEST
        )

    product = PRODUCTS[product_name]

    if 'plan' not in subscription_info:
        return Response(
            'Payload missing required field: plan',
            status=status.HTTP_400_BAD_REQUEST
        )

    plan_name = subscription_info['plan']

    if plan_name not in product['plans']:
        return Response(
            'Incorrect value for field: plan',
            status=status.HTTP_400_BAD_REQUEST
        )
    plan = product['plans'][plan_name]

    with transaction.atomic():
        paypal_api = session()
        _, paypal_subscription = paypal_api(
            'get',
            f'/v1/billing/subscriptions/{subscription_id}',
        )
        # TODO verify plan matches what was sent
        subscription = Subscription.objects.create(
            org=org, product=product_name, plan=plan_name,
            paypal_product_id=product['paypal_id'],
            paypal_plan_id=plan['paypal_id'],
            paypal_subscription_id=subscription_id,
            status='active'
        )
        subscription.save()
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)
