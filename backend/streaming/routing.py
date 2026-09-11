from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/obligations/', consumers.ObligationConsumer.as_asgi())
]