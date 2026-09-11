import asyncio
import logging
import tiktoken
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from openai import AsyncOpenAI, RateLimitError, BadRequestError
import instructor
from pydantic import BaseModel
from typing import Type, TypeVar

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class LLMOrchestrator:
    """
    Handles Phase III: Multi-Tier LLM Extraction Engine.
    Implements Fallback Chain, 429 Rate Limit backoff, and 413 Chunking prevention.
    """
    def __init__(self, groq_key: str, gemini_key: str, deepseek_key: str):
        # Primary: Groq (Llama 3) - Blazing fast, cheap
        self.client_primary = instructor.from_openai(
            AsyncOpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
        )
        self.primary_model = "llama3-70b-8192"

        # Secondary: Gemini Flash (via OpenAI compatible endpoint or OpenRouter)
        self.client_secondary = instructor.from_openai(
            AsyncOpenAI(api_key=gemini_key, base_url="https://api.openai.com/v1") # Assuming proxy/OpenRouter
        )
        self.secondary_model = "google/gemini-flash-1.5"

        # Tertiary: DeepSeek
        self.client_tertiary = instructor.from_openai(
            AsyncOpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com/v1")
        )
        self.tertiary_model = "deepseek-chat"

        # Tiktoken for payload size calculation
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.MAX_TOKENS = 7500 # Safe buffer below 8k limits

    def _truncate_payload(self, text: str) -> str:
        """Phase III: Intelligent Chunking to prevent 413 Payload Too Large"""
        tokens = self.tokenizer.encode(text)
        if len(tokens) > self.MAX_TOKENS:
            logger.warning(f"Payload too large ({len(tokens)} tokens). Truncating to {self.MAX_TOKENS} tokens.")
            # Truncate and decode back to text (in a real scenario, split by semantic boundaries)
            return self.tokenizer.decode(tokens[:self.MAX_TOKENS])
        return text

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def _call_llm(self, client: AsyncOpenAI, model: str, text: str, schema: Type[T]) -> T:
        """Executes the LLM call with built-in Pydantic validation via Instructor"""
        safe_text = self._truncate_payload(text)
        
        return await client.chat.completions.create(
            model=model,
            response_model=schema,
            messages=[
                {"role": "system", "content": "You are a precise data extraction engine. Extract the entities from the provided text into the exact JSON schema requested. Do not hallucinate."},
                {"role": "user", "content": safe_text}
            ],
            max_retries=0 # We handle retries manually via tenacity
        )

    async def extract_entity(self, text: str, schema: Type[T]) -> T:
        """
        Executes the Multi-Tier Fallback Chain.
        Groq -> Gemini -> DeepSeek
        """
        try:
            logger.info("Attempting extraction with Primary Model (Groq Llama 3)...")
            return await self._call_llm(self.client_primary, self.primary_model, text, schema)
        except Exception as e:
            logger.warning(f"Primary model failed: {str(e)}. Falling back to Secondary (Gemini Flash)...")
            
            try:
                return await self._call_llm(self.client_secondary, self.secondary_model, text, schema)
            except Exception as e2:
                logger.warning(f"Secondary model failed: {str(e2)}. Falling back to Tertiary (DeepSeek)...")
                
                # Final attempt, if this fails, we let the exception raise
                return await self._call_llm(self.client_tertiary, self.tertiary_model, text, schema)

# Example Usage
# async def main():
#     orchestrator = LLMOrchestrator("groq_key", "gemini_key", "deepseek_key")
#     result = await orchestrator.extract_entity("OpenAI raised billions today.", StartupEntity)

