import os
import sys

# This file should be called only once
# It is a utility file that initializes the database

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import init_db

if __name__ == "__main__":
    init_db()
