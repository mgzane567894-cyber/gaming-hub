document.addEventListener("DOMContentLoaded", function() {
    loadGameDetails();
});

function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

function goBack() {
    window.history.back();
}

async function loadGameDetails() {
    const gameId = getQueryParam('id') || getQueryParam('game');
    const container = document.getElementById("detailContent");
    
    if (!container) return;

    if (!gameId) {
        container.innerHTML = `<div class="detail-loading" style="color:red;">❌ Game ID not found in URL!</div>`;
        return;
    }

    try {
        const response = await fetch('games.json');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (!data.games || !Array.isArray(data.games)) {
            throw new Error("Invalid JSON format: 'games' array not found.");
        }

        const games = data.games;
        const game = games.find(g => String(g.id) === String(gameId));

        if (!game) {
            container.innerHTML = `<div class="detail-loading" style="color:red;">❌ Game not found in database!</div>`;
            return;
        }

        document.title = `${game.name} - AKL Gaming HUB`;

        const icon = game.icon || game.image || "🎮";
        const iconHTML = isImageURL(icon) 
            ? `<img src="${escapeHTML(icon)}" alt="${escapeHTML(game.name)}" style="width:80px; height:80px; border-radius:16px; object-fit:cover;">` 
            : `<div style="font-size:50px;">${escapeHTML(icon)}</div>`;

        const rating = game.rating !== undefined && game.rating !== null ? Number(game.rating).toFixed(1) : "5.0";
        
        // ============================================
        // features ကို ကိုင်တွယ်ပါ
        // ============================================
        let featuresList = "";
        if (game.features) {
            let features = game.features;
            if (typeof features === 'string') {
                try {
                    if (features.trim().startsWith('[')) {
                        features = JSON.parse(features);
                    } else {
                        features = features.split(',').map(f => f.trim());
                    }
                } catch (e) {
                    features = features.split(',').map(f => f.trim());
                }
            }
            if (Array.isArray(features)) {
                featuresList = features.map(f => `<span>✨ ${escapeHTML(f)}</span>`).join("");
            }
        }
        
        // ============================================
        // screenshots ကို ကိုင်တွယ်ပါ
        // ============================================
        let screenshots = [];
        if (game.screenshots) {
            if (typeof game.screenshots === 'string') {
                try {
                    if (game.screenshots.trim().startsWith('[')) {
                        screenshots = JSON.parse(game.screenshots);
                    } else {
                        screenshots = game.screenshots.split(',').map(s => s.trim()).filter(s => s.length > 0);
                    }
                } catch (e) {
                    screenshots = game.screenshots.split(',').map(s => s.trim()).filter(s => s.length > 0);
                }
            } else if (Array.isArray(game.screenshots)) {
                screenshots = game.screenshots;
            }
        }
        
        console.log('Screenshots found:', screenshots.length);
        
        const screenshotsHTML = screenshots.length > 0 ? `
            <div style="margin-top: 20px;">
                <h3>📸 Screenshots</h3>
                <div style="display: flex; gap: 10px; overflow-x: auto; padding-bottom: 10px;">
                    ${screenshots.map(s => `
                        <img src="${escapeHTML(s)}" 
                             style="width: 200px; height: 120px; object-fit: cover; border-radius: 8px; flex-shrink:0;" 
                             loading="lazy" 
                             onerror="this.style.display='none'; this.parentElement.innerHTML='<div style=\\'width:200px; height:120px; display:flex; align-items:center; justify-content:center; background:#1a1a1a; border-radius:8px; color:#666; font-size:12px; flex-shrink:0;\\'>No image</div>'">
                    `).join("")}
                </div>
            </div>
        ` : "";

        // ============================================
        // Download URL ကို ကိုင်တွယ်ပါ (.bin ကို .apk ပြောင်းမယ်)
        // ============================================
        let downloadUrl = game.downloadUrl || game.downloadurl || "";
        
        // .bin နဲ့ဆုံးရင် .apk လို့ပြောင်းပါ
        if (downloadUrl.endsWith('.bin')) {
            downloadUrl = downloadUrl.replace(/\.bin$/, '.apk');
        }
        
        // ဖိုင်နာမည်ကို သန့်ရှင်းအောင်လုပ်ပါ
        let fileName = game.name || "game";
        fileName = fileName.replace(/[^a-zA-Z0-9]/g, '_') + ".apk";
        
        const obbLink = game.obb_link || game.obbLink || "";
        const playStoreUrl = game.playStoreUrl || game.playstoreurl || "";

        const obbButtonHTML = obbLink ? `
            <a href="${escapeHTML(obbLink)}" class="action-btn secondary" target="_blank" style="display:block; text-align:center; text-decoration:none; margin-top:10px; background:#00838f; color:#fff; padding:12px; border-radius:8px; font-weight:bold;">
                📦 Download OBB / Data File
            </a>
        ` : "";

        const playStoreHTML = playStoreUrl ? `
            <a href="${escapeHTML(playStoreUrl)}" class="action-btn secondary" target="_blank" style="display:block; text-align:center; text-decoration:none; margin-top:10px; background:#2a2a2a; color:#fff; padding:12px; border-radius:8px; font-weight:bold;">
                ▶️ Play Store
            </a>
        ` : "";

        container.innerHTML = `
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="display: flex; gap: 16px; align-items: center; background: #1e1e1e; padding: 20px; border-radius: 12px;">
                    ${iconHTML}
                    <div>
                        <h1 style="font-size: 22px; color: #fff; margin: 0 0 6px 0;">${escapeHTML(game.name)}</h1>
                        <div style="font-size: 14px; color: #aaa;">★ ${rating} • ${escapeHTML(String(game.platform || "").toUpperCase())} • ${escapeHTML(game.type || "Original")}</div>
                        <div style="font-size: 13px; color: #888; margin-top: 4px;">Version: ${escapeHTML(game.version || "1.0")} | Size: ${escapeHTML(game.size || "Unknown")}</div>
                    </div>
                </div>

                <div style="margin-top: 20px; background: #1e1e1e; padding: 20px; border-radius: 12px;">
                    <h3 style="margin-top: 0; color: #fff;">About Game</h3>
                    <p style="color: #ccc; line-height: 1.5; white-space: pre-line;">${escapeHTML(game.description || "No description available.")}</p>
                </div>

                ${featuresList ? `<div style="margin-top: 20px; display: flex; flex-wrap: wrap; gap: 8px;">${featuresList}</div>` : ""}

                ${screenshotsHTML}

                <div style="margin-top: 30px;">
                    ${downloadUrl ? `
                        <a href="${escapeHTML(downloadUrl)}" 
                           class="action-btn primary" 
                           target="_blank" 
                           download="${escapeHTML(fileName)}"
                           style="display:block; text-align:center; text-decoration:none; padding: 14px; font-size: 16px; font-weight: bold; background:#1a8cff; color:#fff; border-radius:10px;">
                            📥 Download APK (${escapeHTML(game.size || "File")})
                        </a>
                    ` : `<div style="text-align:center; color:#666;">Download link not available</div>`}
                    ${obbButtonHTML}
                    ${playStoreHTML}
                </div>
            </div>
        `;

    } catch (error) {
        console.error("Detail Load Error:", error);
        container.innerHTML = `<div class="detail-loading" style="color:red;">❌ Error loading game data.</div>`;
    }
}

function isImageURL(value) {
    return typeof value === "string" && /^https?:\/\//i.test(value);
}

function escapeHTML(value) {
    if (value === null || value === undefined) return "";
    return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}