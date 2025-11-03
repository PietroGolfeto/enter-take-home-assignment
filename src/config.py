"""
Configuration Module

Centralized configuration constants for the extraction system.
This module follows the Single Responsibility Principle (SRP) by only managing configuration.
"""
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_MODEL = "gpt-5-mini"
OPENAI_RESPONSE_FORMAT = {"type": "json_object"}

# PDF Processing Configuration
PDF_CHUNK_SIZE = 4096  # Bytes for reading PDF files in chunks

# Cache Configuration
CACHE_ENABLED = True

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
