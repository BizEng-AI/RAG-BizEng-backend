"""
Quick verification that critical packages are installed
"""
import sys
import warnings

# Suppress bcrypt version warnings
warnings.filterwarnings('ignore', message='.*bcrypt.*')
warnings.filterwarnings('ignore', category=UserWarning, module='passlib')

print("Testing critical packages...")
print()

errors = []

# Test 1: email-validator
try:
    import email_validator
    from pydantic import EmailStr
    print("✅ email-validator: OK")
except ImportError as e:
    print(f"❌ email-validator: MISSING - {e}")
    errors.append("email-validator")

# Test 2: bcrypt (upgraded)
try:
    import bcrypt
    # Test if bcrypt works
    hashed = bcrypt.hashpw(b"test", bcrypt.gensalt())
    if bcrypt.checkpw(b"test", hashed):
        print("✅ bcrypt: OK (upgraded and working)")
    else:
        print("❌ bcrypt: Installed but not working correctly")
        errors.append("bcrypt-functionality")
except Exception as e:
    print(f"❌ bcrypt: ERROR - {e}")
    errors.append("bcrypt")

# Test 3: passlib compatibility
try:
    from passlib.hash import bcrypt as passlib_bcrypt
    # Use very short password to avoid any bcrypt length issues
    test_pw = "pass123"
    hash_val = passlib_bcrypt.hash(test_pw)
    if passlib_bcrypt.verify(test_pw, hash_val):
        print("✅ passlib + bcrypt: OK (compatible)")
    else:
        print("❌ passlib: Hash/verify not working")
        errors.append("passlib")
except Exception as e:
    print(f"❌ passlib: ERROR - {e}")
    errors.append("passlib")

# Test 4: JWT
try:
    from jose import jwt
    print("✅ python-jose: OK")
except ImportError as e:
    print(f"❌ python-jose: MISSING - {e}")
    errors.append("jose")

# Test 5: SQLAlchemy models
try:
    from models import User, ExerciseAttempt
    print("✅ models: OK (imports work)")
except Exception as e:
    print(f"❌ models: ERROR - {e}")
    errors.append("models")

print()
print("=" * 60)

if not errors:
    print("🎉 ALL CRITICAL PACKAGES WORKING!")
    print()
    print("Next step: Run full test")
    print("  python test_system_verification.py")
    sys.exit(0)
else:
    print(f"⚠️  {len(errors)} issue(s) found:")
    for err in errors:
        print(f"  - {err}")
    print()
    print("Fix with:")
    print('  pip install email-validator "pydantic[email]" --upgrade bcrypt passlib')
    sys.exit(1)

