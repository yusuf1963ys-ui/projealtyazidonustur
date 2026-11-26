const videoInput = document.getElementById("video-input");
const fileNameEl = document.getElementById("file-name");
const videoPlayer = document.getElementById("video-player");
const playerPlaceholder = document.getElementById("player-placeholder");

const sourceLangSelect = document.getElementById("source-lang");
const targetLangSelect = document.getElementById("target-lang");
const swapLangBtn = document.getElementById("swap-lang-btn");
const transcribeBtn = document.getElementById("transcribe-btn");
const langWarningEl = document.getElementById("lang-warning");

const transcribeStatusEl = document.getElementById("transcribe-status");
const transcribeSpinnerEl = document.getElementById("transcribe-spinner");
const transcribeStatusTextEl = document.getElementById("transcribe-status-text");

const subtitlePairEl = document.getElementById("subtitle-pair");
const subtitleSourceEl = document.getElementById("subtitle-source");
const subtitleTargetEl = document.getElementById("subtitle-target");

const healthBadge = document.getElementById("health-badge");
const healthText = document.getElementById("health-text");

let currentVideoUrl = null;
let selectedFile = null;
let subtitleSegments = [];
let lastRenderedIndex = -2;
let isTranscribing = false;

function setHealthState(state, message) {
  healthBadge.className = `health-badge status-${state}`;
  healthText.textContent = message;
}

async function checkHealth() {
  setHealthState("loading", "Kontrol ediliyor...");

  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    if (data.status === "ok") {
      setHealthState("ok", data.message || "Bağlantı hazır");
    } else {
      setHealthState("error", "Sunucu yanıtı geçersiz");
    }
  } catch (error) {
    setHealthState("error", "Bağlantı yok");
  }
}

function setTranscribeStatus(type, message, showSpinner = false) {
  if (!type) {
    transcribeStatusEl.hidden = true;
    transcribeSpinnerEl.hidden = true;
    transcribeStatusTextEl.textContent = "";
    return;
  }

  transcribeStatusEl.className = `banner banner-${type}`;
  transcribeStatusTextEl.textContent = message;
  transcribeSpinnerEl.hidden = !showSpinner;
  transcribeStatusEl.hidden = false;
}

function setControlsBusy(busy) {
  isTranscribing = busy;
  transcribeBtn.disabled = busy || !selectedFile;
  transcribeBtn.textContent = busy ? "İşleniyor..." : "Altyazı Oluştur";
  sourceLangSelect.disabled = busy;
  targetLangSelect.disabled = busy;
  swapLangBtn.disabled = busy;
  videoInput.disabled = busy;
}

function getSelectedLabel(selectEl) {
  const option = selectEl.options[selectEl.selectedIndex];
  return option ? option.textContent : selectEl.value;
}

function updateLanguageState() {
  const isSame = sourceLangSelect.value === targetLangSelect.value;
  langWarningEl.hidden = !isSame;

  if (!isSame && transcribeStatusEl.classList.contains("banner-warning")) {
    setTranscribeStatus(null, "");
  }

  const sourceLabel = getSelectedLabel(sourceLangSelect);
  const targetLabel = getSelectedLabel(targetLangSelect);
  subtitlePairEl.textContent = `${sourceLabel} → ${targetLabel}`;
}

function handleSwapLanguages() {
  if (isTranscribing) {
    return;
  }
  const previousSource = sourceLangSelect.value;
  sourceLangSelect.value = targetLangSelect.value;
  targetLangSelect.value = previousSource;
  updateLanguageState();
}

function resetSubtitles(
  sourceMessage,
  targetMessage = "Çeviri satırı burada görünecek"
) {
  subtitleSegments = [];
  lastRenderedIndex = -2;
  subtitleSourceEl.textContent = sourceMessage;
  subtitleSourceEl.classList.add("subtitle-placeholder");
  subtitleTargetEl.textContent = targetMessage;
  subtitleTargetEl.classList.add("subtitle-placeholder");
}

function findActiveSegmentIndex(currentTime) {
  for (let i = 0; i < subtitleSegments.length; i += 1) {
    const seg = subtitleSegments[i];
    if (currentTime >= seg.start && currentTime <= seg.end) {
      return i;
    }
  }
  return -1;
}

