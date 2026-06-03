from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MODEL_NAME: str = "google/flan-t5-large"
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024
    LOG_LEVEL: str = "INFO"
    PARSER_VERSION: str = "1.0.0"
    LIBREOFFICE_PATH: str = "libreoffice"
    RATE_LIMIT: str = "10/minute"

    model_config = ConfigDict(env_file=".env", case_sensitive=True)
