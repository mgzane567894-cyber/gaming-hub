let games = [];

// ============================================
// JSON ကနေ ဂိမ်းဒေတာတွေ Load လုပ်မယ်
// ============================================
async function loadGamesFromJson() {
    try {
        const response = await fetch('games.json');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // data.games က array ဖြစ်ဖို့လိုတယ်
        if (!data.games || !Array.isArray(data.games)) {
            throw new Error("Invalid JSON format: 'games' array not found.");
        }

        console.log(`✅ Loaded ${data.games.length} games from games.json`);
        games = data.games || [];
        
        renderFeaturedGames();
        renderGames();
        renderCategories();
    } catch (error) {
        console.error("❌ Load games error:", error);
        showError();
    }
}

// ============================================
// Featured ဂိမ်းတွေကို ပြမယ်
// ============================================
function renderFeaturedGames() {
    const container = document.getElementById("featuredGames");
    if (!container) return;

    const featured = games.filter(game => game.featured === true || game.featured === "true");

    if (featured.length === 0) {
        container.innerHTML = `<div class="empty-featured">No featured games yet.</div>`;
        return;
    }

    container.innerHTML = featured.map(game => createGameCard(game, true)).join("");
}

// ============================================
// ဂိမ်းအားလုံးကို ပြမယ်
// ============================================
function renderGames(list = games) {
    const container = document.getElementById("gamesList");
    if (!container) return;

    if (list.length === 0) {
        container.innerHTML = `<div class="no-games">🎮 No games available.</div>`;
        return;
    }

    container.innerHTML = list.map(game => createGameCard(game, false)).join("");
}

// ============================================
// ဂိမ်းတစ်ခုချင်းစီအတွက် Card ဖန်တီးမယ်
// ============================================
function createGameCard(game, featured = false) {
    const icon = game.icon || game.image || "🎮";
    let imageHTML;

    if (isImageURL(icon)) {
        imageHTML = `<img src="${escapeHTML(icon)}" alt="${escapeHTML(game.name || "Game")}" class="game-image" loading="lazy" onerror="this.style.display='none'; this.parentElement.innerHTML='🎮';">`;
    } else {
        imageHTML = `<div class="game-icon-placeholder">${escapeHTML(icon)}</div>`;
    }

    const gameType = String(game.type || "Original").trim();
    let typeClass = "original";
    if (gameType.toLowerCase() === "mod") typeClass = "mod";
    else if (gameType.toLowerCase() === "full") typeClass = "full";

    const gameId = String(game.id || "");
    const gameRating = game.rating !== undefined && game.rating !== null ? Number(game.rating).toFixed(1) : "5.0";
    const totalRatings = game.total_ratings || game.totalRatings || 0;

    return `
        <div class="game-card ${featured ? "featured-card" : ""}" data-game-id="${escapeHTML(gameId)}" onclick="openGameFromCard(this)" role="button" tabindex="0">
            <div class="game-card-image">${imageHTML}</div>
            <div class="game-card-content">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                    <div class="game-type-badge ${typeClass}" style="margin: 0;">${escapeHTML(gameType)}</div>
                    <div style="font-size: 11px; color: #ffc107; font-weight: bold;">★ ${gameRating} <span style="color: #888; font-size: 9px;">(${totalRatings})</span></div>
                </div>
                <h3 class="game-name">${escapeHTML(game.name || "Unknown Game")}</h3>
                <div class="game-meta">
                    <span>${escapeHTML(game.platform || "")}</span>
                    <span>${escapeHTML(game.size || "")}</span>
                </div>
            </div>
        </div>
    `;
}

// ============================================
// ဂိမ်းအသေးစိတ်စာမျက်နှာကို ဖွင့်မယ်
// ============================================
function openGameFromCard(card) {
    if (!card) return;
    const gameId = card.getAttribute("data-game-id");
    if (!gameId) return;
    openGame(gameId);
}

function openGame(id) {
    if (!id || String(id).trim() === "") return;
    window.location.assign("./detail.html?id=" + encodeURIComponent(String(id).trim()));
}

