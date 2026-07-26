"""Verify the Sarvam key is readable and the SDK client builds. Run: python3 check_key.py"""

from config import get_api_key

try:
    key = get_api_key()
except RuntimeError as e:
    raise SystemExit(f"FAIL: {e}")

from sarvamai import SarvamAI

SarvamAI(api_subscription_key=key)
print(f"OK: key loaded ({key[:4]}...{key[-4:]}, {len(key)} chars), client constructed.")
