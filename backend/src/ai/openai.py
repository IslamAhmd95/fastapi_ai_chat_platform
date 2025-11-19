from fastapi import HTTPException, status
from openai import OpenAI as open_ai
from .base import AIPlatform


class OpenAI(AIPlatform):
    def __init__(self, api_key: str, system_prompt: str = None):
        self.system_prompt = system_prompt
        self.model = "gpt-5-nano"
        self.client = open_ai(
            api_key=api_key
        )


    def chat(self, prompt: str) -> str:
        if self.system_prompt:
            prompt = f"{self.system_prompt}\n\n{prompt}"

        response = self.client.responses.create(
                model=self.model,
                input=prompt
            )

        return response.output_text