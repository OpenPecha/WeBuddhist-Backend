from enum import Enum


class GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemDirection(str, Enum):
    IN = "in"
    OUT = "out"

    def __str__(self) -> str:
        return str(self.value)
