import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_community.tools.duckduckgo import DuckDuckGoSearchRun
from langchain.chains import RetrievalQA
from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from sentence_transformers import SentenceTransformer

# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# LLM & Embedding
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=GEMINI_API_KEY,
    temperature=0.3
)

# Embed
embedder = SentenceTransformer("all-MiniLM-L6-v2")
vector_store = FAISS.from_texts(["dummy"], embedder)
retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.85}
)

# Web Search Tool
search_tool = DuckDuckGoSearchRun()

# RetrievalQA Chain
rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=False
)

# Daftar tools LangChain
tools = [
    Tool(name="web_search", func=search_tool, description="Search the web"),
    Tool(name="cache_retriever", func=rag_chain.run, description="Retrieve from cached vector store")
]

# Inisialisasi Agent dengan memory percakapan
memory = ConversationBufferMemory(memory_key="chat_history")

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type="openai-tools",
    memory=memory
)

def generate_reply(comment, caption, username):
    prompt = f"""IG caption: {caption}\nKomentar: {comment}\nUsername: {username}\nJawab relevan & ringkas."""
    return agent.invoke({"input": prompt})['output']
