const API_BASE = "http://localhost:5678/api";

let state = {
  page: 1,
  limit: 15,
  total: 0,
  mode: "list", // "list" or "search"
  lastSearch: null,
  data: []
};

const tbody = document.getElementById("recipes-body");
const pageInfo = document.getElementById("page-info");
const prevBtn = document.getElementById("prev-page");
const nextBtn = document.getElementById("next-page");
const limitSel = document.getElementById("limit");
const msgBox = document.getElementById("messages");

const fTitle = document.getElementById("filter-title");
const fCuisine = document.getElementById("filter-cuisine");
const fRating = document.getElementById("filter-rating");
const fTotal = document.getElementById("filter-total");
const fCalories = document.getElementById("filter-calories");
const btnSearch = document.getElementById("btn-search");
const btnClear = document.getElementById("btn-clear");

// Drawer
const drawer = document.getElementById("drawer");
const dClose = document.getElementById("drawer-close");
const dTitle = document.getElementById("drawer-title");
const dSub = document.getElementById("drawer-subtitle");
const dDesc = document.getElementById("d-description");
const dTotal = document.getElementById("d-total");
const dPrep = document.getElementById("d-prep");
const dCook = document.getElementById("d-cook");
const expandTimes = document.getElementById("expand-times");
const timesDetail = document.getElementById("times-detail");
const nutriBody = document.getElementById("nutri-body");

function showMessage(text) {
  msgBox.classList.remove("hidden");
  msgBox.textContent = text;
}
function clearMessage() {
  msgBox.classList.add("hidden");
  msgBox.textContent = "";
}

function renderStars(rating) {
  if (rating == null) return `<span class="rating">—</span>`;
  const full = Math.floor(rating);
  const half = rating - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return `<span class="rating">`
    + "★".repeat(full).split("").map(() => `<span class="star-full">★</span>`).join("")
    + (half ? `<span class="star-full star-half">★</span>` : "")
    + "☆".repeat(empty).split("").map(() => `<span class="star-empty">☆</span>`).join("")
    + `</span>`;
}

function openDrawer(item) {
  dTitle.textContent = item.title || "Untitled";
  dSub.textContent = item.cuisine || "";
  dDesc.textContent = item.description || "—";
  dTotal.textContent = item.total_time != null ? `${item.total_time} min` : "—";
  dPrep.textContent = item.prep_time != null ? `${item.prep_time} min` : "—";
  dCook.textContent = item.cook_time != null ? `${item.cook_time} min` : "—";
  timesDetail.classList.add("hidden");

  // Nutrition table
  const keys = [
    "calories","carbohydrateContent","cholesterolContent","fiberContent",
    "proteinContent","saturatedFatContent","sodiumContent","sugarContent","fatContent"
  ];
  nutriBody.innerHTML = "";
  keys.forEach(k => {
    const v = (item.nutrients && item.nutrients[k]) || "—";
    const tr = document.createElement("tr");
    tr.innerHTML = `<td style="color:#9ca3af">${k}</td><td>${v}</td>`;
    nutriBody.appendChild(tr);
  });

  drawer.classList.add("open");
}
dClose.onclick = () => drawer.classList.remove("open");
expandTimes.onclick = () => {
  const hidden = timesDetail.classList.contains("hidden");
  timesDetail.classList.toggle("hidden");
  expandTimes.textContent = hidden ? "▲" : "▼";
};

function renderTable(list) {
  tbody.innerHTML = "";
  if (!list || list.length === 0) {
    showMessage(state.mode === "search" ? "No results found." : "No data.");
    return;
  }
  clearMessage();

  list.forEach(item => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="title-cell" title="${item.title || ""}">${item.title || "—"}</td>
      <td>${item.cuisine || "—"}</td>
      <td>${renderStars(item.rating)}</td>
      <td>${item.total_time != null ? item.total_time + " min" : "—"}</td>
      <td>${item.serves || "—"}</td>
    `;
    tr.onclick = () => openDrawer(item);
    tbody.appendChild(tr);
  });
}

async function fetchList() {
  state.mode = "list";
  const url = new URL(`${API_BASE}/US_recipes`);
  url.searchParams.set("page", state.page);
  url.searchParams.set("limit", state.limit);
  const res = await fetch(url);
  const json = await res.json();
  state.total = json.total || 0;
  pageInfo.textContent = `Page ${json.page} • ${json.limit}/page • Total ${json.total}`;
  state.data = json.data || [];
  renderTable(state.data);
  prevBtn.disabled = state.page <= 1;
  nextBtn.disabled = state.page * state.limit >= state.total;
}

async function fetchSearch() {
  state.mode = "search";
  const url = new URL(`${API_BASE}/US_recipes/search`);
  const title = fTitle.value.trim();
  const cuisine = fCuisine.value.trim();
  const rating = fRating.value.trim();
  const total = fTotal.value.trim();
  const calories = fCalories.value.trim();

  if (title) url.searchParams.set("title", title);
  if (cuisine) url.searchParams.set("cuisine", cuisine);
  if (rating) url.searchParams.set("rating", rating);
  if (total) url.searchParams.set("total_time", total);
  if (calories) url.searchParams.set("calories", calories);

  state.lastSearch = url.toString(); // keep for refresh if needed
  const res = await fetch(url);
  const json = await res.json();
  // Search returns unpaginated list by spec, then we page on client (simple)
  const all = json.data || [];
  state.total = all.length;
  // client-side pagination
  const start = (state.page - 1) * state.limit;
  const slice = all.slice(start, start + state.limit);
  pageInfo.textContent = `Search • Page ${state.page} • ${state.limit}/page • Matches ${state.total}`;
  state.data = slice;
  renderTable(slice);
  prevBtn.disabled = state.page <= 1;
  nextBtn.disabled = start + state.limit >= state.total;
}

prevBtn.onclick = () => {
  if (state.page > 1) {
    state.page--;
    state.mode === "search" ? fetchSearch() : fetchList();
  }
};
nextBtn.onclick = () => {
  const maxPage = Math.ceil(state.total / state.limit);
  if (state.page < maxPage) {
    state.page++;
    state.mode === "search" ? fetchSearch() : fetchList();
  }
};
limitSel.onchange = () => {
  state.limit = parseInt(limitSel.value, 10);
  state.page = 1;
  state.mode === "search" ? fetchSearch() : fetchList();
};

btnSearch.onclick = () => {
  state.page = 1;
  fetchSearch();
};
btnClear.onclick = () => {
  fTitle.value = "";
  fCuisine.value = "";
  fRating.value = "";
  fTotal.value = "";
  fCalories.value = "";
  state.page = 1;
  fetchList();
};

// initialize
fetchList();
