from groq import Groq
from .base import AIPlatform

class GroqAI(AIPlatform):
    def __init__(self, api_key: str, system_prompt: str = None):
        self.system_prompt = system_prompt
        self.model = "llama-3.3-70b-versatile"
        self.client = Groq(api_key=api_key)

    def chat(self, prompt: str) -> str:
        if self.system_prompt:
            prompt = f"{self.system_prompt}\n\n{prompt}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
