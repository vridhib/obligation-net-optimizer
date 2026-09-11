import pytest
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from streaming.consumers import ObligationConsumer
from streaming.utils import send_snapshot_update


@pytest.mark.asyncio
async def test_obligation_consumer_receives_snapshot():
    # Connect
    communicator = WebsocketCommunicator(ObligationConsumer.as_asgi(), "/ws/obligations/")
    connected, _ =  await communicator.connect()
    assert connected

    # Send snapshot update using channel layer directly 
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "obligations_updates",
        {
            "type": "snapshot_update",
            "data": {"key": "value"}
        }
    )

    # Receive message from WebSocket
    response = await communicator.receive_json_from(timeout=5)
    assert response["key"] == "value"

    # Disconnect
    await communicator.disconnect()