from pathlib import Path
from uuid import UUID

TRADITION_TAXONOMY_PATH = Path(__file__).resolve().parent / "Buddhist Traditions Taxonomy - i18n-v1.1.json"
TRADITION_ONBOARDING_PATH = Path(__file__).resolve().parent / "tradition.json"
TRADITION_ID_NAMESPACE = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
DEFAULT_LLM_MODEL = "gemini-2.5-flash-lite"
DEFAULT_CHAT_LANGUAGE = "en"
