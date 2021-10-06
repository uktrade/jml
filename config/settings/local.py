import sys
from .base import *  # noqa

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
    },
    'root': {
        'handlers': ['stdout'],
        'level': os.getenv('ROOT_LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['stdout', ],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
    },
}
