import uuid
import datetime

def generate_unique_id(prefix: str = "doc") -> str:
    """Generate a unique alphanumeric identifier."""
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{prefix}_{unique_suffix}"

def get_current_timestamp() -> str:
    """Return current timestamp in ISO format."""
    return datetime.datetime.now().isoformat()
