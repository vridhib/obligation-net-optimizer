from django.db import models
from django.utils.translation import gettext_lazy as _


class Obligation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        NETTED = 'netted', _('Netted')     
        SETTLED = 'settled', _('Settled')
        FAILED = 'failed', _('Failed')

    tx_id = models.UUIDField(primary_key=True)
    payer = models.CharField(max_length=50)
    payee = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    timestamp = models.DateTimeField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    netting_window = models.ForeignKey(
        "NettingWindow", null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        indexes = [
            models.Index(fields=["payer", "payee", "timestamp", "status"])
        ]


class NettingWindow(models.Model):
    window_id = models.AutoField(primary_key=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    gross_obligation_count = models.IntegerField()
    net_obligation_count = models.IntegerField()
    net_volume = models.DecimalField(max_digits=18, decimal_places=2)
    liquidity_saved = models.DecimalField(max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)