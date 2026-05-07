from enum import Enum


class GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemType(str, Enum):
    COMMENTARY_OF = "COMMENTARY_OF"
    TRANSLATION_OF = "TRANSLATION_OF"

    def __str__(self) -> str:
        return str(self.value)
