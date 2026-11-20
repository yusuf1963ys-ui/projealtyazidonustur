const statusBox = document.getElementById("status-box");
const statusText = document.getElementById("status-text");
const retryBtn = document.getElementById("retry-btn");

function setStatus(state, message) {
  statusBox.className = `status-box status-${state}`;
  statusText.textContent = message;
}

async function checkHealth() {
  setStatus("loading", "Sunucu bağlantısı kontrol ediliyor...");

  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    if (data.status === "ok") {
      setStatus("ok", data.message || "Bağlantı hazır");
    } else {
      setStatus("error", "Sunucu beklenmeyen bir yanıt döndürdü.");
    }
  } catch (error) {
    setStatus("error", "Yerel sunucuya bağlanılamadı.");
  }
}

retryBtn.addEventListener("click", checkHealth);
document.addEventListener("DOMContentLoaded", checkHealth);
