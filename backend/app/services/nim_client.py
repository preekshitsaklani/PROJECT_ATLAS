import os
import logging
from typing import Optional, Tuple
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
logger = logging.getLogger(__name__)

class NIMClient:
    def __init__(self):
        self.api_key = os.getenv("NVIDIA_API_KEY", "")
        self.base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.model = os.getenv("NVIDIA_MODEL", "z-ai/glm5")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=15.0,
                )
            except ImportError:
                logger.warning("openai package not installed")
                return None
        return self._client

    def available(self) -> bool:
        if not self.api_key or self.api_key == "your_nvidia_api_key_here":
            return False
        try:
            import openai
            return True
        except ImportError:
            return False

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.6,
        max_tokens: int = 4096,
    ) -> Tuple[str, str]:
        """
        Streaming completion with chain-of-thought.
        Returns (thinking_trace, final_answer).
        """
        client = self._get_client()
        if client is None:
            raise RuntimeError("NIM client not available")

        thinking_parts = []
        answer_parts = []

        try:
            stream = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                extra_body={
                    "chat_template_kwargs": {
                        "enable_thinking": True,
                        "clear_thinking": False,
                    }
                },
            )

            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    thinking_parts.append(delta.reasoning_content)
                if hasattr(delta, "content") and delta.content:
                    answer_parts.append(delta.content)

            thinking = "".join(thinking_parts)
            answer = "".join(answer_parts)

            logger.info(f"NIM GLM-5 response: {len(thinking)} chars thinking, {len(answer)} chars answer")
            return thinking, answer

        except Exception as e:
            logger.error(f"NIM completion error: {e}")
            raise

    async def complete_simple(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs,
    ) -> str:
        _, answer = await self.complete(system_prompt, user_prompt, **kwargs)
        return answer

nim_client = NIMClient()