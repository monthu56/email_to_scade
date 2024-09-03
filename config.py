# config.py

class Config:
    IMAP_SERVER = 'imap.yandex.ru'
    EMAIL_ACCOUNT = '**********@yandex.ru'
    PASSWORD = '*************'
    CHECK_INTERVAL = 60  # Интервал проверки почты в секундах

    # Параметры для Scade API
    FLOW_ID = "34096"  # ID флоу
    START_NODE_ID = "axi1-start"  # ID стартовой ноды
    END_NODE_ID = "AQ6K-end"  # ID конечной ноды
    RESULT_NODE_ID = "AQ6K-end"  # ID ноды, с которой извлекается результат (обычно совпадает с конечной)
    API_TOKEN = "******************"  # Токен для аутентификации API Scade

    SCADE_API_URL = f'https://api.scade.pro/api/v1/scade/flow/34096/execute'
