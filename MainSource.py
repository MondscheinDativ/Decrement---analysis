# Core configuration for Actuarial Platform
import os
import sys
import pandas as pd
import numpy as np
import pyarrow as pa
from dotenv import load_dotenv
from loguru import logger

# Initialize environment
load_dotenv()

# System constants
SAS_GRID_USER = os.getenv('SAS_GRID_USER')
SAS_GRID_PASS = os.getenv('SAS_GRID_PASS')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Data processing settings
CHUNK_SIZE = 4096  # For stream processing
MAX_DATASET_SIZE = 100 * 1024 * 1024  # 100MB

# Configure logging
logger.add(
    "logs/application_{time}.log",
    rotation="100 MB",
    retention="30 days",
    level="DEBUG"
)

# Data validation rules
MORTALITY_DATA_SCHEMA = pa.schema([
    ("age", pa.int32()),
    ("year", pa.int32()),
    ("gender", pa.string()),
    ("mortality_rate", pa.float64())
])

# Model registry
ACTUARIAL_MODELS = {
    "lee-carter": {
        "name": "Lee-Carter Model",
        "formula": "ln(m_x) = a_x + b_x * k_t + e_x",
        "parameters": ["a_x", "b_x", "k_t"],
        "soa_ref": "SOA 2023-15"
    },
    "cbd": {
        "name": "CBD Model",
        "formula": "logit(q_x) = k_t^(1) + (x - x_bar) * k_t^(2)",
        "parameters": ["k_t^(1)", "k_t^(2)"],
        "soa_ref": "SOA 2023-22"
    }
}

if __name__ == "__main__":
    logger.info("Actuarial platform configuration loaded")
