from rest_framework import viewsets, status, filters
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from obligations.models import Obligation, NettingWindow, ParticipantBalance
from .serializers import ObligationSerializer, NettingWindowSerializer, ParticipantBalanceSerializer
from api import services


class ObligationViewSet(viewsets.ModelViewSet):
    queryset = Obligation.objects.all()
    serializer_class = ObligationSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["payer", "payee", "tx_id"]

    @action(detail=False, methods=['post'], url_path='bulk', parser_classes=[MultiPartParser, JSONParser])
    def bulk(self, request):
        if 'file' in request.FILES:
            try:
                result = services.create_obligations_from_csv(request.FILES['file'])
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = request.data
            if not isinstance(data, list):
                return Response({'error': 'JSON body must be a list of obligation objects.'}, status=status.HTTP_400_BAD_REQUEST)
            result = services.create_obligations_from_records(data)

        status_code = status.HTTP_201_CREATED if result['created_count'] else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)
            

class NettingWindowViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NettingWindow.objects.all().order_by('-end_time')
    serializer_class = NettingWindowSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, JSONParser]

    @action(detail=False, methods=['post'], url_path='trigger_netting')
    def trigger_netting(self, request):
        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response({'error': 'CSV file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            task_id = services.enqueue_simulation_from_file(csv_file)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"task_id": task_id, "status": "Netting simulation started."}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["get"], url_path="positions")
    def positions(self, request):
        result = services.get_net_positions_for_window(request.query_params.get("window", "latest"))
        if result is None:
            return Response({"error": "Invalid window identifier."}, status=status.HTTP_404_NOT_FOUND)
        return Response(result)
    
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        return Response(services.get_netting_summary())


class ParticipantBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ParticipantBalance.objects.all().order_by('participant')
    serializer_class = ParticipantBalanceSerializer
    permission_classes = [AllowAny]
