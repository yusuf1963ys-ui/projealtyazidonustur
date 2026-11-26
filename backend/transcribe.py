"""faster-whisper ile WAV ses dosyasından zaman damgalı altyazı üretme modülü."""

import gc
from pathlib import Path
import threading
from typing import Any

import ctranslate2
from faster_whisper import WhisperModel

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

DEFAULT_MODEL_SIZE = "base"

_model_lock = threading.Lock()
_model_cache: dict[tuple[str, str, str], WhisperModel] = {}


class TranscriptionError(RuntimeError):
    """Altyazı (transkripsiyon) işlemi sırasında oluşan hataları temsil eder."""


def _detect_device_and_compute_type() -> tuple[str, str]:
    """CUDA destekliyorsa GPU, aksi halde CPU int8 yapılandırmasını seçer."""
    try:
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def _get_model(model_size: str = DEFAULT_MODEL_SIZE) -> WhisperModel:
    """Whisper modelini bellekte önbelleğe alarak yükler."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    device, compute_type = _detect_device_and_compute_type()
    cache_key = (model_size, device, compute_type)

    with _model_lock:
        if cache_key in _model_cache:
            return _model_cache[cache_key]

        try:
            model_kwargs: dict[str, Any] = {
                "device": device,
                "compute_type": compute_type,
                "download_root": str(MODELS_DIR),
            }
            if device == "cpu":
                model_kwargs["cpu_threads"] = 2

            model = WhisperModel(model_size, **model_kwargs)
            _model_cache[cache_key] = model
            return model
        except Exception as exc:
            # CUDA kitaplıkları eksikse otomatik olarak CPU int8 moduna düş.
            if device != "cpu":
                fallback_key = (model_size, "cpu", "int8")
                if fallback_key in _model_cache:
                    return _model_cache[fallback_key]
                try:
                    model = WhisperModel(
                        model_size,
                        device="cpu",
                        compute_type="int8",
                        cpu_threads=2,
                        download_root=str(MODELS_DIR),
                    )
                    _model_cache[fallback_key] = model
                    return model
                except Exception as fallback_exc:
                    raise TranscriptionError(
                        f"Whisper modeli yüklenemedi: {fallback_exc}"
                    ) from fallback_exc

            raise TranscriptionError(f"Whisper modeli yüklenemedi: {exc}") from exc


def release_models() -> None:
    """Önbellekteki Whisper modellerini bellekten boşaltır (çeviri öncesi RAM açar)."""
    with _model_lock:
        for model in _model_cache.values():
            inner = getattr(model, "model", None)
            if inner is not None and hasattr(inner, "unload_model"):
                try:
                    inner.unload_model()
                except Exception:
                    pass
        _model_cache.clear()
    gc.collect()


def transcribe_audio(
    wav_path: str | Path,
    source_lang: str,
    model_size: str = DEFAULT_MODEL_SIZE,
) -> list[dict[str, Any]]:
    """Verilen WAV dosyasını faster-whisper ile yazıya döküp segment listesi döndürür."""
    audio_path = Path(wav_path)
    if not audio_path.exists():
        raise TranscriptionError("Altyazı çıkarılacak WAV ses dosyası bulunamadı.")

    lang_code = (source_lang or "").strip().lower() or None

    model = _get_model(model_size=model_size)

    try:
        raw_segments, _info = model.transcribe(
            str(audio_path),
            language=lang_code,
            vad_filter=True,
        )
        segments: list[dict[str, Any]] = []
        for segment in raw_segments:
            text = (segment.text or "").strip()
            if not text:
                continue
            segments.append(
                {
                    "start": round(float(segment.start), 3),
                    "end": round(float(segment.end), 3),
                    "text": text,
                }
            )
        return segments
    except TranscriptionError:
        raise
    except Exception as exc:
        raise TranscriptionError(
            f"Ses yazıya dönüştürülürken hata oluştu: {exc}"
        ) from exc
