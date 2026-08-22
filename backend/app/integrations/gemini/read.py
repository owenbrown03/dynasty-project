from .transport import GeminiTransport


class GeminiRead:
    def __init__(self, transport: GeminiTransport):
        self.transport = transport

    async def generate_text(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        generation_config: dict | None = None,
    ) -> str:
        response = await self.transport.generate_content(
            contents=[
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            system_instruction=system_instruction,
            generation_config=generation_config,
        )

        return response.text
