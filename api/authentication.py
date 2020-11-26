from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User


class JWTAuthenticationWithImpersonation(JWTAuthentication):

    def authenticate(self, request):
        user_token = super().authenticate(request)

        if user_token:
            user, token = user_token
            request.real_user = user
            request.is_impersonated = False
            if request.real_user.is_superuser:
                user_id = request.META.get('HTTP_X_FANCONTENT_USER')
                if user_id:
                    user = User.objects.filter(
                        pk=user_id, is_superuser=False).first() or user
                    if user:
                        request.is_impersonated = True
                        user_token = (user, token)

        return user_token
