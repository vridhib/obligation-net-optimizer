import uuid
from rest_framework import serializers
from obligations.models import Obligation, NettingWindow, NetPosition, SettlementAttempt, ParticipantBalance


class ObligationSerializer(serializers.ModelSerializer):
    tx_id = serializers.UUIDField(default=uuid.uuid4)
    class Meta: 
        model = Obligation
        fields = ['tx_id', 'payer', 'payee', 'amount', 'currency', 'timestamp', 'status', 'netting_window']
        read_only_fields = ['tx_id']


class NetPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetPosition
        fields = ['participant', 'net_amount']


class SettlementAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SettlementAttempt
        fields = ['payer', 'payee', 'amount', 'status']


class NettingWindowSerializer(serializers.ModelSerializer):
    net_positions = NetPositionSerializer(many=True, read_only=True)
    settlement_attempts = SettlementAttemptSerializer(many=True, read_only=True)

    class Meta:
        model = NettingWindow
        fields = ['window_id', 'start_time', 'end_time', 'gross_obligation_count', 'net_obligation_count', 'net_volume', 'liquidity_saved', 'created_at', 'net_positions', 'settlement_attempts']
        read_only_fields = ['window_id', 'created_at']


class ParticipantBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParticipantBalance
        fields = ['participant', 'balance', 'created_at']
        read_only_fields = ['last_updated']