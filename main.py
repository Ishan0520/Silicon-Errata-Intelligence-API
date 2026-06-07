from fastapi import FastAPI

app = FastAPI(
    title="Silicon Errata Intelligence API",
    description=(
        "Track, query, and report on silicon errata across chip families. "
        "Built for automotive OEM teams managing ECU supply chains."
    ),
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
