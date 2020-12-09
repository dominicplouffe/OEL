from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt import views as jwt_views
from django.urls import path

from api.views.ping import (
    PingViewSet, ping_test, ping_summary, ping_details, ping_now
)
from api.views.pong import (
    pongme, PongViewSet
)
from api.views.failure import FailureViewSet, failure_count
from api.views.ping_header import PingHeaderViewSet
from api.views.org_user import (
    OrgUserViewSet, send_invite, check_invite, finish_invite, resend_invite,
    update_user_order, send_notification_update
)
from api.views.org import OrgViewSet
from api.views.auth import (
    get_current_user, get_role, signup_process_one, signup_code_confirmation,
    signup_code_complete, ChangePasswordView
)
from api.views import dashboard

router = DefaultRouter()
router.register(r'ping', PingViewSet, basename='ping')
router.register(r'pong', PongViewSet, basename='pong')
router.register(r'org_user', OrgUserViewSet, basename='org_user')
router.register(r'failure', FailureViewSet, basename='failure')
router.register(r'ping_header', PingHeaderViewSet, basename='ping_header')
router.register(r'org', OrgViewSet, basename='org')

urlpatterns = [
    path(
        'api-token-auth/',
        jwt_views.TokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),
    path(
        'token/refresh/',
        jwt_views.TokenRefreshView.as_view(),
        name='token_refresh'
    ),

    # Auth, Profile and Signup
    path('auth/get-current-user/', get_current_user, name='get-current-user'),
    path('auth/get-role/', get_role, name='get-role'),
    path('auth/signup-start', signup_process_one, name='signup-process-one'),
    path(
        'auth/signup-code',
        signup_code_confirmation,
        name='signup-code-confirmation'
    ),
    path(
        'auth/signup-complete',
        signup_code_complete,
        name='signup-code-complete'),
    path(
        'auth/change-password/<int:id>/',
        ChangePasswordView.as_view(),
        name='change-password'
    ),
    path('auth/send-invite', send_invite, name='send-invite'),
    path('auth/check-invite', check_invite, name='check-invite'),
    path('auth/finish-invite', finish_invite, name='finish-invite'),
    path('auth/resend-invite', resend_invite, name='resend-invite'),

    # Org User
    path(
        'org_user/update_user_order',
        update_user_order,
        name="update-user-order"
    ),
    path(
        'org_user/send_notification_update',
        send_notification_update,
        name='send_notification_update'
    ),

    # Pings
    path('ping-test/<int:id>/', ping_test, name='ping-test'),
    path('ping/summary/', ping_summary, name='ping-summary'),
    path('ping/summary/<int:id>/', ping_summary, name='ping-ind-summary'),
    path('ping/details/<int:id>/', ping_details, name='ping-ind-details'),
    path('ping/now/<int:id>/', ping_now, name='ping-now'),

    # Pongs
    path('pongmae/', pongme, name='pong-me'),

    # Failures and Incicents
    path('failure/counts/<int:ping_id>/', failure_count, name='failure-count'),

    # Dashboard
    path('dashboard', dashboard.index, name="index")
]

urlpatterns.extend(router.urls)
