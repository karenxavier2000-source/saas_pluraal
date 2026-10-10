import sys
from pathlib import Path

# Add root folder to sys.path so it finds the Backend module
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from Backend.server import create_app

# Vercel needs an "app" object to serve as WSGI
app = create_app()
