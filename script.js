// Proxy OS desktop interactions — front-end demo only.
const $ = (id) => document.getElementById(id);

function openWindow(id) {
  const win = $(id);
  if (!win) return;
  win.classList.remove("hidden");
  win.style.zIndex = String(Date.now());
}
function closeWindow(id) {
  const win = $(id);
  if (win) win.classList.add("hidden");
}
function minimizeWindow(id) { closeWindow(id); }
function maximizeWindow(id) {
  const win = $(id);
  if (!win) return;
  if (win.dataset.maximized === "true") {
    win.style.inset = "";
    win.style.width = "";
    win.style.height = "";
    win.style.transform = "";
    win.style.left = "";
    win.style.top = "";
    win.dataset.maximized = "false";
  } else {
    win.style.left = "8px";
    win.style.top = "8px";
    win.style.right = "8px";
    win.style.bottom = "62px";
    win.style.width = "auto";
    win.style.height = "auto";
    win.style.transform = "none";
    win.dataset.maximized = "true";
  }
}
function toggleStart() { $("startMenu").classList.toggle("hidden"); }
function normalizeAddress(raw) {
  const value = raw.trim();
  if (!value) return "";
  if (/^https?:\/\//i.test(value)) return value;
  if (/^(localhost|127\.0\.0\.1)(:\d+)?([/].*)?$/i.test(value)) return "http://" + value;
  if (/^[^\s]+\.[^\s]+$/.test(value)) return "https://" + value;
  return "https://duckduckgo.com/?q=" + encodeURIComponent(value);
}
function navigate(raw) {
  const url = normalizeAddress(raw);
  if (!url) return;
  $("addressInput").value = url;
  $("viewerAddress").textContent = url;
  $("webFrame").src = url;
  $("homeTab").classList.add("hidden");
  $("browserViewer").classList.remove("hidden");
}
function showHome() {
  $("browserViewer").classList.add("hidden");
  $("homeTab").classList.remove("hidden");
  $("addressInput").value = "";
}
$("addressForm").addEventListener("submit", (event) => {
  event.preventDefault();
  navigate($("addressInput").value);
});
$("heroSearch").addEventListener("submit", (event) => {
  event.preventDefault();
  navigate($("heroInput").value);
});
document.querySelectorAll("[data-url]").forEach((button) => {
  button.addEventListener("click", () => navigate(button.dataset.url));
});
document.querySelectorAll("[data-open]").forEach((button) => {
  button.addEventListener("click", () => {
    openWindow(button.dataset.open);
    $("startMenu").classList.add("hidden");
  });
});
document.querySelectorAll("[data-close]").forEach((button) => button.addEventListener("click", () => closeWindow(button.dataset.close)));
document.querySelectorAll("[data-minimize]").forEach((button) => button.addEventListener("click", () => minimizeWindow(button.dataset.minimize)));
document.querySelectorAll("[data-maximize]").forEach((button) => button.addEventListener("click", () => maximizeWindow(button.dataset.maximize)));
$("startButton").addEventListener("click", toggleStart);
$("powerButton").addEventListener("click", () => $("startMenu").classList.add("hidden"));
$("taskbarSearch").addEventListener("click", () => { openWindow("browserWindow"); $("heroInput").focus(); });
$("newTabButton").addEventListener("click", showHome);
$("addTabButton").addEventListener("click", showHome);
$("backButton").addEventListener("click", () => { try { $("webFrame").contentWindow.history.back(); } catch (_) {} });
$("forwardButton").addEventListener("click", () => { try { $("webFrame").contentWindow.history.forward(); } catch (_) {} });
$("refreshButton").addEventListener("click", () => { try { $("webFrame").contentWindow.location.reload(); } catch (_) { $("webFrame").src = $("webFrame").src; } });
$("openExternal").addEventListener("click", () => {
  const url = $("viewerAddress").textContent;
  if (url && url !== "Ready") window.open(url, "_blank", "noopener,noreferrer");
});
$("saveNote").addEventListener("click", () => {
  const blob = new Blob([$("notesText").value], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url; link.download = "notes.txt"; link.click();
  URL.revokeObjectURL(url);
});
document.querySelectorAll("[data-accent]").forEach((button) => {
  button.addEventListener("click", () => document.documentElement.style.setProperty("--accent", button.dataset.accent));
});
function updateClock() {
  const now = new Date();
  $("clockTime").textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  $("clockDate").textContent = now.toLocaleDateString([], { month: "short", day: "numeric" });
}
updateClock();
setInterval(updateClock, 1000);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") $("startMenu").classList.add("hidden");
  if (event.ctrlKey && event.key.toLowerCase() === "l") {
    event.preventDefault(); openWindow("browserWindow"); $("addressInput").focus(); $("addressInput").select();
  }
});
document.addEventListener("click", (event) => {
  if (!event.target.closest("#startMenu") && !event.target.closest("#startButton")) $("startMenu").classList.add("hidden");
});
