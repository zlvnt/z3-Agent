"""
Unified Query Processor for z3-Agent

Combines routing, context resolution, reformulation, and escalation check
into a single LLM call for efficiency.

Phase 1 Implementation - RAG Orchestration v2
"""

import json
from typing import Dict, Any, Optional
from functools import lru_cache
from pathlib import Path

from google import genai
from google.genai import types


class UnifiedProcessor:
    """
    Unified agent that handles:
    1. Routing decision (direct/docs)
    2. Query reformulation (optimize for retrieval)
    3. Escalation check (needs human?)

    All in a single LLM call for efficiency.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str,
        temperature: float,
        prompt_template_path: Optional[str] = None
    ):
        """
        Initialize unified processor.

        Args:
            api_key: Gemini API key
            model_name: Gemini model name
            temperature: LLM temperature (0-1, lower = more consistent)
            prompt_template_path: Path to prompt template file
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature

        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)

        # Generation config for JSON output
        self.generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=self.temperature,
        )

        # Load prompt template
        if prompt_template_path:
            self.prompt_template = self._load_prompt_template(prompt_template_path)
        else:
            self.prompt_template = self._get_default_prompt()

    def _load_prompt_template(self, template_path: str) -> str:
        """Load prompt template from file."""
        path = Path(template_path)
        if not path.exists():
            # Try relative to project root
            path = Path(__file__).parent.parent.parent / template_path

        if not path.exists():
            print(f"WARNING: Prompt template not found: {template_path}, using default")
            return self._get_default_prompt()

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _get_default_prompt(self) -> str:
        """Default prompt template (fallback)."""
        return """Kamu adalah Query Processor untuk z3, AI Customer Service TokoLapak (e-commerce Indonesia).

=== TUJUANMU ===
Analisis query user dan tentukan strategi respons:
- routing="direct" → langsung generate respons tanpa cari referensi
- routing="docs" → cari informasi di knowledge base dulu
- escalate=true → teruskan ke CS manusia

=== INPUT ===
Query: {query}
History: {history}

=== ANALISIS (3 STEP) ===

STEP 1 - ROUTING:
Tentukan routing berdasarkan intent user (gunakan history jika relevan).
- "direct": greeting, acknowledgment, terima kasih, chitchat ringan
- "docs": pertanyaan produk, kebijakan, prosedur, return/refund, garansi, komplain

STEP 2 - REFORMULATION (jika routing="docs"):
Optimalkan query untuk pencarian knowledge base.

STEP 3 - ESCALATION CHECK:
Escalate=true jika user minta CS/manusia, komplain serius, atau di luar kapabilitas bot.

=== OUTPUT FORMAT (JSON ONLY) ===
{{
  "routing_decision": "direct|docs",
  "resolved_query": "intent user yang dipahami",
  "reformulated_query": "query optimal untuk search",
  "escalate": true|false,
  "escalation_reason": "alasan jika escalate",
  "reasoning": "penjelasan singkat"
}}

=== CONTOH ===

Query: "iya" | History: "Bot: Mau tahu prosedur return?"
{{"routing_decision": "docs", "resolved_query": "prosedur return", "reformulated_query": "prosedur pengembalian barang", "escalate": false, "escalation_reason": "", "reasoning": "User konfirmasi tanya return"}}

Query: "halo" | History: ""
{{"routing_decision": "direct", "resolved_query": "sapaan", "reformulated_query": "sapaan", "escalate": false, "escalation_reason": "", "reasoning": "Greeting sederhana"}}

=== PROSES SEKARANG ==="""

    def process(self, query: str, history: str = "") -> Dict[str, Any]:
        """
        Process query through unified pipeline.

        Args:
            query: User query/message
            history: Conversation history context

        Returns:
            Dictionary with:
            - routing_decision: str
            - resolved_query: str
            - needs_reformulation: bool
            - reformulated_query: str
            - escalate: bool
            - escalation_reason: str
            - reasoning: str
        """
        # Format prompt
        prompt = self.prompt_template.format(
            query=query,
            history=history or "Tidak ada history percakapan sebelumnya"
        )

        try:
            # Call LLM (single call for all decisions)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.generation_config
            )

            # Parse JSON response
            result = json.loads(response.text)

            # Validate required fields
            required_fields = [
                "routing_decision",
                "resolved_query",
                "reformulated_query",
                "escalate",
                "reasoning"
            ]

            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            # Infer needs_reformulation if not provided (for backward compatibility)
            if "needs_reformulation" not in result:
                result["needs_reformulation"] = result["reformulated_query"] != result["resolved_query"]

            # Ensure escalation_reason exists
            if "escalation_reason" not in result:
                result["escalation_reason"] = ""


            return result

        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON response: {e}")
            print(f"Response text: {response.text}")
            return self._fallback_response(query)

        except Exception as e:
            print(f"ERROR: UnifiedProcessor failed: {e}")
            return self._fallback_response(query)

    def _fallback_response(self, query: str) -> Dict[str, Any]:
        """Fallback response when processing fails."""
        return {
            "routing_decision": "docs",  # Safe default: try RAG
            "resolved_query": query,
            "needs_reformulation": False,
            "reformulated_query": query,
            "escalate": False,
            "escalation_reason": "",
            "reasoning": "Fallback response due to processing error"
        }


# Singleton instance
@lru_cache(maxsize=1)
def _get_unified_processor() -> UnifiedProcessor:
    """Get singleton UnifiedProcessor instance."""
    from app.config import settings
    from app.core.rag_config import load_rag_config

    prompt_path = None
    temperature = 0.3  # fallback

    try:
        rag_config = load_rag_config("default")
        prompt_path = getattr(rag_config, 'unified_processor_prompt_path', None)
        temperature = getattr(rag_config, 'unified_processor_temperature', 0.3)
    except Exception as e:
        print(f"WARNING: Could not load RAG config for processor: {e}")

    return UnifiedProcessor(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.MODEL_NAME,
        temperature=temperature,
        prompt_template_path=prompt_path
    )


def process_query(query: str, history: str = "") -> Dict[str, Any]:
    """
    Convenience function to process query using singleton processor.

    Args:
        query: User query/message
        history: Conversation history context

    Returns:
        Processing result dictionary
    """
    processor = _get_unified_processor()
    return processor.process(query, history)
