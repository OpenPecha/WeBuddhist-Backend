from pathlib import Path

ORDER_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_RECITATION_LANGUAGE = "en"
SUPPORTED_RECITATION_LANGUAGES = frozenset({"bo", "en"})

RECITATION_ORDER_PATHS = {
    "bo": ORDER_DIRECTORY / "order_recitations_bo.json",
    "en": ORDER_DIRECTORY / "order_recitations_en.json",
}
