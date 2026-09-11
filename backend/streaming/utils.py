from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_snapshot_update(data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "obligations_updates",
        {"type": "snapshot_update", "data": data}
    )