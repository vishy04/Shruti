import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure project root is always in path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

