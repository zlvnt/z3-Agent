from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun

search_tool = DuckDuckGoSearchRun()

def search_web(query: str, k: int = 3) -> list[str]:
    result = search_tool.invoke(query)
    if isinstance(result, str):
        return [result]
    elif isinstance(result, list):
        return result[:k]
    else:
        return []