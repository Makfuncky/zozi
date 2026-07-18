"""Test BiRefNet availability"""
from rembg import new_session, remove
from PIL import Image
import io

print("Testing BiRefNet availability...\n")

# Try different BiRefNet model names
model_names = [
    'birefnet-general',
    'birefnet-general-lite',
    'birefnet-portrait',
    'isnet-general-use',
    'u2net',
]

for model_name in model_names:
    try:
        print(f"Testing {model_name}...", end=" ")
        session = new_session(model_name)
        print("✅ AVAILABLE")
        
        # Test with a simple image
        test_img = Image.new('RGB', (100, 100), color='white')
        output = remove(test_img, session=session)
        print(f"  ✓ Model works! Output size: {output.size}")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")

print("\n" + "="*50)
print("Recommendation: Use the first AVAILABLE model")
print("="*50)