"""Yerel PC Dil Öğrenme Uygulaması - Masaüstü Başlatıcı."""

import os
import socket
import threading
import time

# 8 GB gibi sınırlı RAM'e sahip sistemlerde Intel MKL bellek taşmasını önle
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("ARGOS_COMPUTE_TYPE", "int8")
os.environ.setdefault("ARGOS_INTRA_THREADS", "2")
os.environ.setdefault("ARGOS_INTER_THREADS", "1")
os.environ.setdefault("ARGOS_BATCH_SIZE", "8")
os.environ.setdefault("ARGOS_BEAM_SIZE", "2")

import uvicorn
import webview

from backend.server import app

HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}"


def wait_for_server(host: str, port: int, timeout: float = 10.0) -> bool:
    """Yerel FastAPI sunucusunun bağlantıları kabul etmesini bekler."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.25):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def main() -> None:
    config = uvicorn.Config(
        app=app,
        host=HOST,
        port=PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)

    server_thread = threading.Thread(
        target=server.run,
        name="fastapi-server",
        daemon=True,
    )
    server_thread.start()

    if not wait_for_server(HOST, PORT):
        raise RuntimeError(f"Yerel sunucu {URL} adresinde başlatılamadı.")

    webview.create_window(
        title="Çift Altyazı - Dil Öğrenme Uygulaması",
        url=URL,
        width=1100,
        height=720,
        min_size=(800, 540),
    )

    try:
        webview.start()
    finally:
        server.should_exit = True


if __name__ == "__main__":
    main()
