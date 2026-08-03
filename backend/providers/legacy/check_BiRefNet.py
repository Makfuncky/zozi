from rembg import new_session
import logging

logger = logging.getLogger(__name__)

# Try to load BiRefNet model
try:
    session = new_session("birefnet-general")
    print("✅ BiRefNet is available!")
except Exception as e:
    print(f"❌ BiRefNet not available: {e}")
    print("\nTrying other models...")
    
    # List available models
    from rembg.sessions import sessions_class
    print(f"Available models: {list(sessions_class.keys())}")




"""

# Test which BiRefNet models are available
model_names = [
    'birefnet-general',
    'birefnet-general-lite', 
    'birefnet-portrait',
    'birefnet-massive',
    'birefnet-dis',
    'birefnet-hrsod',
    'birefnet-cod',
    'birefnet-mo',
]

from rembg import new_session

for model_name in model_names:
    try:
        session = new_session(model_name)
        print(f"✅ {model_name} - AVAILABLE")
    except Exception as e:
        print(f"❌ {model_name} - Not available")

"""










