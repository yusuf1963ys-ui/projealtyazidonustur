"""Argos Translate ile düşük bellekli yerel çift yönlü cümle çevirisi modülü."""

import gc
import os
import threading

os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("ARGOS_COMPUTE_TYPE", "int8")
os.environ.setdefault("ARGOS_INTRA_THREADS", "2")
os.environ.setdefault("ARGOS_INTER_THREADS", "1")
os.environ.setdefault("ARGOS_BATCH_SIZE", "8")
os.environ.setdefault("ARGOS_BEAM_SIZE", "2")

import ctranslate2

try:
    import argostranslate.package

    _ARGOS_IMPORT_ERROR: Exception | None = None
except ImportError as exc:
    argostranslate = None  # type: ignore[assignment]
    _ARGOS_IMPORT_ERROR = exc

PIVOT_LANG = "en"
TRANSLATE_BATCH_SIZE = 8
TRANSLATE_BEAM_SIZE = 2
TRANSLATE_INTRA_THREADS = 2

_package_lock = threading.Lock()


class TranslationError(RuntimeError):
    """Çeviri veya dil paketi kurulumu sırasında oluşan hataları temsil eder."""


def _require_argos() -> None:
    if _ARGOS_IMPORT_ERROR is not None or argostranslate is None:
        raise TranslationError(
            "Argos Translate paketi yüklü değil. Lütfen 'pip install -r requirements.txt' "
            "komutunu çalıştırın."
        )


def _normalize_lang(lang_code: str) -> str:
    return (lang_code or "").strip().lower()


def _find_installed_package(from_code: str, to_code: str):
    installed = argostranslate.package.get_installed_packages()
    return next(
        (
            pkg
            for pkg in installed
            if getattr(pkg, "type", "translate") == "translate"
            and pkg.from_code == from_code
            and pkg.to_code == to_code
        ),
        None,
    )


def _is_pair_installed(from_code: str, to_code: str) -> bool:
    return _find_installed_package(from_code, to_code) is not None


def _install_pair(available_packages: list, from_code: str, to_code: str) -> None:
    """Belirtilen dil çifti için paketi indirip kurar."""
    if _is_pair_installed(from_code, to_code):
        return

    match = next(
        (
            pkg
            for pkg in available_packages
            if getattr(pkg, "type", "translate") == "translate"
            and pkg.from_code == from_code
            and pkg.to_code == to_code
        ),
        None,
    )
    if match is None:
        raise TranslationError(
            f"'{from_code} -> {to_code}' dil çifti için Argos Translate paketi bulunamadı."
        )

    try:
        download_path = match.download()
        argostranslate.package.install_from_path(download_path)
    except Exception as exc:
        raise TranslationError(
            f"'{from_code} -> {to_code}' dil paketi indirilemedi veya kurulamadı. "
            f"İnternet bağlantınızı kontrol edip tekrar deneyin. (Detay: {exc})"
        ) from exc


def ensure_language_packages(source_lang: str, target_lang: str) -> list:
    """Gerekli doğrudan veya İngilizce pivotlu dil paketlerini kurar ve sırayla döndürür."""
    _require_argos()

    source = _normalize_lang(source_lang)
    target = _normalize_lang(target_lang)

    if not source or not target:
        raise TranslationError("Kaynak ve hedef dil kodları boş olamaz.")

    if source == target:
        return []

    with _package_lock:
        direct_pkg = _find_installed_package(source, target)
        if direct_pkg is not None:
            return [direct_pkg]

        if source != PIVOT_LANG and target != PIVOT_LANG:
            first_pkg = _find_installed_package(source, PIVOT_LANG)
            second_pkg = _find_installed_package(PIVOT_LANG, target)
            if first_pkg is not None and second_pkg is not None:
                return [first_pkg, second_pkg]

        try:
            argostranslate.package.update_package_index()
            available_packages = argostranslate.package.get_available_packages()
        except Exception as exc:
            raise TranslationError(
                "Argos Translate paket listesi alınamadı. İlk kurulum için internet "
                f"bağlantısı gereklidir. (Detay: {exc})"
            ) from exc

        direct_available = next(
            (
                pkg
                for pkg in available_packages
                if getattr(pkg, "type", "translate") == "translate"
                and pkg.from_code == source
                and pkg.to_code == target
            ),
            None,
        )

        if direct_available is not None:
            _install_pair(available_packages, source, target)
            installed_pkg = _find_installed_package(source, target)
            if installed_pkg is None:
                raise TranslationError(
                    f"'{source} -> {target}' dil paketi kuruldu ancak yüklenemedi."
                )
            return [installed_pkg]

        if source != PIVOT_LANG and target != PIVOT_LANG:
            _install_pair(available_packages, source, PIVOT_LANG)
            _install_pair(available_packages, PIVOT_LANG, target)
            first_pkg = _find_installed_package(source, PIVOT_LANG)
            second_pkg = _find_installed_package(PIVOT_LANG, target)
            if first_pkg is None or second_pkg is None:
                raise TranslationError(
                    f"'{source} -> {target}' ara çeviri paketleri kuruldu ancak yüklenemedi."
                )
            return [first_pkg, second_pkg]

        raise TranslationError(
            f"'{source} -> {target}' dil çifti için uygun Argos Translate paketi bulunamadı."
        )


