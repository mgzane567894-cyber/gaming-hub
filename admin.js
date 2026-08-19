let editingGameId = null;

const SUPABASE_URL = 'https://olqnxhgrcixzzsyadlic.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_eSBSq4elZu2wW1BKzS38qQ_YoqdIrds';

if (!window.supabaseClient && window.supabase) {
    window.supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}

document.addEventListener("DOMContentLoaded", function() {
    const adminApp = document.getElementById("adminApp");
    if (adminApp) adminApp.classList.add("show");
    loadStatsAndGames();
});

async function fetchSupabaseGames() {
    try {
        if (!window.supabaseClient) throw new Error("Supabase client not initialized.");
        let { data, error } = await window.supabaseClient.from('games').select('*');
        if (error) throw error;
        return data || [];
    } catch (e) {
        console.error("Error fetching games:", e);
        return [];
    }
}

async function loadStatsAndGames() {
    await loadStats();
    await loadGames();
}

async function loadStats() {
    try {
        const games = await fetchSupabaseGames();
        const featured = games.filter(game => game.featured === true || game.featured === "true");
        document.getElementById("totalGames").textContent = games.length;
        document.getElementById("featuredGames").textContent = featured.length;
    } catch (error) {
        console.error("Stats Error:", error);
    }
}

async function loadGames() {
    const container = document.getElementById("adminGamesList");
    if (!container) return;

    try {
        const games = await fetchSupabaseGames();
        if (games.length === 0) {
            container.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding:20px; color:#666;">🎮 No games found in database.</div>`;
            await loadStats();
            return;
        }

        container.innerHTML = games.map(game => {
            const icon = game.icon || game.image || "🎮";
            const iconHTML = isImageURL(icon) 
                ? `<img src="${escapeHTML(icon)}" class="admin-game-icon-image" alt="${escapeHTML(game.name)}">` 
                : `<div class="admin-game-icon">${escapeHTML(icon)}</div>`;
            
            const rating = game.rating !== undefined && game.rating !== null ? Number(game.rating).toFixed(1) : "5.0";
            const hasObb = game.obb_link ? `<span style="font-size: 11px; background: #e0f7fa; color: #00838f; padding: 2px 6px; border-radius: 4px; margin-left: 4px;">📦 OBB</span>` : "";

            return `
                <div class="admin-game-item">
                    <div class="admin-game-info">
                        ${iconHTML}
                        <div class="admin-game-details">
                            <div class="admin-game-name" title="${escapeHTML(game.name || "Unnamed")}">${escapeHTML(game.name || "Unnamed")} ${hasObb}</div>
                            <div style="font-size: 12px; color: #888; margin-top: 4px;">★ ${rating} • ${escapeHTML(String(game.platform || "").toUpperCase())} • ${escapeHTML(game.type || "Original")}</div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 6px; margin-top: 8px;">
                        <button type="button" class="action-btn secondary" style="padding: 6px 10px; font-size: 12px; flex: 1;" onclick="editGame('${escapeHTML(String(game.id))}')">✏️ Edit</button>
                        <button type="button" class="action-btn danger" style="padding: 6px 10px; font-size: 12px; flex: 1;" onclick="deleteGame('${escapeHTML(String(game.id))}')">🗑️ Delete</button>
                    </div>
                </div>
            `;
        }).join("");
        await loadStats();
    } catch (error) {
        console.error("Error loading games:", error);
    }
}

function showAddForm() {
    const form = document.getElementById("gameForm");
    form.style.display = "block";
    document.getElementById("formTitle").textContent = "➕ Add New Game";
    document.getElementById("gameFormInputs").reset();
    document.getElementById("editId").value = "";
    document.getElementById("gameType").value = "Original";
    editingGameId = null;
    form.scrollIntoView({ behavior: "smooth" });
}

