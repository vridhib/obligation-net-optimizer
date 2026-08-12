from rest_framework import viewsets, status
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from django.core.files.storage import default_storage
from obligations.models import Obligation, NettingWindow, ParticipantBalance
from .serializers import ObligationSerializer, NettingWindowSerializer, ParticipantBalanceSerializer
from streaming.tasks import run_simulation_task


class ObligationViewSet(viewsets.ModelViewSet):
    queryset = Obligation.objects.all()
    serializer_class = ObligationSerializer
    permission_classes = [AllowAny]


class NettingWindowViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NettingWindow.objects.all().order_by('-end_time')
    serializer_class = NettingWindowSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, JSONParser]

    # Expects CSV file in request (multipart form-data) or path
    @action(detail=False, methods=['post'])
    def trigger_netting(self, request):
        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response({'error': 'CSV file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Temporarily save file
        path = default_storage.save(f'tmp/{csv_file.name}', csv_file)
        full_path = default_storage.path(path)

        # Dispatch Celery task
        task = run_simulation_task.delay(full_path)
        return Response({
            'task_id': task.id,
            'status': 'Netting simulation started.'
        }, status=status.HTTP_202_ACCEPTED)


class ParticipantBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParticipantBalance.objects.all()
    serializer_class = ParticipantBalanceSerializer
    permission_classes = [AllowAny]
