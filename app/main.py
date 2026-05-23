from fastapi import FastAPI

app = FastAPI(
    title="Multi-Agent Billing Support System",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "message": "Multi-Agent Billing Support System API"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }