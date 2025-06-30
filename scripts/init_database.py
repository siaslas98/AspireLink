import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import init_db

if __name__ == "__main__":
    init_db()
