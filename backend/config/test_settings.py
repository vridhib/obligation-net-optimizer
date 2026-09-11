from .settings import *   # noqa


CHANNEL_LAYERS = {
    'default': {
        "BACKEND": 'channels.layers.InMemoryChannelLayer'
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True