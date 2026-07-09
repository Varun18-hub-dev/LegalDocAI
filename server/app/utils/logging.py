import logging
import sys
from pathlib import Path

# Create a logger
logger = logging.getLogger("legaldocai")
logger.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Optionally write to file
log_file_dir = Path(__file__).resolve().parent.parent.parent / "logs"
log_file_dir.mkdir(exist_ok=True)
file_handler = logging.FileHandler(log_file_dir / "app.log", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_logger(module_name: str) -> logging.Logger:
    """Helper to return a module-specific logger child."""
    return logging.getLogger(f"legaldocai.{module_name}")
