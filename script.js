
const browserFrame = document.getElementById("browserFrame");
const addressInput = document.getElementById("address");
const addressForm = document.getElementById("addressForm");

function openApp(id) {
  const app = document.getElementById(id);

  if (app) {
    app.hidden = false;
    app.style.zIndex = Date.now();
  }
}

function closeApp(id) {
  const app = document.getElementById(id);

  if (app) {
    app.hidden = true;
  }
}

function minimizeApp(id) {
  closeApp(id);
}

function navigateTo(input) {
  let value = input.trim();

  if (!value) return;

  let url;

  try {
    if (!/^https?:\/\//i.test(value)) {
      if (value.includes(".") && !value.includes(" ")) {
        value = "https://" + value;
      } else {
        value = "https://www.google.com/search?q=" +
          encodeURIComponent(value);
      }
    }

    url = new URL(value);

    if (!["http:", "https:"].includes(url.protocol)) {
      alert("Only HTTP and HTTPS addresses are supported.");
      return;
    }

    browserFrame.src = url.href;
    addressInput.value = url.href;

  } catch (error) {
    alert("Please enter a valid website address.");
  }
}

addressForm.addEventListener("submit", function (event) {
  event.preventDefault();
  navigateTo(addressInput.value);
});

function goBack() {
  try {
    browserFrame.contentWindow.history.back();
  } catch (error) {
    console.log("Back navigation is unavailable.");
  }
}

function goForward() {
  try {
    browserFrame.contentWindow.history.forward();
  } catch (error) {
    console.log("Forward navigation is unavailable.");
  }
}

function reloadPage() {
  try {
    browserFrame.contentWindow.location.reload();
  } catch (error) {
    browserFrame.src = browserFrame.src;
  }
}

function changeBackground() {
  const colors = [
    "linear-gradient(135deg, #124c88, #401d70)",
    "linear-gradient(135deg, #065f46, #164e63)",
    "linear-gradient(135deg, #7c2d12, #7e22ce)",
    "linear-gradient(135deg, #1e3a8a, #0f766e)",
    "linear-gradient(135deg, #334155, #111827)"
  ];

  const color = colors[Math.floor(Math.random() * colors.length)];

  document.querySelector(".desktop").style.background = color;
}

function updateClock() {
  const now = new Date();

  const time = now.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit"
  });

  document.getElementById("clock").textContent = time;
  document.getElementById("taskbarClock").textContent = time;
}

updateClock();
setInterval(updateClock, 1000);
