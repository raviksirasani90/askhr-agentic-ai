import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT_DIR / "data" / "hr_policies.txt"
VECTOR_DIR = ROOT_DIR / "vectorstore"

load_dotenv(ROOT_DIR / ".env")


def ingest_documents():
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL")
    embedding_model = os.getenv("OPENROUTER_EMBEDDING_MODEL")

    if not api_key or api_key == "your_actual_api_key":
        raise ValueError("Configure OPENROUTER_API_KEY in .env first.")

    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Policy document not found: {DATA_FILE}")

    loader = TextLoader(str(DATA_FILE), encoding="utf-8")
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings(
        model=embedding_model,
        api_key=api_key,
        base_url=base_url,
    )

    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(str(VECTOR_DIR))

    print(f"Source documents: {len(documents)}")
    print(f"Chunks created: {len(chunks)}")
    print(f"Vector index saved to: {VECTOR_DIR}")


if __name__ == "__main__":
    ingest_documents()