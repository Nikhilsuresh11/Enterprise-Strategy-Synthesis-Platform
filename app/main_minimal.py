"""Minimal FastAPI app to test Render deployment."""

from fastapi import FastAPI

app = FastAPI(title="Stratagem AI - Minimal Test")

@app.get("/")
def root():
    return {"status": "ok", "message": "Minimal app working"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
