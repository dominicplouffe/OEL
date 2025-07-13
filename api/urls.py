from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt import views as jwt_views
from django.urls import path

from api.views.ping import (
    PingViewSet,
    ping_details,
    ping_now,
    fix,
    acknowledge,
    ignore,
    ping_test2,
)
from api.views.pong import (
    pongme,
    PongViewSet,
    pong_details,
    validate_cron,
    process_pong_now,
)
from api.views.failure import FailureViewSet, failure_count
from api.views.ping_header import PingHeaderViewSet
from api.views.metric_condition import MetricConditionViewSet, metric_condition_details
from api.views.org_user import (
    OrgUserViewSet,
    send_invite,
    check_invite,
    finish_invite,
    resend_invite,
    update_user_order,
    send_notification_update,
    get_on_call_user,
)
from api.views.org import OrgViewSet
from api.views.auth import (
    get_current_user,
    get_role,
    signup_process_one,
    signup_code_confirmation,
    signup_code_complete,
    ChangePasswordView,
)
from api.views import dashboard
from api.views import metrics
from api.views import summary
from api.views.vital_instance import VitalInstancegViewSet
from api.views.schedule import ScheduleOverrideViewSet

router = DefaultRouter()
router.register(r"ping", PingViewSet, basename="ping")
router.register(r"pong", PongViewSet, basename="pong")
router.register(r"org_user", OrgUserViewSet, basename="org_user")
router.register(r"failure", FailureViewSet, basename="failure")
router.register(r"ping_header", PingHeaderViewSet, basename="ping_header")
router.register(r"org", OrgViewSet, basename="org")
router.register(
    r"schedule_override", ScheduleOverrideViewSet, basename="schedule_override"
)

router.register(
    r"metric_condition", MetricConditionViewSet, basename="metric_condition"
)
router.register(r"vital_instance", VitalInstancegViewSet, basename="vital_instance")

urlpatterns = [
    path(
        "api-token-auth/",
        jwt_views.TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path("token/refresh/", jwt_views.TokenRefreshView.as_view(), name="token_refresh"),
    # Auth, Profile and Signup
    path("auth/get-current-user/", get_current_user, name="get-current-user"),
    path("auth/get-role/", get_role, name="get-role"),
    path("auth/signup-start", signup_process_one, name="signup-process-one"),
    path("auth/signup-code", signup_code_confirmation, name="signup-code-confirmation"),
    path("auth/signup-complete", signup_code_complete, name="signup-code-complete"),
    path(
        "auth/change-password/<int:id>/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
    path("auth/send-invite", send_invite, name="send-invite"),
    path("auth/check-invite", check_invite, name="check-invite"),
    path("auth/finish-invite", finish_invite, name="finish-invite"),
    path("auth/resend-invite", resend_invite, name="resend-invite"),
    # Org User
    path("org_user/update_user_order", update_user_order, name="update-user-order"),
    path(
        "org_user/send_notification_update",
        send_notification_update,
        name="send_notification_update",
    ),
    path("org_user/get_on_call_user", get_on_call_user, name="get_on_call_user"),
    # Pings
    path("ping-test/", ping_test2, name="ping-test2"),
    path("ping/details/<int:id>/", ping_details, name="ping-ind-details"),
    path("ping/now/<int:id>/", ping_now, name="ping-now"),
    # Pongs
    path("pongme/<pos>/<push_key>", pongme, name="pong-me"),
    path("pong/details/<int:id>/", pong_details, name="pong-ind-details"),
    path("pong/cron_check/", validate_cron, name="pong-check"),
    path("pong/now/<int:id>/", process_pong_now, name="process_pong_now"),
    # Metics
    path("metrics/tags/<tag_name>", metrics.get_metric_values, name="get-tags-by-name"),
    path("metrics/tags", metrics.get_metrics_tags, name="get-tags"),
    path("metrics", metrics.add_metrics, name="add-metrics"),
    path("metrics-sample", metrics.metric_sample, name="metric-sample"),
    path(
        "metric_condition/details/<int:id>/",
        metric_condition_details,
        name="metric_condition-details",
    ),
    # Confirmation
    path("ping/acknowledge/<int:id>/", acknowledge, name="acknowledge"),
    path("ping/fix/<int:id>/", fix, name="fix"),
    path("ping/ignore/<int:id>/", ignore, name="ignore"),
    # Failures and Incicents
    path("failure/counts/<int:alert_id>/", failure_count, name="failure-count"),
    # Summary
    path("alert_summary/<str:object>/", summary.summarizer, name="alert-summary"),
    path(
        "alert_summary/<str:object>/<int:id>/",
        summary.summarizer,
        name="alert-summary-details",
    ),
    # Dashboard
    path("dashboard", dashboard.index, name="index"),
]

urlpatterns.extend(router.urls)
