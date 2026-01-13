"""Test if imports work with tensorflow stub"""
import sys

# Stub tensorflow before any imports
class TensorFlowStub:
    def __getattr__(self, name):
        raise ImportError("TensorFlow is disabled")

sys.modules['tensorflow'] = TensorFlowStub()

# Now try importing
try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence-transformers imports successfully!")
except Exception as e:
    print(f"❌ Error: {e}")

