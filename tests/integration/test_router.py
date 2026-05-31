import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.core.router import classify_intent

print(classify_intent("पिरेंका तिवारी 30 माई 38, 35, 42, 49, 40, सलवार सेंति 30, 15"))

print(classify_intent("बिंदु का नाप क्या है और कब देना है"))
