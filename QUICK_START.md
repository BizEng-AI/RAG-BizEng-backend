# 🚀 QUICK START GUIDE

## Start Server (Port 8020)
```bash
cd C:\Users\sanja\rag-biz-english\server
start_server.bat
```

## Test Endpoints
```bash
# Health
curl http://localhost:8020/health

# Chat
curl -X POST http://localhost:8020/chat -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}"
```

## Ingest Documents
```bash
python ingest.py
```

## Check Qdrant
```bash
python test_quick.py
```

## Fly.io Commands
```bash
fly status --app bizeng-server
fly logs --app bizeng-server
fly deploy --app bizeng-server
```

## Credentials
```
Qdrant:  https://9963ec6f-613b-4fc2-84a7-cdcd7712fed8.eu-central-1-0.aws.cloud.qdrant.io
API Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.JqQKtcPaZgl-zLwfngmGn-f5oAzghkNtZP6Tv1EfHKY
Collection: bizeng
```

## Status
✅ All files configured  
✅ Qdrant collection created  
✅ Fly.io secrets updated  
✅ App loads without errors  
⏳ Ready to start server

