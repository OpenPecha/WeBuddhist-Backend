from pathlib import Path
from uuid import UUID, uuid5

TRADITION_ONBOARDING_PATH = Path(__file__).resolve().parent / "tradition.json"
TRADITION_ID_NAMESPACE = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
DEFAULT_CHAT_LANGUAGE = "en"


def tradition_id_from_code(code: str) -> UUID:
    return uuid5(TRADITION_ID_NAMESPACE, code)