def _translate_with_package(pkg, texts: list[str]) -> list[str]:
    """Tek bir Argos paketini düşük bellekli int8 CTranslate2 ile çalıştırıp bellekten boşaltır."""
    model_path = str(pkg.package_path / "model")
    translator = ctranslate2.Translator(
        model_path,
        device="cpu",
        compute_type="int8",
        inter_threads=1,
        intra_threads=TRANSLATE_INTRA_THREADS,
    )

    try:
        results = [""] * len(texts)
        non_empty_indices: list[int] = []
        tokenized_inputs: list[list[str]] = []

        for idx, text in enumerate(texts):
            cleaned = (text or "").strip()
            if not cleaned:
                continue
            tokens = pkg.tokenizer.encode(cleaned)
            if not tokens:
                continue
            non_empty_indices.append(idx)
            tokenized_inputs.append(tokens)

        target_prefix_token = getattr(pkg, "target_prefix", "") or ""

        for start in range(0, len(tokenized_inputs), TRANSLATE_BATCH_SIZE):
            batch_tokens = tokenized_inputs[start : start + TRANSLATE_BATCH_SIZE]
            batch_indices = non_empty_indices[start : start + TRANSLATE_BATCH_SIZE]
            target_prefix = (
                [[target_prefix_token]] * len(batch_tokens)
                if target_prefix_token
                else None
            )

            translated_batch = translator.translate_batch(
                batch_tokens,
                target_prefix=target_prefix,
                replace_unknowns=True,
                max_batch_size=TRANSLATE_BATCH_SIZE,
                batch_type="examples",
                beam_size=TRANSLATE_BEAM_SIZE,
                num_hypotheses=1,
                length_penalty=0.2,
            )

            for out_idx, item in zip(batch_indices, translated_batch):
                out_tokens = item.hypotheses[0] if item.hypotheses else []
                decoded = pkg.tokenizer.decode(out_tokens)
                if target_prefix_token and decoded.startswith(target_prefix_token):
                    decoded = decoded[len(target_prefix_token) :]
                results[out_idx] = decoded.strip()

        return results
    finally:
        try:
            translator.unload_model()
        except Exception:
            pass
        del translator
        gc.collect()


def translate_texts(
    texts: list[str],
    source_lang: str,
    target_lang: str,
) -> list[str]:
    """Verilen metin listesini source_lang dilinden target_lang diline çevirir."""
    if not texts:
        return []

    packages = ensure_language_packages(source_lang, target_lang)
    if not packages:
        return [(text or "").strip() for text in texts]

    current_texts = list(texts)
    try:
        # Pivot çeviride iki modeli aynı anda RAM'de tutmamak için paketleri sırayla çalıştır
        for pkg in packages:
            current_texts = _translate_with_package(pkg, current_texts)
        return current_texts
    except TranslationError:
        raise
    except Exception as exc:
        raise TranslationError(
            f"Altyazılar çevrilirken hata oluştu: {exc}"
        ) from exc


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Tek bir metni source_lang dilinden target_lang diline çevirir."""
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    return translate_texts([cleaned], source_lang=source_lang, target_lang=target_lang)[0]
