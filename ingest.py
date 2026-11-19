"""Build the vector store from policies/*.md.  Usage: python ingest.py"""
from helpdesk import rag

if __name__ == "__main__":
    n = rag.ingest()
    print(f"Ingested {n} policy sections into Chroma.")
