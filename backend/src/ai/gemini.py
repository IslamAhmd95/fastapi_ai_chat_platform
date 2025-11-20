from google import genai
from .base import AIPlatform


class Gemini(AIPlatform):
    def __init__(self, api_key: str, system_prompt: str = None):
        self.system_prompt = system_prompt
        self.model = "gemini-2.0-flash"
        self.client = genai.Client(api_key=api_key)


    def chat(self, prompt: str) -> str:
        if self.system_prompt:
            prompt = f"{self.system_prompt}\n\n{prompt}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return response.text
