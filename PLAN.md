# Proje Yol Haritası

Bilgisayardaki en fazla 30 dakikalık videoları cümle cümle çift yönlü çeviren ve çift altyazı ile oynatan yerel PC dil öğrenme uygulamasının 6 fazlı geliştirme planı:

## Faz 1: İskelet ve PC Penceresi (Mevcut Faz)
- Temel klasör yapısının (`backend/`, `frontend/`, `app.py`) kurulması.
- `FastAPI` + `uvicorn` ile yerel sunucu ve `/api/health` uç noktasının oluşturulması.
- `pywebview` ile yerel masaüstü penceresinin açılması ve başlangıç ekranında bağlantı durumunun doğrulanması.

## Faz 2: Yerel Video Seçimi ve Oynatıcı
- Bilgisayardan yerel video dosyası seçme akışının eklenmesi.
- HTML5 video oynatıcısı ve yerel dosya akış (stream / range request) desteğinin kurulması.
- Temel oynatma kontrolleri ve süre sınırı (en fazla 30 dakika) doğrulaması.

## Faz 3: FFmpeg + faster-whisper Altyazı
- `backend/audio.py` içinde FFmpeg ile videodan ses ayrıştırma.
- `backend/transcribe.py` içinde `faster-whisper` ile zaman damgalı cümle/segment altyazı üretimi.
- İşlem ilerleme durumunun arayüzde gösterilmesi.

## Faz 4: Argos Translate Çift Altyazı
- `backend/translate.py` içinde Argos Translate ile çevrimdışı cümle bazlı çift yönlü çeviri.
- Orijinal ve çevrilmiş altyazının video üzerinde senkronize çift altyazı olarak gösterilmesi.
- Kaynak ve hedef dil seçimi.

## Faz 5: Cümle Tekrarı ve Kelime Baloncuğu
- Aktif cümleyi tek tıkla veya kısayolla tekrar oynatma (loop / önceki-sonraki cümle).
- Altyazıdaki kelimelere tıklandığında yerel anlam/çeviri baloncuğu gösterimi.
- Öğrenme odaklı oynatma hızı ve etkileşimli altyazı listesi.

## Faz 6: 30 dk Optimizasyonu ve Dağıtım
- 30 dakikalık videolarda bellek, işlem süresi ve önbellek (cache) optimizasyonları.
- Geçici dosya temizliği ve hata yönetimi iyileştirmeleri.
- Windows için tek tıkla çalıştırılabilir paketleme / dağıtım hazırlığı.
