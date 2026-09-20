const API_BASE = "http://127.0.0.1:8000/api";

const ICONS = ["⭐", "💧", "🏃", "📚", "🧘", "🥗", "😴", "✍️", "💪", "🎯", "🧹", "🎸"];
const COLORS = ["#6C5CE7", "#00B894", "#0984E3", "#FDCB6E", "#E17055", "#FF6B6B", "#00CEC9", "#A29BFE"];

let habits = [];
let selectedIcon = ICONS[0];
let selectedColor = COLORS[0];

// Хранит id редактируемой привычки. null означает "создаём новую".
let editingHabitId = null;

const el = (id) => document.getElementById(id);

// ---------------------------------------------------------------------
// Загрузка данных
// ---------------------------------------------------------------------

async function fetchHabits() {
  const res = await fetch(`${API_BASE}/habits`);
  habits = await res.json();
  renderHabits();
}

async function fetchStats() {
  const res = await fetch(`${API_BASE}/stats`);
  const stats = await res.json();
  el("statHabits").textContent = stats.total_habits;
  el("statDoneToday").textContent = stats.done_today_count;
  el("statBestStreak").textContent = stats.best_streak;
  el("statTotalCheckins").textContent = stats.total_checkins;
}

async function refreshAll() {
  await fetchHabits();
  await fetchStats();
}

// ---------------------------------------------------------------------
// Рендер
// ---------------------------------------------------------------------

function renderHabits() {
  const grid = el("habitsGrid");
  const emptyState = el("emptyState");

  if (habits.length === 0) {
    grid.innerHTML = "";
    emptyState.classList.remove("hidden");
    return;
  }
  emptyState.classList.add("hidden");

  grid.innerHTML = habits
    .map((habit) => {
      const rate = Math.min(habit.completion_rate, 100);
      return `
      <div class="habit-card" style="--accent-color:${habit.color}">
        <div class="habit-top">
          <div class="habit-title">
            <div class="habit-emoji">${habit.icon}</div>
            <div>
              <div class="habit-name">${escapeHtml(habit.name)}</div>
              <div class="habit-meta">с ${formatDate(habit.created_at)}</div>
            </div>
          </div>
          <div class="habit-actions">
            <button class="btn-icon" title="Редактировать" onclick="openEditModal(${habit.id})">✎</button>
            <button class="btn-icon" title="Удалить" onclick="deleteHabit(${habit.id})">🗑</button>
          </div>
        </div>

        <div class="habit-stats">
          <div class="habit-stat">
            <span class="value">🔥 ${habit.streak}</span>
            <span class="label">Стрик</span>
          </div>
          <div class="habit-stat">
            <span class="value">${habit.completion_rate}%</span>
            <span class="label">Выполнение</span>
          </div>
          <div class="habit-stat">
            <span class="value">${habit.total_checkins}</span>
            <span class="label">Всего</span>
          </div>
        </div>

        <div class="progress-bar">
          <div class="progress-fill" style="width:${rate}%"></div>
        </div>

        <button class="done-toggle ${habit.done_today ? "done" : ""}" onclick="toggleDone(${habit.id})">
          ${habit.done_today ? "✓ Сделано сегодня" : "Отметить выполненным"}
        </button>
      </div>
    `;
    })
    .join("");
}

function formatDate(isoDate) {
  const d = new Date(isoDate);
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------------------------------------------------------------------
// Отметка выполнения
// ---------------------------------------------------------------------

async function toggleDone(habitId) {
  // Отмечаем привычку выполненной сегодня.
  await fetch(`${API_BASE}/habits/${habitId}/checkins`, { method: "POST" });
  await refreshAll();
  showToast("Привычка отмечена ✓");
}

async function deleteHabit(habitId) {
  if (!confirm("Удалить привычку?")) return;
  await fetch(`${API_BASE}/habits/${habitId}`, { method: "DELETE" });
  await refreshAll();
  showToast("Привычка удалена");
}

// ---------------------------------------------------------------------
// Модалка создания / редактирования
// ---------------------------------------------------------------------

function renderPickers() {
  el("iconPicker").innerHTML = ICONS.map(
    (icon) => `<div class="icon-option ${icon === selectedIcon ? "selected" : ""}" data-icon="${icon}">${icon}</div>`
  ).join("");

  el("colorPicker").innerHTML = COLORS.map(
    (color) =>
      `<div class="color-option ${color === selectedColor ? "selected" : ""}" data-color="${color}" style="background:${color};color:${color}"></div>`
  ).join("");

  el("iconPicker").querySelectorAll(".icon-option").forEach((node) => {
    node.addEventListener("click", () => {
      selectedIcon = node.dataset.icon;
      renderPickers();
    });
  });

  el("colorPicker").querySelectorAll(".color-option").forEach((node) => {
    node.addEventListener("click", () => {
      selectedColor = node.dataset.color;
      renderPickers();
    });
  });
}

function openCreateModal() {
  el("modalTitle").textContent = "Новая привычка";
  el("habitNameInput").value = "";
  selectedIcon = ICONS[0];
  selectedColor = COLORS[0];
  renderPickers();
  el("modalOverlay").classList.remove("hidden");
  el("habitNameInput").focus();
}

function openEditModal(habitId) {
  const habit = habits.find((h) => h.id === habitId);
  if (!habit) return;

  editingHabitId = habitId;
  el("modalTitle").textContent = "Редактировать привычку";
  el("habitNameInput").value = habit.name;
  selectedIcon = habit.icon;
  selectedColor = habit.color;
  renderPickers();
  el("modalOverlay").classList.remove("hidden");
  el("habitNameInput").focus();
}

function closeModal() {
  el("modalOverlay").classList.add("hidden");
}

async function saveHabit() {
  const name = el("habitNameInput").value.trim();
  if (!name) {
    showToast("Введите название привычки");
    return;
  }

  const payload = { name, icon: selectedIcon, color: selectedColor };

  if (editingHabitId) {
    await fetch(`${API_BASE}/habits/${editingHabitId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showToast("Привычка обновлена");
  } else {
    await fetch(`${API_BASE}/habits`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    showToast("Привычка добавлена");
  }

  closeModal();
  await refreshAll();
}

// ---------------------------------------------------------------------
// Тосты
// ---------------------------------------------------------------------

let toastTimer = null;
function showToast(message) {
  const toast = el("toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add("hidden"), 2200);
}

// ---------------------------------------------------------------------
// Слушатели событий
// ---------------------------------------------------------------------

el("openCreateBtn").addEventListener("click", openCreateModal);
el("emptyCreateBtn").addEventListener("click", openCreateModal);
el("cancelBtn").addEventListener("click", () => {
  editingHabitId = null;
  closeModal();
});
el("saveHabitBtn").addEventListener("click", saveHabit);

el("modalOverlay").addEventListener("click", (e) => {
  if (e.target === el("modalOverlay")) {
    closeModal();
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

renderPickers();
refreshAll();
