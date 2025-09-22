from pathlib import Path
import os


# Resolve project root (tinyowl/) from this file's location (tinyowl/chat_app)
ROOT: Path = Path(__file__).resolve().parents[1]

# Core paths
DB_PATH: Path = ROOT / "vectordb"
CHUNKS_DIR: Path = ROOT / "domains" / "theology" / "chunks"
OSIS_CONFIG_PATH: Path = ROOT / "configs" / "osis_canonical.yaml"
VENV_PATH: Path = ROOT / "venv"

# Chunk files used for fast lookups (pure concordance/no-AI mode)
KJV_VERSES_JSON: Path = CHUNKS_DIR / "kjv_verses_chunks.json"
WEB_VERSES_JSON: Path = CHUNKS_DIR / "web_verses_chunks.json"
STRONGS_CONCORDANCE_JSON: Path = CHUNKS_DIR / "strongs_concordance_entries_chunks.json"
STRONGS_NUMBERS_JSON: Path = CHUNKS_DIR / "strongs_strongs_numbers_chunks_with_defs.json"

# App state (store runtime artifacts under 'chat-app' to match spec)
APP_DATA_DIR: Path = ROOT / "chat-app"
HISTORY_DB_PATH: Path = APP_DATA_DIR / "history.sqlite3"
HISTORY_FILE_PATH: Path = APP_DATA_DIR / ".tinyowl_history"
EXPORTS_DIR: Path = APP_DATA_DIR / "exports"
SETTINGS_FILE_PATH: Path = APP_DATA_DIR / "settings.json"

# Defaults
DEFAULT_MAX_RESULTS = 10

# Ollama configuration (overridable via env)
# - TINYOWL_OLLAMA_HOST: e.g., http://localhost:11434
# - TINYOWL_OLLAMA_MODEL: e.g., mistral:latest
OLLAMA_HOST = os.environ.get("TINYOWL_OLLAMA_HOST", "http://localhost:11434")
DEFAULT_AI_MODEL = os.environ.get("TINYOWL_OLLAMA_MODEL", "mistral:latest")
