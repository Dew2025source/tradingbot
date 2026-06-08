const user = requireUser();
document.getElementById("welcomeUser").textContent = `Logged in as ${user.name}`;

let map;
let currentMarker = null;
let savedMarker = null;
let currentLocation = null;
let selectedSaved = null;

const statusValue = document.getElementById("statusValue");
const savedCount = document.getElementById("savedCount");
const distanceValue = document.getElementById("distanceValue");
const noteValue = document.getElementById("noteValue");
const historyList = document.getElementById("historyList");

function initMap() {
  map = L.map("map", { zoomControl: true }).setView([28.6139, 77.2090], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
}

function haversineDistance(lat1, lon1, lat2, lon2) {
  const toRad = (deg) => (deg * Math.PI) / 180;
  const R = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);

  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) ** 2;

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function formatDistance(km) {
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(2)} km`;
}

function setCurrentMarker(lat, lng) {
  if (currentMarker) currentMarker.remove();
  currentMarker = L.circleMarker([lat, lng], {
    radius: 9,
    color: "#26d07c",
    fillColor: "#26d07c",
    fillOpacity: 1
  }).addTo(map).bindPopup("You are here");
}

function setSavedMarker(lat, lng, note = "My vehicle") {
  if (savedMarker) savedMarker.remove();
  savedMarker = L.marker([lat, lng]).addTo(map).bindPopup(`Saved Spot: ${note}`);
}

function updateDistanceCard() {
  if (!currentLocation || !selectedSaved) {
    distanceValue.textContent = "--";
    return;
  }

  const km = haversineDistance(
    currentLocation.lat,
    currentLocation.lng,
    selectedSaved.lat,
    selectedSaved.lng
  );
  distanceValue.textContent = formatDistance(km);
}

async function getCurrentLocation() {
  statusValue.textContent = "Detecting...";
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        currentLocation = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude
        };

        setCurrentMarker(currentLocation.lat, currentLocation.lng);
        map.setView([currentLocation.lat, currentLocation.lng], 15);
        statusValue.textContent = "Ready";
        updateDistanceCard();
        resolve(currentLocation);
      },
      (err) => {
        statusValue.textContent = "Location blocked";
        reject(err);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  });
}

async function saveParking() {
  try {
    if (!currentLocation) await getCurrentLocation();

    const note = prompt("Add a note for this parking spot:", "Basement / Mall / Street") || "My vehicle";

    const res = await fetch(`${API}/save-location`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lat: currentLocation.lat,
        lng: currentLocation.lng,
        note,
        userEmail: user.email
      })
    });

    if (!res.ok) throw new Error("Failed to save");
    await loadHistory();
  } catch (e) {
    alert("Could not save parking spot.");
  }
}

function selectHistoryItem(item, focus = true) {
  selectedSaved = item;
  setSavedMarker(item.lat, item.lng, item.note);
  noteValue.textContent = item.note || "--";
  updateDistanceCard();

  if (focus) {
    map.setView([item.lat, item.lng], 16);
  }
}

function renderHistory(items) {
  savedCount.textContent = String(items.length);

  if (!items.length) {
    historyList.innerHTML = `<div class="empty">No parking saved yet. Save your first spot.</div>`;
    noteValue.textContent = "--";
    selectedSaved = null;
    updateDistanceCard();
    if (savedMarker) {
      savedMarker.remove();
      savedMarker = null;
    }
    return;
  }

  historyList.innerHTML = items.map(item => `
    <div class="history-item">
      <div class="history-top">
        <div>
          <div class="history-note">${item.note || "My vehicle"}</div>
          <div class="history-time">${new Date(item.createdAt).toLocaleString()}</div>
        </div>
      </div>
      <div class="history-meta">Lat: ${item.lat.toFixed(5)} • Lng: ${item.lng.toFixed(5)}</div>
      <div class="history-actions">
        <button class="action-btn" data-view="${item.id}">View</button>
        <button class="action-btn" data-directions="${item.id}">Directions</button>
        <button class="action-btn danger-btn" data-delete="${item.id}">Delete</button>
      </div>
    </div>
  `).join("");

  if (!selectedSaved) {
    selectHistoryItem(items[0], false);
  }
}

async function loadHistory() {
  const res = await fetch(`${API}/locations?userEmail=${encodeURIComponent(user.email)}`);
  const data = await res.json();
  renderHistory(data);
}

async function deleteLocation(id) {
  await fetch(`${API}/locations/${id}`, { method: "DELETE" });
  selectedSaved = null;
  await loadHistory();
}

function openDirections(item = selectedSaved) {
  if (!item) {
    alert("No saved parking location selected.");
    return;
  }
  window.open(`https://www.google.com/maps/dir/?api=1&destination=${item.lat},${item.lng}`, "_blank");
}

document.getElementById("saveBtn").addEventListener("click", saveParking);
document.getElementById("locateBtn").addEventListener("click", getCurrentLocation);
document.getElementById("findMyCarBtn").addEventListener("click", () => {
  if (!selectedSaved) {
    alert("No saved parking spot found.");
    return;
  }
  selectHistoryItem(selectedSaved, true);
});
document.getElementById("openMapsBtn").addEventListener("click", () => openDirections());

historyList.addEventListener("click", async (e) => {
  const viewId = e.target.getAttribute("data-view");
  const dirId = e.target.getAttribute("data-directions");
  const delId = e.target.getAttribute("data-delete");

  const res = await fetch(`${API}/locations?userEmail=${encodeURIComponent(user.email)}`);
  const items = await res.json();

  if (viewId) {
    const item = items.find(x => x.id === viewId);
    if (item) selectHistoryItem(item, true);
  }

  if (dirId) {
    const item = items.find(x => x.id === dirId);
    if (item) openDirections(item);
  }

  if (delId) {
    await deleteLocation(delId);
  }
});

initMap();
getCurrentLocation().catch(() => {});
loadHistory();
