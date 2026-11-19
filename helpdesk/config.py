"""All settings in one place, read from environment variables / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# LLM: "ollama" (local, free, default), "gemini" or "openai"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
# 127.0.0.1, not localhost: on Windows "localhost" tries IPv6 first and adds ~2 s per call
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

# Vector DB (Chroma, stored on disk; no server needed)
CHROMA_DIR = os.getenv("CHROMA_DIR", str(ROOT / ".chroma"))
POLICY_DIR = ROOT / "policies"
COLLECTION = "hr_it_policies"
TOP_K = 3
# Cosine distance (0 = identical, 2 = opposite). Chunks farther than this are
# treated as "not relevant"; if none are close enough, the agent says it doesn't know.
# Measured: most real questions score 0.24-0.50, but "How many casual leaves do I get?"
# scores 0.70 while unanswerable ones (ESOP, insurance) score 0.60-0.71: they overlap, so
# this only drops clearly unrelated text (cricket: 0.80+). The LLM grade node does the rest.
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", "0.72"))
RELATIVE_MARGIN = 0.15   # also drop chunks more than this much worse than the best match

# Postgres, used only by the MCP server, with a read-only role
PG_DSN = os.getenv(
    "PG_DSN",
    "postgresql://helpdesk_ro:readonly_dev_only@127.0.0.1:5433/helpdesk",
)
