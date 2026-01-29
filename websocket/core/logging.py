import logging
import os
import sys

from pythonjsonlogger import json

from websocket.core.settings import LOG_LEVEL, SERVICE_NAME

PROCESS_ID = os.getpid()


class CustomJsonFormatter(json.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['pid'] = record.process
        log_record['service'] = SERVICE_NAME
        log_record['pid'] = PROCESS_ID

        if 'timestamp' not in log_record:
            log_record['timestamp'] = self.formatTime(record, '%Y-%m-%dT%H:%M:%S.%fZ')


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(LOG_LEVEL)
