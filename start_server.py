"""
Start the FastAPI server on port 8020
"""
import uvicorn
import sys

if __name__ == "__main__":
    print("Starting server on http://0.0.0.0:8020")
    print("Press CTRL+C to stop")
    sys.stdout.flush()

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8020,
        reload=True,
        log_level="info"
    )

