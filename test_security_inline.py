"""
Inline test of security.py functions
"""
print("Testing security.py...")
print()

# Test 1: Import security module
try:
    from security import hash_password, verify_password, make_access_token, make_refresh_token
    print("✅ security module imported successfully")
except Exception as e:
    print(f"❌ Failed to import security: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 2: Hash a password
try:
    password = "test123"
    hashed = hash_password(password)
    print(f"✅ hash_password works: {hashed[:30]}...")
except Exception as e:
    print(f"❌ hash_password failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Verify correct password
try:
    if verify_password(password, hashed):
        print("✅ verify_password works (correct password)")
    else:
        print("❌ verify_password returned False for correct password")
        exit(1)
except Exception as e:
    print(f"❌ verify_password failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Reject wrong password
try:
    if not verify_password("wrongpass", hashed):
        print("✅ verify_password correctly rejects wrong password")
    else:
        print("❌ verify_password accepted wrong password")
        exit(1)
except Exception as e:
    print(f"❌ Wrong password test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 5: Make JWT token
try:
    token = make_access_token("test@example.com", ["student"])
    print(f"✅ make_access_token works: {token[:50]}...")
except Exception as e:
    print(f"❌ make_access_token failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 6: Make refresh token
try:
    refresh = make_refresh_token()
    print(f"✅ make_refresh_token works: {refresh[:20]}...")
except Exception as e:
    print(f"❌ make_refresh_token failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("=" * 60)
print("🎉 ALL SECURITY FUNCTIONS WORK!")
print("=" * 60)
print()
print("Now run: python test_system_verification.py")

