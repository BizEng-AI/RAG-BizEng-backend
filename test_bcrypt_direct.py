"""
SIMPLEST POSSIBLE TEST - Direct bcrypt usage
"""
import sys

print("=" * 60)
print("DIRECT BCRYPT TEST (No passlib)")
print("=" * 60)
print()

# Test 1: Can we import bcrypt?
try:
    import bcrypt
    print("✅ bcrypt imported")
except Exception as e:
    print(f"❌ Cannot import bcrypt: {e}")
    sys.exit(1)

# Test 2: Can we hash with bcrypt directly?
try:
    password = b"test123"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    print(f"✅ bcrypt.hashpw works: {hashed[:30]}...")
except Exception as e:
    print(f"❌ bcrypt.hashpw failed: {e}")
    sys.exit(1)

# Test 3: Can we verify?
try:
    if bcrypt.checkpw(password, hashed):
        print("✅ bcrypt.checkpw works (correct password)")
    else:
        print("❌ bcrypt.checkpw returned False")
        sys.exit(1)
except Exception as e:
    print(f"❌ bcrypt.checkpw failed: {e}")
    sys.exit(1)

# Test 4: Does it reject wrong password?
try:
    if not bcrypt.checkpw(b"wrong", hashed):
        print("✅ bcrypt correctly rejects wrong password")
    else:
        print("❌ bcrypt accepted wrong password")
        sys.exit(1)
except Exception as e:
    print(f"❌ Wrong password check failed: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("✅ BCRYPT WORKS PERFECTLY!")
print("=" * 60)
print()
print("Now let's test passlib...")
print()

# Test 5: Can passlib work with bcrypt?
try:
    from passlib.context import CryptContext
    print("✅ CryptContext imported")

    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    print("✅ CryptContext created")

    test_hash = ctx.hash("test123")
    print(f"✅ ctx.hash works: {test_hash[:30]}...")

    if ctx.verify("test123", test_hash):
        print("✅ ctx.verify works")
    else:
        print("❌ ctx.verify returned False")
        sys.exit(1)

    print()
    print("=" * 60)
    print("🎉 PASSLIB + BCRYPT WORKS PERFECTLY!")
    print("=" * 60)

except Exception as e:
    print(f"❌ Passlib test failed: {e}")
    print()
    print("SOLUTION: Use bcrypt directly instead of passlib")
    sys.exit(1)

print()
print("✅ ALL TESTS PASSED - Ready to use!")

