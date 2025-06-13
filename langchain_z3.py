import os
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
from langchain.chains import RetrievalQA
from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory

from config import GEMINI_API_KEY
import personality as persona
import conversation as convo

# --- Optional sentiment model (fallback ke "Netral" jika tidak ada) ---
try:
    from rf_model import analyze_sentiment  # type: ignore
except ImportError:  # pragma: no cover
    def analyze_sentiment(_text: str) -> str:  # noqa: D401
        """Fallback dummy sentiment analyzer."""
        return "Netral"

# ----------------------------------------------------------------------------
#  LLM & TOOLING INITIALISATION
# ----------------------------------------------------------------------------

# Large‑language model (Gemini‑1.5‑pro via LangChain wrapper)
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=GEMINI_API_KEY,
    temperature=0.4,
)

# Minimal RAG scaffold (can be expanded later)
embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = FAISS.from_texts(["dummy"], embedder)
retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.85},
)
rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=False,
)

# External web search tool (optional — dipanggil via agent jika dibutuhkan)
search_tool = DuckDuckGoSearchRun()

# LangChain agent setup (tools + memory)
_tools = [
    Tool(name="web_search", func=search_tool, description="Search the Web (DuckDuckGo)"),
    Tool(name="cache_retriever", func=rag_chain.run, description="Retrieve cached knowledge base"),
]
memory = ConversationBufferMemory(memory_key="chat_history")
agent = initialize_agent(
    tools=_tools,
    llm=llm,
    agent_type="openai-tools",
    memory=memory,
)

# ----------------------------------------------------------------------------
#  HELPERS
# ----------------------------------------------------------------------------

_PERSONALITY_DATA = persona.load_personality()

_REPLY_DO_RULES = "\n  - " + "\n  - ".join(_PERSONALITY_DATA.get("rules", {}).get("reply_do", []))
_DONT_RULES = "\n  - " + "\n  - ".join(_PERSONALITY_DATA.get("rules", {}).get("dont", []))
_REPLY_PROMPT_TEMPLATE = persona.get_prompt(_PERSONALITY_DATA, "reply")


def _build_context(post_id: str, comment_id: str, limit: int = 5) -> str:
    """Mengambil riwayat percakapan (maks `limit` pesan terakhir) untuk konteks."""
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
    """Generate AI reply that mirrors the behaviour of `agent_gemini.generate_reply`."""

    # Sentiment & basic post info ------------------------------------------------
    sentiment = analyze_sentiment(comment)
    post_data = persona.get_post_by_id(_PERSONALITY_DATA, post_id) or {}
    post_caption = post_data.get("caption", "Tanpa konteks.")
    tone = post_data.get("tone", "lifestyle")

    # Conversation context ------------------------------------------------------
    context = _build_context(post_id, comment_id)

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
        # LangChain agent gives tool‑use flexibility if prompt memicu panggilan tool
        response = agent.invoke({"input": prompt})
        ai_reply = response.get("output") if isinstance(response, dict) else str(response)
    except Exception:  # pragma: no cover
        try:
            ai_reply = llm.predict(prompt)
        except Exception as err:  # ultimate fallback
            print(f"❌ LLM error: {err}")
            ai_reply = "AI gagal merespons."

    # Save conversation ---------------------------------------------------------
    convo.append_comment(post_id, comment_id, username, comment, ai_reply)

    return ai_reply


# Convenience for interactive testing -----------------------------------------
if __name__ == "__main__":
    demo_reply = generate_reply(
        comment="Keren banget!",
        post_id="18088890409561216",
        comment_id="demo123",
        username="tester",
    )
    print("\n=== Demo Reply ===\n", demo_reply)
