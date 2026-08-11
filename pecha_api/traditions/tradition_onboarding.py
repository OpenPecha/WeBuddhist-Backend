"""Onboarding page chrome (title/subtitle/footer). Tradition path titles and
descriptions come from ``tradition_metadata`` in the database."""

from typing import Any

from pecha_api.traditions.tradition_constants import DEFAULT_CHAT_LANGUAGE

ONBOARDING_CHROME_BY_LANGUAGE: dict[str, dict[str, str]] = {
    "en": {
        "title": "How do you follow the Buddha?",
        "subtitle": (
            "We'll show you the practices and texts of your path. "
            "You can change this anytime in the app settings."
        ),
        "option_intro": "Through:",
        "footer": "Show me everything Practices and texts from every path",
    },
    "hi": {
        "title": "आप बुद्ध का अनुसरण कैसे करते हैं?",
        "subtitle": (
            "हम आपको आपके मार्ग की प्रथाएं और ग्रंथ दिखाएंगे। "
            "आप इसे ऐप सेटिंग्स में कभी भी बदल सकते हैं।"
        ),
        "option_intro": "इसके माध्यम से:",
        "footer": "मुझे हर मार्ग की सभी प्रथाएं और ग्रंथ दिखाएं",
    },
    "bo": {
        "title": "ཁྱེད་ཀྱིས་སངས་རྒྱས་ཀྱི་རྗེས་སུ་ཇི་ལྟར་འབྲང་ངམ།",
        "subtitle": (
            "ང་ཚོས་ཁྱེད་ལ་འཚམ་པའི་ལམ་གྱི་ཉམས་ལེན་དང་གསུང་རབ་རྣམས་བསྟན་པར་བྱ། "
            "འདེམས་ཁ་འདི་ཉིད་མཉེན་ཆས་ཀྱི་སྒྲིག་བཀོད་ནང་ནས་ག་དུས་ཡིན་ཡང་སྒྱུར་བཅོས་གཏང་ཆོག"
        ),
        "option_intro": "འདི་དག་བརྒྱུད་ནས།",
        "footer": "ང་ལ་བཀའ་བསྟན་གྱི་དབྱེ་བ་མེད་པར་ཉམས་ལེན་དང་གསུང་རབ་ཐམས་ཅད་སྟོན།",
    },
    "mn": {
        "title": "Та Бурхан багшийг хэрхэн дагадаг вэ?",
        "subtitle": (
            "Бид танд өөрийн сонгосон замын дагуух бясалгал, практик болон судар бичгүүдийг харуулах болно. "
            "Та үүнийг аппликейшний тохиргоо хэсгээс хэдийд ч өөрчлөх боломжтой."
        ),
        "option_intro": "Дараах судраар дамжуулан:",
        "footer": "Бүх замын дагуух бүх практик, судар бичгүүдийг харуулах",
    },
    "ne": {
        "title": "तपाईं बुद्धको अनुसरण कसरी गर्नुहुन्छ?",
        "subtitle": (
            "हामी तपाईंलाई तपाईंको मार्गका अभ्यासहरू र ग्रन्थहरू देखाउनेछौं। "
            "तपाईं यसलाई एप सेटिङमा जुनसुकै बेला परिवर्तन गर्न सक्नुहुन्छ।"
        ),
        "option_intro": "यस मार्फत:",
        "footer": "मलाई हरेक मार्गका सबै अभ्यास र ग्रन्थहरू देखाउनुहोस्",
    },
    "zh": {
        "title": "您如何追随佛陀的教导？",
        "subtitle": "我们将为您展示您所选修行路径的实践与经典。您可以随时在应用设置中更改此设置。",
        "option_intro": "通过：",
        "footer": "向我展示所有路径的完整实践与经典",
    },
}


def get_tradition_onboarding_chrome(language: str = DEFAULT_CHAT_LANGUAGE) -> dict[str, Any]:
    normalized_language = (language or DEFAULT_CHAT_LANGUAGE).lower()
    return (
        ONBOARDING_CHROME_BY_LANGUAGE.get(normalized_language)
        or ONBOARDING_CHROME_BY_LANGUAGE[DEFAULT_CHAT_LANGUAGE]
    )
