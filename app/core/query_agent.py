"""
Query Analysis & Reformulation Agent for z3-Agent

Analyzes user queries and reformulates when needed for better retrieval.
Based on agentic-rag research (exp_a1 - 78.6% quality improvement)
"""

import json
from typing import Dict, Any
from functools import lru_cache
from pathlib import Path


class QueryAgent:
    """
    Agent untuk analisis query dan reformulation.

    Capabilities:
    - Analyze: Apakah query perlu retrieval?
    - Reformulate: Transform query untuk retrieval optimal (jika perlu)
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",  # Default fallback (singleton uses settings.MODEL_NAME)
        prompt_template_path: str = None,
        temperature: float = 0.3
    ):
        """
        Initialize query agent.

        Args:
            api_key: Gemini API key
            model_name: Gemini model name
            prompt_template_path: Path to prompt template file
            temperature: LLM temperature (0-1, lower = more consistent)
        """
        from google import genai
        from google.genai import types

        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature

        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)

        # Generation config
        self.generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=self.temperature,
        )

        # Load prompt template
        if prompt_template_path:
            self.prompt_template = self._load_prompt_template(prompt_template_path)
        else:
            # Use default inline prompt if no file specified
            self.prompt_template = self._get_default_prompt()

    def _load_prompt_template(self, template_path: str) -> str:
        """Load prompt template from file."""
        path = Path(template_path)
        if not path.exists():
            # Try relative to project root
            path = Path(__file__).parent.parent.parent / template_path

        if not path.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {template_path}\n"
                f"Searched: {path}"
            )

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _get_default_prompt(self) -> str:
        """Default prompt template (inline)."""
        return """Kamu adalah agent analisis untuk sistem RAG (Retrieval-Augmented Generation) pada domain e-commerce Indonesia.

TUGAS KAMU:
1. Analisis apakah query user memerlukan pencarian informasi dari knowledge base atau tidak
2. Jika perlu retrieve, reformulate query agar lebih optimal untuk pencarian (jika diperlukan)

CONTEXT:
- Knowledge base berisi: kebijakan toko (return, refund, garansi), FAQ, info produk, prosedur customer service
- Query yang PERLU retrieval: pertanyaan tentang kebijakan, cara order/return, info produk, prosedur toko
- Query yang TIDAK PERLU retrieval: greeting (halo, terima kasih), chitchat, pertanyaan umum di luar e-commerce (cuaca, matematika, dll)

QUERY USER:
{query}

OUTPUT FORMAT (JSON):
{{
  "need_retrieval": true/false,
  "query_type": "support_query" | "greeting" | "chitchat" | "out_of_scope",
  "reasoning": "Penjelasan singkat (maks 20 kata)",
  "needs_reformulation": true/false,
  "reformulated_query": "hasil reformulate atau query original",
  "reformulation_reasoning": "Penjelasan singkat (maks 20 kata)"
}}

ATURAN:
- Output HANYA JSON tanpa teks lain
- Reasoning dalam Bahasa Indonesia, maksimal 20 kata
- Jika need_retrieval = false: needs_reformulation = false, reformulated_query = query original
- Reformulation criteria (hanya jika need_retrieval = true):
  * Ganti slang/informal → formal (gimana→bagaimana, gak→tidak, dong→mohon)
  * Expand implicit → explicit (kekecilan→ukuran tidak sesuai)
  * Jangan ubah intent atau tambah informasi baru

CONTOH:

Query: "Saya beli kemeja kekecilan, gimana dong?"
{{
  "need_retrieval": true,
  "query_type": "support_query",
  "reasoning": "User ingin return karena ukuran tidak sesuai",
  "needs_reformulation": true,
  "reformulated_query": "Bagaimana prosedur pengembalian barang yang tidak sesuai ukuran?",
  "reformulation_reasoning": "Ubah slang ke formal dan perjelas intent return"
}}

Analisis query user dan output JSON."""

    def analyze_and_reformulate(self, query: str) -> Dict[str, Any]:
        """
        Analyze query dan reformulate jika perlu (one-shot).

        Args:
            query: User query

        Returns:
            Dictionary dengan:
            - need_retrieval: bool
            - query_type: str
            - reasoning: str
            - needs_reformulation: bool
            - reformulated_query: str
            - reformulation_reasoning: str
        """
        # Format prompt dengan query
        prompt = self.prompt_template.format(query=query)

        try:
            # Call LLM (one-shot)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.generation_config
            )

            # Parse JSON response
            result = json.loads(response.text)

            # Validate required fields
            required_fields = [
                "need_retrieval",
                "query_type",
                "reasoning",
                "needs_reformulation",
                "reformulated_query",
                "reformulation_reasoning"
            ]

            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            return result

        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON response: {e}")
            print(f"Response text: {response.text}")
            # Fallback: no reformulation
            return {
                "need_retrieval": True,
                "query_type": "support_query",
                "reasoning": "JSON parse error, using original query",
                "needs_reformulation": False,
                "reformulated_query": query,
                "reformulation_reasoning": "Fallback to original query"
            }
        except Exception as e:
            print(f"ERROR: Agent analysis failed: {e}")
            # Fallback: no reformulation
            return {
                "need_retrieval": True,
                "query_type": "support_query",
                "reasoning": "Agent error, using original query",
                "needs_reformulation": False,
                "reformulated_query": query,
                "reformulation_reasoning": "Fallback to original query"
            }


@lru_cache(maxsize=1)
def _get_query_agent():
    """Get singleton query agent instance."""
    from app.config import settings
    from app.core.rag_config import load_rag_config

    try:
        rag_config = load_rag_config("default")
        use_agent = getattr(rag_config, 'use_query_agent', False)

        if not use_agent:
            return None

        # Get prompt path if specified
        prompt_path = getattr(rag_config, 'query_agent_prompt_path', None)

        return QueryAgent(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.MODEL_NAME,
            prompt_template_path=prompt_path,
            temperature=0.3
        )
    except Exception as e:
        print(f"WARNING: Could not initialize query agent: {e}")
        return None


def analyze_query(query: str) -> Dict[str, Any]:
    """
    Convenience function to analyze query using singleton agent.

    Args:
        query: User query

    Returns:
        Analysis result or None if agent disabled
    """
    agent = _get_query_agent()
    if agent is None:
        # Agent disabled, return passthrough
        return {
            "need_retrieval": True,
            "query_type": "support_query",
            "reasoning": "Query agent disabled",
            "needs_reformulation": False,
            "reformulated_query": query,
            "reformulation_reasoning": "Agent disabled, passthrough"
        }

    return agent.analyze_and_reformulate(query)
