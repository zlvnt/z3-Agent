from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun

_search_tool: Union["DuckDuckGoSearchRun", None] = None

def _get_search_tool() -> "DuckDuckGoSearchRun":
    global _search_tool
    if _search_tool is None:
        from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun

        _search_tool = DuckDuckGoSearchRun()
    return _search_tool

def search_web(query: str, k: int = 3) -> list[str]:
    tool = _get_search_tool()
    result = tool.invoke(query)
    if isinstance(result, str):
        return [result]
    elif isinstance(result, list):
        return result[:k]
    else:
        return []