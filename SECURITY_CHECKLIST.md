# 🔐 SECURITY CHECKLIST - Before Going Public

**Created:** November 10, 2025  
**Purpose:** Ensure all credentials are rotated before sharing code publicly

---

## ⚠️ CRITICAL: Before Publishing Repository

### 1. Rotate All API Keys (REQUIRED)

#### Qdrant Cloud API Key
- [ ] Go to: https://cloud.qdrant.io
- [ ] Navigate to your cluster → API Keys
- [ ] Click "Create API Key"
- [ ] Copy the new key
- [ ] Update `.env` file: `QDRANT_API_KEY=new_key`
- [ ] Update Fly.io: `fly secrets set QDRANT_API_KEY="new_key" --app bizeng-server`
- [ ] Test connection: `python test_quick.py`
- [ ] Delete old key from Qdrant dashboard

#### Azure OpenAI Keys (Chat - Sweden Central)
- [ ] Go to: https://portal.azure.com
- [ ] Navigate to your Azure OpenAI resource (Sweden Central)
- [ ] Keys and Endpoint → Regenerate Key 1
- [ ] Copy the new key
- [ ] Update `.env` file: `AZURE_OPENAI_KEY=new_key`
- [ ] Update Fly.io: `fly secrets set AZURE_OPENAI_KEY="new_key" --app bizeng-server`
- [ ] Test: `curl http://localhost:8020/chat ...`

#### Azure OpenAI Keys (Embeddings - UAE North)
- [ ] Go to: https://portal.azure.com
- [ ] Navigate to your Azure OpenAI resource (UAE North)
- [ ] Keys and Endpoint → Regenerate Key 1
- [ ] Copy the new key
- [ ] Update `.env` file: `AZURE_OPENAI_EMBEDDING_KEY=new_key`
- [ ] Update Fly.io: `fly secrets set AZURE_OPENAI_EMBEDDING_KEY="new_key" --app bizeng-server`
- [ ] Test: `curl http://localhost:8020/debug/embed ...`

#### Azure Speech Service Key (East Asia)
- [ ] Go to: https://portal.azure.com
- [ ] Navigate to your Speech Service resource
- [ ] Keys and Endpoint → Regenerate Key 1
- [ ] Copy the new key
- [ ] Update `.env` file: `AZURE_SPEECH_KEY=new_key`
- [ ] Update Fly.io: `fly secrets set AZURE_SPEECH_KEY="new_key" --app bizeng-server`
- [ ] Test: `curl http://localhost:8020/pronunciation/test`

#### OpenAI API Key (Fallback)
- [ ] Go to: https://platform.openai.com/api-keys
- [ ] Create new secret key
- [ ] Copy the new key
- [ ] Update `.env` file: `OPENAI_API_KEY=new_key`
- [ ] Update Fly.io: `fly secrets set OPENAI_API_KEY="new_key" --app bizeng-server`

---

### 2. Verify .gitignore Protection

Run these commands to ensure sensitive files are protected:

```bash
# Check that .env is ignored
git check-ignore .env
# Should output: .env

# Check that setup docs with credentials are ignored
git check-ignore QDRANT_SETUP_SUMMARY.md MIGRATION_COMPLETE.md
# Should output the filenames

# Search for any staged sensitive files
git status --ignored
```

---

### 3. Search for Hardcoded Credentials

```bash
# Search entire codebase for potential secrets
git grep -i "eyJ"  # JWT tokens
git grep -i "sk-proj"  # OpenAI keys
git grep -i "azure.*key"  # Azure keys
git grep -i "api.*key.*="  # Generic API keys
git grep -i "password.*="  # Passwords
git grep -i "secret.*="  # Secrets

# Check commit history for leaked secrets
git log -p | grep -i "api.*key\|secret\|password"
```

If any secrets are found in commit history, you MUST:
1. Rotate those credentials immediately
2. Consider using `git filter-branch` or BFG Repo-Cleaner to remove them

---

### 4. Review Documentation Files

- [ ] Check all `.md` files for embedded credentials
- [ ] Review code comments for sensitive information
- [ ] Ensure example code uses placeholder values like `your-key-here`

```bash
# Search markdown files for keys
grep -r "eyJ" *.md
grep -r "sk-proj" *.md
grep -r "api-key.*:" *.md
```

---

### 5. Database Credentials

If using PostgreSQL in production:

