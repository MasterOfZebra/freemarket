"""
FreeMarket Backend Configuration
Centralized settings for database, API, logging, etc.
"""

import os
from dotenv import load_dotenv

# Load environment variables if .env file exists
if os.path.exists('.env'):
    load_dotenv()

# ============================================================
# DATABASE CONFIG
# ============================================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://assistadmin_pg:assistMurzAdmin@postgres:5432/assistance_kz"
)

# ============================================================
# REDIS CONFIG
# ============================================================
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# ============================================================
# API CONFIG
# ============================================================
API_TITLE = "FreeMarket API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "A free marketplace for mutual aid and resource exchange"

# CORS settings
CORS_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://localhost",        # Local production
    "http://127.0.0.1",        # Localhost
]

# ============================================================
# TELEGRAM BOT CONFIG
# ============================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "")

# ============================================================
# LOGGING CONFIG
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================
# ENVIRONMENT
# ============================================================
ENV = os.getenv("ENV", "development")
DEBUG = ENV == "development"

# ============================================================
# CACHE CONFIG
# ============================================================
CACHE_TTL = 3600  # 1 hour default
CACHE_EMBEDDINGS_TTL = 86400  # 24 hours for embeddings

# ============================================================
# RATE LIMITING
# ============================================================
RATE_LIMIT_LISTINGS_PER_HOUR = 10
RATE_LIMIT_ENABLED = True

# ============================================================
# MATCHING CONFIG
# ============================================================
MATCHING_SCORE_THRESHOLD = 0.5
MATCHING_TOP_K = 10
MATCHING_SIMILARITY_METRIC = "cosine"
