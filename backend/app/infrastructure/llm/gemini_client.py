from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from app.infrastructure.llm.embeddings import LLMClientInterface


class GeminiClient(LLMClientInterface):
    """
    Production LLM client wrapping ChatGoogleGenerativeAI (Gemini).
    Why: Generates grounded natural language answers from assembled RAG prompts.
    """
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash") -> None:
        self._llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.2,
        )

    def generate(self, prompt: str) -> str:
        """Invokes the Gemini chat model and returns the text response."""
        response = self._llm.invoke(prompt)
        return response.content


class FakeLLMClient(LLMClientInterface):
    """
    Deterministic fake LLM client for unit test isolation and local sandbox usage.
    Why: Bypasses live API token constraints, returning polished local context.
    """
    CANNED_RESPONSE = """### Diagnostic Engine

**Summary**
The AI Integration engine is running in Local Sandbox Mode as the Google Gemini API key has not been explicitly provisioned.

**Key Insights**
- Essential numerical KPIs and topologies have been successfully assembled into the RAG payload structure.
- The interface is fully operational and is capturing exact variables from the active schema representation.

**Recommendation**
Review the KPI components or update the `.env` configuration file with a valid Gemini key to unlock generative analytical insights.
"""

    def __init__(self) -> None:
        self.last_prompt: Optional[str] = None

    def generate(self, prompt: str) -> str:
        """Records the prompt and returns a canned string."""
        self.last_prompt = prompt
        return self.CANNED_RESPONSE
