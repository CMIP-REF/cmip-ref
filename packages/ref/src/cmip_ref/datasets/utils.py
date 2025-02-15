from pathlib import Path


def validate_path(raw_path: str) -> Path:
    """
    Validate the prefix of a dataset against the data directory
    """
    prefix = Path(raw_path)

    if not prefix.exists():
        raise FileNotFoundError(prefix)

    if not prefix.is_absolute():
        raise ValueError(f"Path {prefix} must be absolute")

    return prefix