- [ ] Rotate database password
- [ ] Update `DATABASE_URL` in Fly.io secrets
- [ ] Ensure database is not publicly accessible
- [ ] Enable SSL connections

---

### 6. Update Fly.io Secrets (After Rotation)

After rotating all keys, update Fly.io in one command:

```bash
fly secrets set \
  QDRANT_API_KEY="new_qdrant_key" \
  QDRANT_URL="https://..." \
  AZURE_OPENAI_KEY="new_azure_chat_key" \
  AZURE_OPENAI_EMBEDDING_KEY="new_azure_embed_key" \
  AZURE_SPEECH_KEY="new_speech_key" \
  OPENAI_API_KEY="new_openai_key" \
  --app bizeng-server
```

Verify secrets are set:
```bash
fly secrets list --app bizeng-server
```

---

### 7. Test After Rotation

Run full test suite to ensure everything still works:

```bash
# Start server
uvicorn app:app --host 0.0.0.0 --port 8020 --reload

# Test health
curl http://localhost:8020/health

# Test Qdrant
curl "http://localhost:8020/debug/search?q=test&k=3"

# Test chat
curl -X POST http://localhost:8020/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'

# Test pronunciation
curl http://localhost:8020/pronunciation/test

# Test embeddings
curl -X POST http://localhost:8020/debug/embed \
  -H "Content-Type: application/json" \
  -d '{"text":"test"}'
```

---

### 8. Final Git Checks

Before pushing to public repo:

```bash
# Check what will be committed
git status

# Ensure .env is NOT in the list
git ls-files | grep ".env"
# Should return nothing

# Check .gitignore is working
cat .gitignore

# Do a final diff
git diff --cached

# Only push if everything looks clean
git push origin main
```

---

## 🚨 What to Do If Credentials Are Accidentally Committed

### Immediate Actions (Within 1 Hour)

1. **Rotate ALL credentials immediately** (even if only one was exposed)
2. **Force push to remove from history** (if caught before others cloned):
   ```bash
   # Remove the file from history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push
   git push origin --force --all
   ```

3. **If it's too late to remove from history:**
   - Rotate all credentials
   - Consider the exposed credentials compromised forever
   - Monitor usage logs for suspicious activity
   - Document the incident

### Using BFG Repo-Cleaner (Easier Method)

```bash
# Install BFG
brew install bfg  # Mac
# or download from https://rtyley.github.io/bfg-repo-cleaner/

# Clone a fresh copy
git clone --mirror https://github.com/BizEng-AI/backend.git

# Remove sensitive files
bfg --delete-files .env backend.git
bfg --delete-files "*.env" backend.git

# Clean up
cd backend.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Push cleaned history
git push
```

---

## 📋 Quick Reference: Current Credentials (Nov 10, 2025)

**⚠️ THESE MUST BE ROTATED BEFORE GOING PUBLIC:**

- Qdrant API Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (ends in JqQKtcPaZgl...)
- Azure Chat Key: `DuQJzDcQmb9siNeUiiUsgaENRgewWHd9...` (ends in ACOGDSnb)
- Azure Embed Key: `9fyw2LxxdqRgay7cAuK84FXP7TwWMm1H...` (ends in ACOGMrGx)
- Azure Speech Key: `CbZ50wqN8vOc9BwwgUZak4sKkHqtUZSj...` (ends in ACOGKoCE)
- OpenAI Key: `sk-proj-kw7pgA3YOEcBZuRfePYA...` (ends in aScRtkA)

**Status:** In active development use. DO NOT PUBLISH without rotation.

---

## ✅ Final Checklist

Before making repository public:

- [ ] All API keys rotated
- [ ] Fly.io secrets updated with new keys
- [ ] All services tested with new keys
- [ ] `.gitignore` protecting sensitive files
- [ ] No hardcoded credentials in code
- [ ] No credentials in documentation
- [ ] No credentials in commit history
- [ ] Database credentials secured
- [ ] README security warning is visible
- [ ] This checklist completed

**After checklist completion:**
- [ ] Delete this file (or move to private notes)
- [ ] Make repository public
- [ ] Set up branch protection rules
- [ ] Enable Dependabot security alerts

---

**⏱️ Time Estimate:** 30-45 minutes for full key rotation  
**Frequency:** Rotate keys every 90 days minimum  
**Last Rotation:** Never (using development keys)  
**Next Rotation Due:** Before public release OR by February 10, 2026

---

**Document Status:** Active  
**Owner:** Development Team  
**Review Date:** Before every public release

