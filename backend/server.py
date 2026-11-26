"""FastAPI yerel sunucu, statik arayüz sunumu, altyazı ve çeviri uç noktaları."""

from pathlib import Path
import shutil
import tempfile
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from backend.audio import AudioExtractionError, extract_audio
from backend.transcribe import TranscriptionError, release_models, transcribe_audio
from backend.translate import TranslationError, translate_texts

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
TEMP_DIR = BASE_DIR / "temp"

SUPPORTED_LANGUAGES = {"tr", "en", "de", "fr", "es"}

app = FastAPI(
    title="Çift Altyazı Dil Öğrenme API",
    version="0.4.0",
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Sunucunun ayakta olduğunu doğrulayan temel sağlık uç noktası."""
    return {
        "status": "ok",
        "message": "Bağlantı hazır",
    }


@app.post("/api/transcribe")
def create_transcription(
    video: UploadFile = File(...),
    source_lang: str = Form("en"),
    target_lang: str = Form("tr"),
) -> dict[str, list[dict[str, Any]]]:
    """Yüklenen videodan ses ayırır, orijinal altyazı çıkarır ve hedef dile çevirir."""
    normalized_source = (source_lang or "").strip().lower()
    normalized_target = (target_lang or "").strip().lower()

    if normalized_source not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen kaynak dil kodu: {source_lang}",
        )

    if normalized_target not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen hedef dil kodu: {target_lang}",
        )

    if normalized_source == normalized_target:
        raise HTTPException(
            status_code=400,
            detail="Kaynak ve hedef dil aynı olamaz. Çift altyazı için farklı diller seçin.",
        )

    if not video.filename:
        raise HTTPException(
            status_code=400,
            detail="Geçerli bir video dosyası seçilmedi.",
        )

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    request_temp_dir = Path(tempfile.mkdtemp(prefix="job_", dir=str(TEMP_DIR)))

    raw_suffix = Path(video.filename).suffix.lower()
    suffix = raw_suffix if raw_suffix and len(raw_suffix) <= 10 else ".mp4"
    video_path = request_temp_dir / f"input{suffix}"
    wav_path = request_temp_dir / "audio.wav"

    try:
        with video_path.open("wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        if video_path.stat().st_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Yüklenen video dosyası boş.",
            )

        extract_audio(video_path, wav_path)
        segments = transcribe_audio(wav_path, source_lang=normalized_source)
        release_models()

        if segments:
            translations = translate_texts(
                [seg["text"] for seg in segments],
                source_lang=normalized_source,
                target_lang=normalized_target,
            )
            translated_segments = [
                {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "translation": translated_text,
                }
                for seg, translated_text in zip(segments, translations)
            ]
        else:
            translated_segments = []

        return {"segments": translated_segments}
    except HTTPException:
        raise
    except AudioExtractionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except TranscriptionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except TranslationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Altyazı ve çeviri oluşturulurken beklenmeyen bir hata oluştu: {exc}",
        ) from exc
    finally:
        try:
            video.file.close()
        except Exception:
            pass

        video_path.unlink(missing_ok=True)
        wav_path.unlink(missing_ok=True)
        shutil.rmtree(request_temp_dir, ignore_errors=True)


app.mount(
    "/",
    StaticFiles(directory=str(FRONTEND_DIR), html=True),
    name="frontend",
)
