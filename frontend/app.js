const videoInput = document.getElementById("video-input");
const fileNameEl = document.getElementById("file-name");
const videoPlayer = document.getElementById("video-player");
const playerPlaceholder = document.getElementById("player-placeholder");

const sourceLangSelect = document.getElementById("source-lang");
const targetLangSelect = document.getElementById("target-lang");
const swapLangBtn = document.getElementById("swap-lang-btn");
const langWarningEl = document.getElementById("lang-warning");
const subtitlePairEl = document.getElementById("subtitle-pair");

const healthBadge = document.getElementById("health-badge");
const healthText = document.getElementById("health-text");

let currentVideoUrl = null;

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

function getSelectedLabel(selectEl) {
  const option = selectEl.options[selectEl.selectedIndex];
  return option ? option.textContent : selectEl.value;
}

function updateLanguageState() {
  const isSame = sourceLangSelect.value === targetLangSelect.value;
  langWarningEl.hidden = !isSame;

  const sourceLabel = getSelectedLabel(sourceLangSelect);
  const targetLabel = getSelectedLabel(targetLangSelect);
  subtitlePairEl.textContent = `${sourceLabel} → ${targetLabel}`;
}

function handleSwapLanguages() {
  const previousSource = sourceLangSelect.value;
  sourceLangSelect.value = targetLangSelect.value;
  targetLangSelect.value = previousSource;
  updateLanguageState();
}

function handleVideoSelect(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) {
    return;
  }

  if (currentVideoUrl) {
    URL.revokeObjectURL(currentVideoUrl);
  }

  currentVideoUrl = URL.createObjectURL(file);
  videoPlayer.src = currentVideoUrl;
  videoPlayer.hidden = false;
  playerPlaceholder.hidden = true;
  videoPlayer.load();

  fileNameEl.textContent = file.name;
  fileNameEl.classList.remove("file-name-empty");
  fileNameEl.title = file.name;
}

videoInput.addEventListener("change", handleVideoSelect);
sourceLangSelect.addEventListener("change", updateLanguageState);
targetLangSelect.addEventListener("change", updateLanguageState);
swapLangBtn.addEventListener("click", handleSwapLanguages);
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
