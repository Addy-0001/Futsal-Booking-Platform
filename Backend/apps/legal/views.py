from rest_framework import mixins, status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.utils import client_ip

from .models import ConsentRecord, Policy
from .serializers import ConsentRecordSerializer, ConsentSerializer, PolicySerializer


class PolicyViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Public, read-only. Lists current policies; retrieve by slug returns the current version."""

    serializer_class = PolicySerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    lookup_value_regex = "[a-z]+"

    def get_queryset(self):
        return Policy.objects.filter(is_current=True)


class ConsentView(APIView):
    """Record a consent. Works for anonymous (cookie banner) and logged-in users."""

    permission_classes = [AllowAny]
    throttle_scope = "anon"

    def post(self, request):
        ser = ConsentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if ser.validated_data.get("policy"):
            policy = get_object_or_404(Policy, pk=ser.validated_data["policy"])
        else:
            policy = get_object_or_404(Policy, slug=ser.validated_data["slug"], is_current=True)

        record = ConsentRecord.objects.create(
            policy=policy,
            user=request.user if request.user.is_authenticated else None,
            ip_address=client_ip(request),
        )
        return Response(ConsentRecordSerializer(record).data, status=status.HTTP_201_CREATED)
