import os

SHUTDOWN_TIMEOUT = int(os.getenv('SHUTDOWN_TIMEOUT', 30 * 60))
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 5))
PERIODIC_NOTIFICATION = int(os.getenv('PERIODIC_NOTIFICATION', 10))

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
SERVICE_NAME = os.getenv('SERVICE_NAME', 'ws-notification-service')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')

REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}'
