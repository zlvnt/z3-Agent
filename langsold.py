import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
from langchain.chains import RetrievalQA
from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain_community.embeddings import HuggingFaceEmbeddings

# Load .env & Gemini Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Load personality JSON
base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "personality1.json")
with open(file_path) as f:
    personality = json.load(f)

# Inisialisasi Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=GEMINI_API_KEY,
    temperature=0.3
)

# Embedding (masih sentence-transformers)
embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = FAISS.from_texts(["dummy"], embedder)
retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.85}
)

# Web Search Tool
search_tool = DuckDuckGoSearchRun()
res = search_tool.run("Siapa presiden Indonesia saat ini?")
print(res)

# RetrievalQA Chain
rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=False
)

# LangChain Tools
tools = [
    Tool(name="web_search", func=search_tool, description="Search the web"),
    Tool(name="cache_retriever", func=rag_chain.run, description="Retrieve from cached vector store")
]

# Memory
memory = ConversationBufferMemory(memory_key="chat_history")

# Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type="openai-tools",
    memory=memory
)

def generate_reply(comment, caption, username):
    persona = personality["persona"] 
    prompt = f"""{persona}\n\nCaption IG: {caption}\nKomentar user: {comment}\nUsername: {username}\nBalas singkat, kontekstual, dan sesuai karakter z3."""
    return agent.invoke({"input": prompt})['output']
