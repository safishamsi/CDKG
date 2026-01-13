"""
Fix imports to avoid tensorflow/protobuf issues
"""
import sys

# Monkey patch to prevent tensorflow import
class TensorFlowStub:
    def __getattr__(self, name):
        raise ImportError("TensorFlow is disabled for this project")

# Add stub before any imports
sys.modules['tensorflow'] = TensorFlowStub()