// ============================================
// Category (Platform) တွေကို ပြမယ်
// ============================================
function renderCategories() {
    const container = document.getElementById("categoriesList");
    if (!container) return;

    const platforms = [...new Set(games.map(game => game.platform).filter(Boolean))];
    if (platforms.length === 0) {
        container.innerHTML = "<span>No categories</span>";
        return;
    }

    container.innerHTML = platforms.map(platform => {
        const safePlatform = encodeURIComponent(String(platform));
        return `<button type="button" class="category-btn" onclick="filterPlatform('${safePlatform}')">🎮 ${escapeHTML(String(platform).toUpperCase())}</button>`;
    }).join("");
}

// ============================================
// Platform အလိုက် Filter လုပ်မယ်
// ============================================
function filterPlatform(platform) {
    const decoded = decodeURIComponent(platform);
    const filtered = games.filter(game => String(game.platform || "").toLowerCase() === String(decoded).toLowerCase());
    renderGames(filtered);
}

// ============================================
// Search လုပ်မယ်
// ============================================
function setupSearch() {
    const input = document.getElementById("searchInput");
    if (!input) return;

    input.addEventListener("input", () => {
        const query = input.value.toLowerCase().trim();
        if (!query) {
            renderGames();
            return;
        }
        const filtered = games.filter(game =>
            (game.name || "").toLowerCase().includes(query) ||
            (game.platform || "").toLowerCase().includes(query) ||
            (game.type || "").toLowerCase().includes(query) ||
            (game.description || "").toLowerCase().includes(query)
        );
        renderGames(filtered);
    });
}

// ============================================
// Utility Functions
// ============================================
function escapeHTML(value) {
    if (value === null || value === undefined) return "";
    return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function isImageURL(value) {
    if (typeof value !== "string") return false;
    return /^https?:\/\//i.test(value);
}

function showError() {
    const container = document.getElementById("gamesList");
    if (!container) return;
    container.innerHTML = `<div class="firebase-error" style="text-align:center; padding:20px; color:#ff5252;">❌<br><br>ဂိမ်းဒေတာ မရှိပါ။<br>games.json ဖိုင်ကို စစ်ဆေးပေးပါ။<br><small style="color:#888;">Error: JSON မှာ ဂိမ်းတွေ မတွေ့ပါ</small></div>`;
}

// ============================================
// Navigation
// ============================================
function setupNavigation() {
    const buttons = document.querySelectorAll(".nav-item");
    buttons.forEach(button => {
        button.addEventListener("click", () => {
            buttons.forEach(item => item.classList.remove("active"));
            button.classList.add("active");
            const page = button.dataset.page;
            if (page === "home") {
                window.location.href = "index.html";
                return;
            }
            if (page === "categories") {
                const section = document.querySelector(".categories-section");
                if (section) section.scrollIntoView({ behavior: "smooth" });
                return;
            }
        });
    });
}

function goHomePage() {
    window.location.href = "index.html";
}

function goCategoriesPage() {
    const section = document.querySelector(".categories-section");
    if (section) section.scrollIntoView({ behavior: "smooth" });
}

// ============================================
// DOM Ready
// ============================================
document.addEventListener("DOMContentLoaded", () => {
    setTimeout(() => {
        const splash = document.getElementById("splashScreen");
        const main = document.getElementById("mainApp");
        if (splash) splash.style.display = "none";
        if (main) main.style.display = "block";
    }, 1000);

    setupSearch();
    setupNavigation();
    loadGamesFromJson();
});

window.addEventListener("pageshow", (event) => {
    if (event.persisted || (window.performance && window.performance.getEntriesByType("navigation")[0]?.type === "back_forward")) {
        loadGamesFromJson();
    }
});

// ============================================
// Global Functions
// ============================================
window.openGame = openGame;
window.openGameFromCard = openGameFromCard;
window.filterPlatform = filterPlatform;
window.goHomePage = goHomePage;
window.goCategoriesPage = goCategoriesPage;