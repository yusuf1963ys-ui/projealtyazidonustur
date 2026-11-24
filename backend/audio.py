"""FFmpeg kullanarak video dosyasından 16kHz mono WAV ses ayrıştırma modülü."""

from pathlib import Path
import shutil
import subprocess


class AudioExtractionError(RuntimeError):
    """Ses ayrıştırma sırasında oluşan hataları temsil eder."""


def extract_audio(video_path: str | Path, output_wav_path: str | Path) -> Path:
    """Verilen video dosyasından 16kHz mono PCM WAV ses dosyası üretir."""
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise AudioExtractionError(
            "FFmpeg bulunamadı. Lütfen FFmpeg'i kurup sistem PATH değişkenine ekleyin."
        )

    source_path = Path(video_path)
    target_path = Path(output_wav_path)

    if not source_path.exists():
        raise AudioExtractionError("Ses ayrıştırılacak video dosyası bulunamadı.")

    target_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        ffmpeg_bin,
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(target_path),
    ]

    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            creationflags=creation_flags,
        )
    except FileNotFoundError as exc:
        raise AudioExtractionError(
            "FFmpeg çalıştırılamadı. Kurulumu ve PATH ayarlarını kontrol edin."
        ) from exc
    except OSError as exc:
        raise AudioExtractionError(
            f"FFmpeg başlatılırken sistem hatası oluştu: {exc}"
        ) from exc

    if result.returncode != 0:
        stderr_lines = [
            line.strip()
            for line in (result.stderr or "").splitlines()
            if line.strip()
        ]
        stderr_lower = (result.stderr or "").lower()
        if "does not contain any stream" in stderr_lower or "no audio" in stderr_lower:
            raise AudioExtractionError(
                "Seçilen video dosyasında ses kanalı bulunamadı."
            )
        detail = stderr_lines[-1] if stderr_lines else "Bilinmeyen FFmpeg hatası."
        raise AudioExtractionError(
            f"FFmpeg videodan ses ayırırken hata oluştu: {detail}"
        )

    if not target_path.exists() or target_path.stat().st_size == 0:
        raise AudioExtractionError(
            "Ses dosyası oluşturulamadı veya video geçerli bir ses kanalı içermiyor."
        )

    return target_path