async function editGame(id) {
    try {
        const games = await fetchSupabaseGames();
        const game = games.find(g => String(g.id) === String(id));
        if (!game) return alert("❌ Game not found!");

        editingGameId = game.id;
        document.getElementById("gameForm").style.display = "block";
        document.getElementById("formTitle").textContent = "✏️ Edit Game";
        document.getElementById("editId").value = game.id;

        document.getElementById("gameName").value = game.name || "";
        document.getElementById("gamePlatform").value = (game.platform || "").toLowerCase();
        document.getElementById("gameType").value = game.type || "Original";
        document.getElementById("gameVersion").value = game.version || "";
        document.getElementById("gameSize").value = game.size || "";
        document.getElementById("gameIcon").value = game.icon || game.image || "";
        document.getElementById("gameDescription").value = game.description || "";
        document.getElementById("gameFeatures").value = Array.isArray(game.features) ? game.features.join(", ") : (game.features || "");
        document.getElementById("gameDownloadUrl").value = game.downloadUrl || "";
        document.getElementById("gameObbUrl").value = game.obb_link || "";
        document.getElementById("gamePlayStoreUrl").value = game.playStoreUrl || "";
        
        const screenshots = Array.isArray(game.screenshots) ? game.screenshots : [];
        document.getElementById("screenshot1").value = screenshots[0] || "";
        document.getElementById("screenshot2").value = screenshots[1] || "";
        document.getElementById("screenshot3").value = screenshots[2] || "";
        document.getElementById("screenshot4").value = screenshots[3] || "";
        document.getElementById("gameFeatured").checked = game.featured === true || game.featured === "true";

        document.getElementById("gameForm").scrollIntoView({ behavior: "smooth" });
    } catch (error) {
        console.error("Edit Error:", error);
    }
}

function cancelForm() {
    document.getElementById("gameForm").style.display = "none";
    document.getElementById("gameFormInputs").reset();
    editingGameId = null;
}

async function saveGame(event) {
    event.preventDefault();

    const id = document.getElementById("editId").value.trim();
    const name = document.getElementById("gameName").value.trim();
    const platform = document.getElementById("gamePlatform").value;
    const type = document.getElementById("gameType").value;
    const version = document.getElementById("gameVersion").value.trim() || "1.0.0";
    const size = document.getElementById("gameSize").value.trim() || "Unknown";
    const icon = document.getElementById("gameIcon").value.trim() || "🎮";
    const description = document.getElementById("gameDescription").value.trim() || "No description available.";
    
    const featuresInput = document.getElementById("gameFeatures").value;
    const features = featuresInput ? featuresInput.split(",").map(i => i.trim()).filter(Boolean) : [];
    const downloadUrl = document.getElementById("gameDownloadUrl").value.trim();
    const obb_link = document.getElementById("gameObbUrl").value.trim();
    const playStoreUrl = document.getElementById("gamePlayStoreUrl").value.trim();
    
    const screenshots = [
        document.getElementById("screenshot1")?.value.trim(),
        document.getElementById("screenshot2")?.value.trim(),
        document.getElementById("screenshot3")?.value.trim(),
        document.getElementById("screenshot4")?.value.trim()
    ].filter(Boolean);

    const featured = document.getElementById("gameFeatured")?.checked || false;

    if (!name || !platform || !downloadUrl) {
        alert("❌ Please fill in required fields (Name, Platform, Download URL).");
        return;
    }

    const gameData = {
        name,
        platform,
        type,
        version,
        size,
        icon,
        description,
        features,
        downloadUrl,
        obb_link,
        playStoreUrl,
        screenshots,
        featured,
        updatedAt: Date.now()
    };

    if (!id) {
        gameData.rating = 5.0;
        gameData.total_ratings = 0;
    }

    try {
        let response;
        if (id) {
            response = await window.supabaseClient.from('games').update(gameData).eq('id', id);
        } else {
            response = await window.supabaseClient.from('games').insert([gameData]);
        }

        if (response.error) throw response.error;

        alert(id ? "✅ Game updated successfully!" : "✅ Game added successfully!");
        cancelForm();
        await loadGames();
    } catch (error) {
        console.error("Save Error:", error);
        alert("❌ Error saving game: " + (error.message || JSON.stringify(error)));
    }
}

async function deleteGame(id) {
    if (!confirm("Are you sure you want to delete this game?")) return;
    try {
        let { error } = await window.supabaseClient.from('games').delete().eq('id', id);
        if (error) throw error;
        alert("🗑️ Game deleted successfully!");
        await loadGames();
    } catch (error) {
        console.error("Delete Error:", error);
        alert("❌ Could not delete game.");
    }
}

function logout() {
    alert("AKL Gaming HUB Admin Panel (Supabase Connected)");
}

function isImageURL(value) {
    return typeof value === "string" && /^https?:\/\//i.test(value);
}

function escapeHTML(value) {
    if (value === null || value === undefined) return "";
    return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

window.showAddForm = showAddForm;
window.editGame = editGame;
window.cancelForm = cancelForm;
window.saveGame = saveGame;
window.deleteGame = deleteGame;
window.logout = logout;
window.loadGames = loadGames;
