import os

DEFAULTS = dict(
    SITE_LANGUAGE="en",
    SITE_NAME="Pecha",
    ACCESS_TOKEN_EXPIRE_MINUTES=3000000,
    APP_NAME="Pecha Backend",
    AWS_ACCESS_KEY="",
    AWS_SECRET_KEY="",
    AWS_REGION="eu-central-1",
    AWS_BUCKET_NAME="app-pecha-backend",
    AWS_BUCKET_OWNER="",
    BASE_URL="https://webuddhist.com/",
    CLIENT_ID="",
    COMPRESSED_QUALITY=80,
    DATABASE_URL="postgresql://admin:pechaAdmin@localhost:5434/pecha",
    DEFAULT_LANGUAGE="en",
    DEFAULT_PAGE_SIZE=10,
    DEPLOYMENT_MODE="DEBUG",
    DOMAIN_NAME="dev-pecha-esukhai.us.auth0.com",
    IMAGE_EXPIRATION_IN_SEC=3600,
    JWT_ALGORITHM="HS256",
    JWT_AUD="https://pecha.org",
    JWT_ISSUER="https://pecha.org",
    JWT_SECRET_KEY="",
    MAX_FILE_SIZE_MB=1,
    MAX_FILE_SIZE = 5 * 1024 * 1024,
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'},
    MONGO_CONNECTION_STRING="mongodb://admin:pechaAdmin@localhost:27017/pecha?authSource=admin",

    WEBUDDHIST_STUDIO_BASE_URL="https://studio.webuddhist.com",
    MONGO_DATABASE_NAME="pecha",
    REFRESH_TOKEN_EXPIRE_DAYS=30,
    VERSION="0.0.1",
    # Cache Configuration
    CACHE_HOST="localhost",
    CACHE_PORT=6379,
    CACHE_DB=0,
    CACHE_PREFIX="pecha:",
    CACHE_DEFAULT_TIMEOUT=3000000, # 30 seconds in seconds
    CACHE_CONNECTION_STRING="redis://localhost:6379",
    
    # Cache timeout configurations for different types (in seconds)
    CACHE_TEXT_TIMEOUT=1800,        # 30 minutes for texts (not frequently changed)
    CACHE_COLLECTION_TIMEOUT=1800,  # 30 minutes for collections (not frequently changed)
    CACHE_USER_TIMEOUT=900,         # 15 minutes for users (not frequently changed)
    CACHE_TOPIC_TIMEOUT=1800,       # 30 minutes for topics (not frequently changed)
    CACHE_SHEET_TIMEOUT=60,         # 1 minute for sheets (frequently edited by users)

    SHORT_URL_GENERATION_ENDPOINT="https://pech.as/api/v1",
    
    # External Multilingual Search API Configuration
    EXTERNAL_SEARCH_API_URL="https://pecha-backend-dev.web.app/",  # Change this to your actual external API URL

    PECHA_BACKEND_ENDPOINT="http://127.0.0.1:8000/api/v1",

    # Search configuration
    ELASTICSEARCH_URL= None,
    ELASTICSEARCH_API=None,
    ELASTICSEARCH_CONTENT_INDEX = "pecha-texts",
    ELASTICSEARCH_SEGMENT_INDEX = "pecha-segments",
    ELASTICSEARCH_SHEET_INDEX = "pecha-sheets",

    MAILTRAP_API_KEY = "",
    SENDER_EMAIL="",
    SENDER_NAME="",

    OPENPECHA_SEARCH_API_URL="",

    ### text uploader script configuration
    APPLICATION = "webuddhist",
    ACCESS_TOKEN="",
    COLLECTION_LANGUAGES = ["bo", "en", "zh"],

    #pecha api configuration
    EXTERNAL_PECHA_API_URL="",

    SQS_TIMEOUT=1800,


)


def get(key: str) -> str:
    if key in os.environ:
        return os.environ[key]
    else:
        return str(DEFAULTS[key])


def get_float(key: str) -> float:
    try:
        return float(get(key))
    except (TypeError, ValueError) as e:
        raise ValueError(f"Could not convert the value for key '{key}' to float: {e}")


def get_int(key: str) -> int:
    try:
        return int(get(key))
    except (TypeError, ValueError) as e:
        raise ValueError(f"Could not convert the value for key '{key}' to int: {e}")
