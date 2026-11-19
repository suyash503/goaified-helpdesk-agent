"""RAG over the policy documents.

Ingest: each markdown file is split into one chunk per "## " section, so every
chunk carries a citation (document title + section heading). Chunks are embedded
with Chroma's default local embedding model (all-MiniLM-L6-v2, runs on CPU).

Search: embed the question, return the closest sections that are within
MAX_DISTANCE. Anything farther away is dropped, so an unrelated question gets
no context at all and the agent says it doesn't know instead of guessing.
"""
import re
from dataclasses import dataclass

import chromadb

from . import config


@dataclass
class Chunk:
    doc: str        # file name, e.g. leave-policy.md
    title: str      # document title, e.g. Leave Policy
    section: str    # section heading, e.g. 4. Carry forward
    text: str
    distance: float = 0.0

    @property
    def citation(self) -> str:
        return f"{self.title} ({self.doc}) § {self.section}"


def split_markdown(doc: str, markdown: str) -> list[Chunk]:
    """Split one policy file into section chunks."""
    title_match = re.search(r"^# (.+)$", markdown, re.M)
    title = title_match.group(1).strip() if title_match else doc
    chunks = []
    # re.split with a capture group keeps the headings: [intro, h1, body1, h2, body2, ...]
    parts = re.split(r"^## (.+)$", markdown, flags=re.M)
    for heading, body in zip(parts[1::2], parts[2::2]):
        body = body.strip()
        # Prefix the title + heading so the embedding knows what the section is about.
        chunks.append(Chunk(doc, title, heading.strip(), f"{title}: {heading.strip()}\n{body}"))
    return chunks


def _collection():
    client = chromadb.PersistentClient(path=config.CHROMA_DIR)
    return client.get_or_create_collection(config.COLLECTION, metadata={"hnsw:space": "cosine"})


def ingest() -> int:
    """(Re)build the vector store from policies/*.md. Returns the number of chunks."""
    client = chromadb.PersistentClient(path=config.CHROMA_DIR)
    try:
        client.delete_collection(config.COLLECTION)
    except Exception:
        pass
    col = client.create_collection(config.COLLECTION, metadata={"hnsw:space": "cosine"})
    chunks = []
    for path in sorted(config.POLICY_DIR.glob("*.md")):
        chunks += split_markdown(path.name, path.read_text(encoding="utf-8"))
    col.add(
        ids=[f"{c.doc}#{i}" for i, c in enumerate(chunks)],
        documents=[c.text for c in chunks],
        metadatas=[{"doc": c.doc, "title": c.title, "section": c.section} for c in chunks],
    )
    return len(chunks)


def search(question: str, k: int = config.TOP_K) -> list[Chunk]:
    res = _collection().query(query_texts=[question], n_results=k)
    hits = []
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        if dist <= config.MAX_DISTANCE:
            hits.append(Chunk(meta["doc"], meta["title"], meta["section"], text, dist))
    # Keep only chunks nearly as relevant as the best one, so the cited sources are the ones
    # that actually answer the question (not the "closest of the rest").
    if hits:
        hits = [h for h in hits if h.distance <= hits[0].distance + config.RELATIVE_MARGIN]
    return hits
