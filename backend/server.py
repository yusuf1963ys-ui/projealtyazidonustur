"""FastAPI yerel sunucu ve statik arayüz sunumu (Faz 1)."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Çift Altyazı Dil Öğrenme API",
    version="0.1.0",
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Sunucunun ayakta olduğunu doğrulayan temel sağlık uç noktası."""
    return {
        "status": "ok",
        "message": "Bağlantı hazır",
    }


app.mount(
    "/",
    StaticFiles(directory=str(FRONTEND_DIR), html=True),
    name="frontend",
)
