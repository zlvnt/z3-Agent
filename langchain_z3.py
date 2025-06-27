import os
import faiss

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
from langchain.chains import RetrievalQA
from langchain.agents import Tool
from typing_extensions import TypedDict
from langgraph.graph import START, StateGraph

from config import GEMINI_API_KEY
import personality as persona
import conversation as convo

try:
    from rf_model import analyze_sentiment
except Exception:
    # Fall back to a dummy sentiment analyzer if the model cannot be loaded
    # (e.g. missing pickle files or other import issues)
    def analyze_sentiment(_text: str) -> str:
        return "Netral"

# ----------------------------------------------------------------------------
#  LLM & TOOLING INITIALISATION
# ----------------------------------------------------------------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.4,
)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
vector_store = FAISS.load_local("faiss_store", embeddings, allow_dangerous_deserialization=False)
retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "k": 4,
        "score_threshold": 0.85},
)
rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=False,
)

# External web search
search_tool = DuckDuckGoSearchRun()

# ----------------------------------------------------------------------------
#  Router Agent (LangGraph)
# ----------------------------------------------------------------------------

class _RouterState(TypedDict):
    user_input: str
    route_to: str  # 'rag' | 'websearch'

def _route(state: _RouterState) -> dict:
    prompt = f"""
    You are a routing agent. Your task is to choose the appropriate information source to answer the user's message below.

    User's Message:
    "{state['user_input']}"

    Choose exactly ONE option from these:
    - direct       → if the message can be answered directly without external info.
    - internal_doc → if the message specifically asks about internal documentation or reports.
    - web_search   → if the message needs general knowledge, news, or external information.

    ONLY answer with: direct OR internal_doc OR web_search.
    """
    
    decision = llm.invoke(prompt).content.strip().lower()

    if decision.startswith("internal_doc"):
        route = "rag"
    elif decision.startswith("web_search"):
        route = "websearch"
    else:
        route = "direct"
        
    return {"route_to": route}

_router_graph = (
    StateGraph(_RouterState)
    .add_node("route", _route)
    .add_edge(START, "route")
    .compile()
)

def _decide_route(text: str) -> str:
    return _router_graph.invoke({"user_input": text})["route_to"]

# ----------------------------------------------------------------------------
#  HELPERS
# ----------------------------------------------------------------------------

_PERSONALITY_DATA = persona.load_personality()

_REPLY_DO_RULES = "\n  - " + "\n  - ".join(_PERSONALITY_DATA.get("rules", {}).get("reply_do", []))
_DONT_RULES = "\n  - " + "\n  - ".join(_PERSONALITY_DATA.get("rules", {}).get("dont", []))
_REPLY_PROMPT_TEMPLATE = persona.get_prompt(_PERSONALITY_DATA, "reply")


def _build_context(post_id: str, comment_id: str, limit: int = 5) -> str:
    history = convo.get_comment_history(post_id, comment_id)
    if not history:
        return ""

    slices = history[-limit:]
    ctx_lines = ["Riwayat Percakapan:"]
    for h in slices:
        ctx_lines.append(f"{h['user']}: {h['comment']}")
        ctx_lines.append(f"z3: {h['reply']}")
    return "\n".join(ctx_lines)


# ----------------------------------------------------------------------------
#  MAIN PUBLIC API
# ----------------------------------------------------------------------------

def generate_reply(comment: str, post_id: str, comment_id: str, username: str) -> str:

    # Sentiment & basic post info ------------------------------------------------
    sentiment = analyze_sentiment(comment)
    post_data = persona.get_post_by_id(_PERSONALITY_DATA, post_id) or {}
    post_caption = post_data.get("caption", "Tanpa konteks.")

    # Conversation context
    context = _build_context(post_id, comment_id)

    # Decide route
    route = _decide_route(comment)

    if route == "rag":
        external_info = rag_chain.run(comment)
    elif route == "websearch":
        external_info = search_tool.run(comment)
    else:  # direct
        external_info = None

    if external_info:
        context = f"{context}\n\nInfo Eksternal:\n{external_info}"

    print(f"[router] route chosen: {route}")

    # Prompt construction -------------------------------------------------------
    prompt = _REPLY_PROMPT_TEMPLATE.format(
        post_caption=post_caption,
        username=username,
        comment=comment,
        sentiment=sentiment,
        context=context,
        reply_do_rules=_REPLY_DO_RULES,
        dont_rules=_DONT_RULES,
    )

    # LLM call ------------------------------------------------------------------
    try:
        response = llm.invoke(prompt)
        ai_reply = response.content if hasattr(response, "content") else str(response)
    except Exception as err:
        print(f"❌ LLM error: {err}")
        ai_reply = "AI gagal merespons."

    # Save conversation ---------------------------------------------------------
    convo.append_comment(post_id, comment_id, username, comment, ai_reply)
    return ai_reply

if __name__ == "__main__":
    demo_reply = generate_reply(
        comment="Keren banget!",
        post_id="18088890409561216",
        comment_id="demo123",
        username="tester",
    )
    print("\n=== Demo Reply ===\n", demo_reply)
