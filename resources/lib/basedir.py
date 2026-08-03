import os, sys


def get_path(file, default):
    base = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--base-dir=")), os.getenv("BASE_DIR", default))
    if not base:
        base = default

    return os.path.join(base, file)
