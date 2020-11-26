from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import ModelViewSet


class ViewSet:
    pagination_class = LimitOffsetPagination
    model = None

    def get_queryset(self):
        if hasattr(self.model, 'created_on'):
            return self.model.objects.filter().order_by('-created_on')
        return self.model.objects.filter()


class BaseViewSet(ViewSet, ModelViewSet):
    pass


class AuthenticatedViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
