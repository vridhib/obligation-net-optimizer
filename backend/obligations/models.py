import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Obligation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        NETTED = 'netted', _('Netted')     
        SETTLED = 'settled', _('Settled')
        FAILED = 'failed', _('Failed')

    tx_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payer = models.CharField(max_length=50)
    payee = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    timestamp = models.DateTimeField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    netting_window = models.ForeignKey(
        "NettingWindow", 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name="obligations"
    )

    class Meta:
        verbose_name = "obligation"
        verbose_name_plural = "obligations"
        ordering = ["-timestamp", "tx_id"]
        indexes = [
            models.Index(fields=["payer", "payee", "timestamp", "status"])
        ]

    def __str__(self):
        return f"Obl {self.tx_id} | {self.payer} -> {self.payee} {self.amount} {self.currency}"


class NettingWindow(models.Model):
    window_id = models.AutoField(primary_key=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    gross_obligation_count = models.IntegerField()
    net_obligation_count = models.IntegerField()
    gross_volume = models.DecimalField(max_digits=18, decimal_places=2)
    net_volume = models.DecimalField(max_digits=18, decimal_places=2)
    liquidity_saved = models.DecimalField(max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "netting window"
        verbose_name_plural = "netting windows"
        ordering = ["-end_time"]
        indexes = [
            models.Index(fields=["end_time"])
        ]

    def __str__(self):
        return f"Window #{self.window_id} ({self.start_time:%m-%d %H:%M}-{self.end_time:%H:%M})"


class NetPosition(models.Model):
    window = models.ForeignKey(
        NettingWindow, 
        on_delete=models.CASCADE, 
        related_name='net_positions'
    )
    participant = models.CharField(max_length=50)
    net_amount = models.DecimalField(max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "net position"
        verbose_name_plural = "net positions"
        constraints = [
            models.UniqueConstraint(
                fields=["window", "participant"],
                name="unique_window_participant"
            )
        ]

    def __str__(self):
        return f"W{self.window_id} | {self.participant}: {self.net_amount:+}"


class SettlementAttempt(models.Model):
    class Status(models.TextChoices):
        SETTLED = 'settled', _('Settled')
        FAILED = 'failed', _('Failed')

    window = models.ForeignKey(
        NettingWindow, 
        on_delete=models.CASCADE, related_name="settlement_attempts"
    )
    payer = models.CharField(max_length=50)
    payee = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices)
    attempt_number = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "settlement attempt"
        verbose_name_plural = "settlement attempts"

    def __str__(self):
        return f"W{self.window_id} | {self.payer} -> {self.payee} {self.amount} ({self.status})"

    
class ParticipantBalance(models.Model):
    participant = models.CharField(max_length=50, unique=True)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "participant balance"
        verbose_name_plural = "participant balances"
        indexes = [
            models.Index(fields=["participant"])
        ]

    def __str__(self):
        return f"{self.participant} has a balance of {self.balance}."