from enum import Enum


class AIModels(str, Enum):
    GROQ = "groq"
    GEMINI = "gemini"
    OPENAI = "openai"


PROVIDER_AVAILABILITY = {
    AIModels.GROQ: True,
    AIModels.GEMINI: False,
    AIModels.OPENAI: False,
}


def is_provider_available(model_name: AIModels) -> bool:
    return PROVIDER_AVAILABILITY.get(model_name, False)
