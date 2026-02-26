"""
Web search service using DuckDuckGo.

Provides web search capabilities for the RAG pipeline
when document retrieval is insufficient.
"""

from typing import List, Dict


def web_search(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Search the web using DuckDuckGo.

    Args:
        query: Search query
        max_results: Maximum number of results

    Returns:
        List of results with title, body, href
    """
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "body": r.get("body", ""),
                    "href": r.get("href", ""),
                }
                for r in results
            ]
    except ImportError:
        print("duckduckgo-search not installed")
        return []
    except Exception as e:
        print(f"Web search failed: {e}")
        return []


def format_search_results(results: List[Dict[str, str]]) -> str:
    """Format search results into context string."""
    if not results:
        return ""

    parts = []
    for i, r in enumerate(results, 1):
        parts.append(f"[{i}] {r['title']}\n{r['body']}")

    return "\n\n".join(parts)
