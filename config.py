# config.py

class Config:
    IMAP_SERVER = 'imap.your-email.com'
    EMAIL_ACCOUNT = 'your-email@example.com'
    PASSWORD = 'your_password'
    CHECK_INTERVAL = 60  # Интервал проверки почты в секундах

    # Параметры для Scade API
    FLOW_ID = "1607"  # ID флоу
    START_NODE_ID = "SYnn-start"  # ID стартовой ноды
    END_NODE_ID = "y5iI-end"  # ID конечной ноды
    RESULT_NODE_ID = "y5iI-end"  # ID ноды, с которой извлекается результат (обычно совпадает с конечной)
    API_TOKEN = "your_api_token_here"  # Токен для аутентификации API Scade

    @property
    def SCADE_API_URL(self):
        return f'https://api.scade.pro/api/v1/scade/flow/{self.FLOW_ID}/execute'
