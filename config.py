import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    PHONE = os.getenv("PHONE", "")
    CHANNEL_LINK = os.getenv("CHANNEL_LINK", "")
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads")
    MAX_PARALLEL_DOWNLOADS = int(os.getenv("MAX_PARALLEL_DOWNLOADS", 3))

    @classmethod
    def validate(cls):
        if not cls.API_ID or not cls.API_HASH or not cls.PHONE:
            raise ValueError("Preencha API_ID, API_HASH e PHONE no arquivo .env")
        if not cls.CHANNEL_LINK:
            raise ValueError("Preencha CHANNEL_LINK no arquivo .env")
        
        # Cria o diretório de downloads se não existir
        if not os.path.exists(cls.DOWNLOAD_DIR):
            os.makedirs(cls.DOWNLOAD_DIR)
        
        # Cria o diretório de logs
        if not os.path.exists("logs"):
            os.makedirs("logs")
