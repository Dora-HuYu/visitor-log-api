from fastapi import FastAPI

app = FastAPI(title="Visitor Log API")


@app.get("/health")
def health_check():
    return {"status": "ok"}