import enum


class MessageType(str, enum.Enum):
    notification = 'notification'
    welcome = 'welcome'
    shutdown_notice = 'shutdown_notice'
    echo = 'echo'