function updateActiveSubtitle() {
  if (subtitleSegments.length === 0) {
    return;
  }

  const activeIndex = findActiveSegmentIndex(videoPlayer.currentTime);
  if (activeIndex === lastRenderedIndex) {
    return;
  }
  lastRenderedIndex = activeIndex;

  subtitleSourceEl.classList.remove("subtitle-placeholder");
  subtitleTargetEl.classList.remove("subtitle-placeholder");

  if (activeIndex >= 0) {
    const activeSegment = subtitleSegments[activeIndex];
    subtitleSourceEl.textContent = activeSegment.text || "";
    subtitleTargetEl.textContent = activeSegment.translation || "";
  } else {
    subtitleSourceEl.textContent = "";
    subtitleTargetEl.textContent = "";
  }
}

function handleVideoSelect(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) {
    return;
  }

  if (currentVideoUrl) {
    URL.revokeObjectURL(currentVideoUrl);
  }

  selectedFile = file;
  currentVideoUrl = URL.createObjectURL(file);
  videoPlayer.src = currentVideoUrl;
  videoPlayer.hidden = false;
  playerPlaceholder.hidden = true;
  videoPlayer.load();

  fileNameEl.textContent = file.name;
  fileNameEl.classList.remove("file-name-empty");
  fileNameEl.title = file.name;

  transcribeBtn.disabled = false;
  setTranscribeStatus(null, "");
  resetSubtitles(
    'Çift altyazı çıkarmak için "Altyazı Oluştur" butonuna basın',
    "Çeviri satırı burada görünecek"
  );
}

async function handleTranscribe() {
  if (!selectedFile || isTranscribing) {
    return;
  }

  if (sourceLangSelect.value === targetLangSelect.value) {
    langWarningEl.hidden = false;
    setTranscribeStatus(
      "warning",
      "Kaynak ve hedef dil aynı olamaz. İşlemi başlatmadan önce farklı diller seçin."
    );
    return;
  }

  setControlsBusy(true);
  setTranscribeStatus(
    "info",
    "Ses ayrıştırılıyor, altyazı çıkarılıyor ve çevriliyor...",
    true
  );

  try {
    const formData = new FormData();
    formData.append("video", selectedFile);
    formData.append("source_lang", sourceLangSelect.value);
    formData.append("target_lang", targetLangSelect.value);

    const response = await fetch("/api/transcribe", {
      method: "POST",
      body: formData,
    });

    let data = null;
    try {
      data = await response.json();
    } catch (parseErr) {
      data = null;
    }

    if (!response.ok) {
      const errorMessage =
        (data && data.detail) ||
        `Altyazı ve çeviri oluşturulamadı (HTTP ${response.status}).`;
      throw new Error(errorMessage);
    }

    const receivedSegments = Array.isArray(data && data.segments)
      ? data.segments
      : [];

    subtitleSegments = receivedSegments;
    lastRenderedIndex = -2;

    if (subtitleSegments.length > 0) {
      setTranscribeStatus(
        "ok",
        `Çift altyazı hazır (${subtitleSegments.length} cümle/segment).`
      );
      updateActiveSubtitle();
    } else {
      resetSubtitles("Videoda konuşma tespit edilemedi.", "");
      setTranscribeStatus("warning", "Videoda konuşma tespit edilemedi.");
    }
  } catch (error) {
    setTranscribeStatus(
      "error",
      error.message || "Altyazı ve çeviri çıkarılırken bir hata oluştu."
    );
  } finally {
    setControlsBusy(false);
  }
}

videoInput.addEventListener("change", handleVideoSelect);
sourceLangSelect.addEventListener("change", updateLanguageState);
targetLangSelect.addEventListener("change", updateLanguageState);
swapLangBtn.addEventListener("click", handleSwapLanguages);
transcribeBtn.addEventListener("click", handleTranscribe);
videoPlayer.addEventListener("timeupdate", updateActiveSubtitle);
videoPlayer.addEventListener("seeked", updateActiveSubtitle);
healthBadge.addEventListener("click", checkHealth);

window.addEventListener("beforeunload", () => {
  if (currentVideoUrl) {
    URL.revokeObjectURL(currentVideoUrl);
  }
});

document.addEventListener("DOMContentLoaded", () => {
  updateLanguageState();
  checkHealth();
});
