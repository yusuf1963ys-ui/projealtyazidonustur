# Çift Altyazı - Yerel PC Dil Öğrenme Uygulaması

Bilgisayarınızdaki en fazla 30 dakikalık videoları cümle cümle çift yönlü çeviren ve çift altyazı ile oynatan yerel bir masaüstü dil öğrenme uygulamasıdır.

> **Not:** Proje şu anda **Faz 1 (Proje İskeleti ve Temel PC Penceresi)** aşamasındadır.

## Gereksinimler
- Python 3.10 veya üzeri

## Kurulum ve Çalıştırma (Windows PowerShell)

1. **Proje klasöründe sanal ortam (`venv`) oluşturun:**
   ```powershell
   python -m venv venv
   ```

2. **Sanal ortamı etkinleştirin:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   *(PowerShell betik çalıştırma kısıtlaması alırsanız geçici olarak `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` komutunu çalıştırabilirsiniz.)*

3. **Bağımlılıkları yükleyin:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Uygulamayı başlatın:**
   ```powershell
   python app.py
   ```

Uygulama açıldığında yerel masaüstü penceresinde başlangıç ekranı görünür ve arka plandaki FastAPI sunucusuna (`/api/health`) istek atarak **"Bağlantı hazır"** durumunu gösterir.

## Proje Yapısı
- `app.py`: FastAPI sunucusunu arka plan iş parçacığında başlatır ve `pywebview` masaüstü penceresini açar.
- `backend/`: FastAPI sunucusu (`server.py`) ve ileriki fazlara ait yer tutucu modüller (`audio.py`, `transcribe.py`, `translate.py`).
- `frontend/`: Sade HTML, CSS ve JavaScript arayüz dosyaları.
- `PLAN.md`: 6 fazlı proje yol haritası.
