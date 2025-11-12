"""
Configuration for matching system
Centralized settings for tolerances, thresholds, and model parameters
"""

import os
import json
from typing import Dict, Any
from pathlib import Path

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./exchange.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# API Configuration
API_TITLE = os.getenv("API_TITLE", "FreeMarket API")
API_VERSION = os.getenv("API_VERSION", "2.2.1")
API_DESCRIPTION = os.getenv("API_DESCRIPTION", "AI-Powered Marketplace for Mutual Aid & Exchange")
CORS_ORIGINS = json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:3000", "http://127.0.0.1:3000", "https://assistance-kz.ru"]'))
ENV = os.getenv("ENV", "development")


class MatchingConfig:
    """Configuration for the matching system"""

    # Vector similarity settings
    VECTOR_MODEL_NAME = os.getenv('VECTOR_MODEL', 'multilingual')
    VECTOR_CACHE_DIR = os.getenv('VECTOR_CACHE_DIR')

    # Tolerance settings (how much price/time difference to allow)
    VALUE_TOLERANCE = float(os.getenv('EXCHANGE_TOLERANCE', '0.15'))          # ±15% for permanent
    TEMPORAL_TOLERANCE = float(os.getenv('TEMPORAL_TOLERANCE', '0.25'))       # ±25% for temporary
    CROSS_CATEGORY_VALUE_TOLERANCE = float(os.getenv('CROSS_CATEGORY_TOLERANCE', '0.5'))  # ±50% for cross-category

    # Matching thresholds
    MIN_MATCH_SCORE = float(os.getenv('EXCHANGE_MIN_SCORE', '0.70'))          # 70% base minimum
    CROSS_CATEGORY_MIN_SCORE = float(os.getenv('CROSS_CATEGORY_MIN_SCORE', '0.30'))  # 30% for cross-category

    # Combined score thresholds
    SAME_CATEGORY_THRESHOLD = float(os.getenv('SAME_CATEGORY_THRESHOLD', '0.70'))
    CROSS_CATEGORY_THRESHOLD = float(os.getenv('CROSS_CATEGORY_THRESHOLD', '0.20'))

    # Scoring weights
    SEMANTIC_VECTOR_WEIGHT = float(os.getenv('SEMANTIC_VECTOR_WEIGHT', '0.4'))    # 40%
    WORD_OVERLAP_WEIGHT = float(os.getenv('WORD_OVERLAP_WEIGHT', '0.4'))         # 40%
    FUZZY_MATCH_WEIGHT = float(os.getenv('FUZZY_MATCH_WEIGHT', '0.2'))           # 20%

    # Cost priority settings
    COST_PRIORITY_FACTOR = float(os.getenv('COST_PRIORITY_FACTOR', '0.5'))       # How much cost affects ranking

    # Duration penalty settings
    DURATION_MATCH_BONUS = float(os.getenv('DURATION_MATCH_BONUS', '1.1'))       # Bonus for matching duration
    DURATION_MISMATCH_PENALTY = float(os.getenv('DURATION_MISMATCH_PENALTY', '0.9'))  # Penalty for different duration

    # Cache settings
    ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'true').lower() == 'true'
    CACHE_SIZE = int(os.getenv('CACHE_SIZE', '10000'))

    # Data paths
    DATA_DIR = Path(__file__).parent / 'data'
    SYNONYMS_FILE = DATA_DIR / 'synonyms.json'
    STOPWORDS_FILE = DATA_DIR / 'stopwords.txt'

    # Model settings
    SENTENCE_TRANSFORMERS_HOME = os.getenv('SENTENCE_TRANSFORMERS_HOME', str(DATA_DIR / 'models'))

    @classmethod
    def get_scoring_weights(cls) -> Dict[str, float]:
        """Get scoring weights as dict"""
        return {
            'semantic_vector': cls.SEMANTIC_VECTOR_WEIGHT,
            'word_overlap': cls.WORD_OVERLAP_WEIGHT,
            'fuzzy_match': cls.FUZZY_MATCH_WEIGHT,
        }

    @classmethod
    def get_thresholds(cls, is_cross_category: bool = False) -> Dict[str, float]:
        """Get appropriate thresholds based on category relationship"""
        if is_cross_category:
            return {
                'min_match_score': cls.CROSS_CATEGORY_MIN_SCORE,
                'combined_threshold': cls.CROSS_CATEGORY_THRESHOLD,
                'value_tolerance': cls.CROSS_CATEGORY_VALUE_TOLERANCE,
            }
        else:
            return {
                'min_match_score': cls.MIN_MATCH_SCORE,
                'combined_threshold': cls.SAME_CATEGORY_THRESHOLD,
                'value_tolerance': cls.VALUE_TOLERANCE,
            }

    @classmethod
    def validate_config(cls) -> None:
        """Validate configuration values"""
        assert 0 <= cls.VALUE_TOLERANCE <= 1, "VALUE_TOLERANCE must be between 0 and 1"
        assert 0 <= cls.MIN_MATCH_SCORE <= 1, "MIN_MATCH_SCORE must be between 0 and 1"
        assert abs(sum(cls.get_scoring_weights().values()) - 1.0) < 0.01, "Scoring weights must sum to 1.0"

        # Validate thresholds are reasonable
        assert cls.CROSS_CATEGORY_MIN_SCORE < cls.MIN_MATCH_SCORE, "Cross-category threshold should be lower"
        assert cls.CROSS_CATEGORY_THRESHOLD < cls.SAME_CATEGORY_THRESHOLD, "Cross-category combined threshold should be lower"


# Validate config on import
MatchingConfig.validate_config()
