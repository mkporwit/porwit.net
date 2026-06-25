/**
 * JobTracker SPA — Dark Command Center
 * Vanilla JS single-page application.
 */

const API = window.APP_CONFIG?.API_URL || "";

// --- Monitor Filter State ---

const monitorFilters = {
    hidePoorMatch: JSON.parse(localStorage.getItem("jt_hidePoorMatch") ?? "true"),
    hideApplied: JSON.parse(localStorage.getItem("jt_hideApplied") ?? "true"),
};

function toggleFilter(key) {
    monitorFilters[key] = !monitorFilters[key];
    localStorage.setItem(`jt_${key}`, JSON.stringify(monitorFilters[key]));
    render();
}

// --- Auth State ---

function getToken() {
    return localStorage.getItem("jt_token");
}

function setToken(token) {
    localStorage.setItem("jt_token", token);
}

function clearToken() {
    localStorage.removeItem("jt_token");
}

function isLoggedIn() {
    return !!getToken();
}

// --- API Client ---

async function api(path, options = {}) {
    const url = `${API}${path}`;
    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };
    const token = getToken();
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    const resp = await fetch(url, { ...options, headers });
    if (resp.status === 401) {
        // Had a token → session expired/invalid: kick back to login.
        // No token (e.g. the login request itself) → let the caller show
        // the server's error instead of wiping the form mid-submit.
        if (token) {
            clearToken();
            render();
            throw new Error("Unauthorized");
        }
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.error || "Unauthorized");
    }
    const data = await resp.json();
    if (!resp.ok) {
        throw new Error(data.error || `HTTP ${resp.status}`);
    }
    return data;
}

// --- Router ---

function getRoute() {
    return window.location.hash.slice(1) || "/";
}

function navigate(path) {
    window.location.hash = path;
}

// --- Toast System ---

function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const colors = {
        success: "border-accent-emerald",
        error: "border-accent-rose",
        info: "border-accent-cyan",
        warning: "border-accent-amber",
    };

    const toast = document.createElement("div");
    toast.className = `toast bg-surface border border-slate-700 ${colors[type] || colors.info} border-l-4 px-4 py-3 rounded shadow-lg max-w-sm text-sm text-slate-200`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("toast-exit");
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- Render ---

async function render() {
    const app = document.getElementById("app");

    if (!isLoggedIn()) {
        app.innerHTML = renderLogin();
        return;
    }

    const route = getRoute();
    const nav = renderNav(route);

    if (route === "/" || route === "/dashboard") {
        app.innerHTML = nav + renderLoading("Dashboard");
        const [stats, monitor] = await Promise.all([
            api("/api/stats"),
            api("/api/monitor/results?status=new"),
        ]);
        app.innerHTML = nav + renderDashboard(stats, monitor);
    } else if (route === "/applications") {
        app.innerHTML = nav + renderLoading("Applications");
        const data = await api("/api/applications?limit=500");
        app.innerHTML = nav + renderApplications(data);
    } else if (route === "/monitor") {
        app.innerHTML = nav + renderLoading("Monitor");
        const [results, companies] = await Promise.all([
            api("/api/monitor/results"),
            api("/api/monitor/companies"),
        ]);
        app.innerHTML = nav + renderMonitor(results, companies);
    } else {
        app.innerHTML = nav + `<div class="p-8"><p class="text-slate-600">Page not found</p></div>`;
    }
}

// --- Components ---

function renderNav(activeRoute) {
    const links = [
        { path: "/", label: "Dashboard" },
        { path: "/applications", label: "Applications" },
        { path: "/monitor", label: "Monitor" },
    ];
    const linkHtml = links.map(l => {
        const active = activeRoute === l.path || (l.path !== "/" && activeRoute.startsWith(l.path));
        const cls = active
            ? "text-cyan-400 border-b-2 border-cyan-400 px-3 py-2 text-sm font-medium tracking-wide"
            : "text-slate-500 hover:text-slate-300 px-3 py-2 text-sm font-medium tracking-wide transition-colors";
        return `<a href="#${l.path}" class="${cls}">${l.label}</a>`;
    }).join("");

    return `
    <nav class="bg-[#0a0f1a] border-b border-cyan-900/30">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-14">
                <div class="flex items-center space-x-6">
                    <span class="text-cyan-400 font-bold text-sm tracking-[0.2em] uppercase">JOBTRACKER</span>
                    <div class="flex items-center space-x-1">
                        ${linkHtml}
                    </div>
                </div>
                <button onclick="clearToken(); render();" class="text-slate-600 hover:text-slate-400 text-xs uppercase tracking-wider transition-colors">
                    Logout
                </button>
            </div>
        </div>
    </nav>`;
}

function renderLogin() {
    return `
    <div class="flex items-center justify-center min-h-screen bg-gradient-to-br from-[#060910] via-[#0a1020] to-[#060910]">
        <div class="bg-surface border border-cyan-500/20 rounded-lg shadow-2xl shadow-cyan-900/10 p-8 w-full max-w-sm animate-in">
            <div class="text-center mb-8">
                <h1 class="font-heading text-3xl font-bold text-white tracking-wide">JOBTRACKER</h1>
                <div class="h-0.5 w-12 bg-cyan-400 mx-auto mt-3 rounded-full"></div>
            </div>
            <form id="login-form" onsubmit="handleLogin(event)">
                <div class="mb-4">
                    <label class="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">Username</label>
                    <input type="text" name="username" required
                        class="w-full px-3 py-2.5 rounded-md text-sm">
                </div>
                <div class="mb-6">
                    <label class="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">Password</label>
                    <input type="password" name="password" required
                        class="w-full px-3 py-2.5 rounded-md text-sm">
                </div>
                <div id="login-error" class="text-accent-rose text-sm mb-4 hidden"></div>
                <button type="submit"
                    class="w-full bg-cyan-500 hover:bg-cyan-400 text-body font-bold py-2.5 px-4 rounded-md text-sm uppercase tracking-wider transition-colors">
                    Sign In
                </button>
            </form>
        </div>
    </div>`;
}

async function handleLogin(e) {
    e.preventDefault();
    const form = e.target;
    const username = form.username.value;
    const password = form.password.value;
    const errorEl = document.getElementById("login-error");
    try {
        const data = await api("/api/auth/login", {
            method: "POST",
            body: JSON.stringify({ username, password }),
        });
        setToken(data.token);
        render();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.classList.remove("hidden");
    }
}

function renderLoading(section) {
    return `
    <div class="flex items-center justify-center py-24">
        <div class="text-center">
            <div class="inline-block w-5 h-5 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin mb-3"></div>
            <p class="text-slate-600 text-sm uppercase tracking-wider">Loading ${section}</p>
        </div>
    </div>`;
}

function renderDashboard(stats, monitor) {
    const newJobs = monitor.jobs || [];

    const statCards = [
        { label: "Total Applications", value: stats.total_applications, color: "bg-cyan-400" },
        { label: "This Month", value: stats.this_month, color: "bg-accent-amber" },
        { label: "Interview Rate", value: `${(stats.interview_rate * 100).toFixed(1)}%`, color: "bg-accent-emerald" },
        { label: "Active Matches", value: stats.monitor.active_matches, color: "bg-purple-400" },
    ];

    const byStatus = stats.by_status || {};
    const statusTotal = Object.values(byStatus).reduce((a, b) => a + b, 0) || 1;
    const statusColors = {
        applied: "#3b82f6",
        interview: "#34d399", screen: "#34d399", recruiter: "#34d399",
        offer: "#22d3ee",
        rejected: "#f43f5e",
        withdrawn: "#64748b",
        "hiring freeze": "#fbbf24",
    };

    function getStatusBarColor(status) {
        const s = status.toLowerCase();
        for (const [key, color] of Object.entries(statusColors)) {
            if (s.includes(key)) return color;
        }
        return "#475569";
    }

    return `
    <div class="max-w-7xl mx-auto px-4 py-8">
        <h1 class="font-heading text-2xl font-bold text-white mb-6 animate-in">Dashboard</h1>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            ${statCards.map((c, i) => `
            <div class="bg-surface border border-slate-800 rounded-lg p-4 card-glow animate-in stagger-${i + 1} flex items-start gap-3">
                <div class="${c.color} w-1 h-10 rounded-full flex-shrink-0 mt-0.5"></div>
                <div>
                    <p class="text-2xl font-bold text-white">${c.value}</p>
                    <p class="text-xs text-slate-500 uppercase tracking-wider mt-0.5">${c.label}</p>
                </div>
            </div>`).join("")}
        </div>

        ${newJobs.length > 0 ? `
        <div class="bg-surface border border-slate-800 rounded-lg mb-8 animate-in">
            <div class="px-4 py-3 border-b border-slate-800">
                <h2 class="text-sm font-bold text-white uppercase tracking-wider">New Roles Found</h2>
            </div>
            <ul>
                ${newJobs.map((j, i) => `
                <li class="px-4 py-3 border-l-2 border-cyan-400/40 ml-4 flex items-center justify-between hover:bg-surface-light transition-colors ${i < newJobs.length - 1 ? 'border-b border-b-slate-800/50' : ''}">
                    <div>
                        <p class="text-sm font-medium text-white">${esc(j.title)}</p>
                        <p class="text-xs text-slate-500">${esc(j.company)} &middot; ${esc(j.location)} ${flagEmoji(j.location_flag)}</p>
                    </div>
                    <a href="${esc(j.url)}" target="_blank" class="text-cyan-400 hover:text-cyan-300 text-sm transition-colors">&rarr;</a>
                </li>`).join("")}
            </ul>
        </div>` : ""}

        <div class="bg-surface border border-slate-800 rounded-lg animate-in">
            <div class="px-4 py-3 border-b border-slate-800">
                <h2 class="text-sm font-bold text-white uppercase tracking-wider">Status Breakdown</h2>
            </div>
            <div class="p-4">
                <div class="flex rounded-full overflow-hidden h-2.5 mb-4 bg-slate-800">
                    ${Object.entries(byStatus).sort((a,b) => b[1]-a[1]).map(([status, count]) =>
                        `<div class="status-bar-segment h-full" style="width:${(count / statusTotal * 100).toFixed(1)}%;background:${getStatusBarColor(status)}" title="${esc(status)}: ${count}"></div>`
                    ).join("")}
                </div>
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    ${Object.entries(byStatus).sort((a,b) => b[1]-a[1]).map(([status, count]) =>
                        `<div class="flex items-center gap-2 text-sm">
                            <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" style="background:${getStatusBarColor(status)}"></span>
                            <span class="text-slate-400">${esc(status)}</span>
                            <span class="text-white font-medium ml-auto">${count}</span>
                        </div>`
                    ).join("")}
                </div>
            </div>
        </div>
    </div>`;
}

function renderApplications(data) {
    const apps = data.applications || [];
    return `
    <div class="max-w-7xl mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-6 animate-in">
            <h1 class="font-heading text-2xl font-bold text-white">Applications <span class="text-slate-500 text-lg font-mono">(${data.count})</span></h1>
        </div>
        <div class="bg-surface border border-slate-800 rounded-lg overflow-x-auto animate-in stagger-1">
            <table class="min-w-full">
                <thead>
                    <tr class="border-b border-slate-800">
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Date</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Company</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Role</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Level</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Source</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Link</th>
                    </tr>
                </thead>
                <tbody>
                    ${apps.map(a => `
                    <tr class="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                        <td class="px-4 py-2.5 text-sm text-slate-400 whitespace-nowrap tabular-nums">${esc(a.date || "")}</td>
                        <td class="px-4 py-2.5 text-sm text-white">${esc(a.company || "")}</td>
                        <td class="px-4 py-2.5 text-sm text-slate-200">${esc(a.role || "")}</td>
                        <td class="px-4 py-2.5 text-sm text-slate-500">${esc(a.level || "")}</td>
                        <td class="px-4 py-2.5 text-sm">
                            <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${statusColor(a.status)}">${esc(a.status || "")}</span>
                        </td>
                        <td class="px-4 py-2.5 text-sm text-slate-500">${esc(a.source || "")}</td>
                        <td class="px-4 py-2.5 text-sm">${a.link ? `<a href="${esc(a.link)}" target="_blank" class="text-cyan-400 hover:text-cyan-300 transition-colors">&rarr;</a>` : ""}</td>
                    </tr>`).join("")}
                </tbody>
            </table>
        </div>
    </div>`;
}

function renderMonitor(results, companiesData) {
    const jobs = results.jobs || [];
    const companies = companiesData.companies || [];

    const hidePoorMatch = monitorFilters.hidePoorMatch;
    const hideApplied = monitorFilters.hideApplied;

    const visibleJobs = jobs.filter(j => {
        if (hidePoorMatch && j.status === "poor_match") return false;
        if (hideApplied && (j.already_applied || j.status === "applied")) return false;
        return true;
    });
    const hiddenCount = jobs.length - visibleJobs.length;

    const bySector = {};
    visibleJobs.forEach(j => {
        const s = j.sector || "Other";
        if (!bySector[s]) bySector[s] = [];
        bySector[s].push(j);
    });

    const sectorColors = ["cyan-400", "accent-emerald", "purple-400", "accent-amber", "blue-400", "accent-rose"];
    const sectorEntries = Object.entries(bySector);

    return `
    <div class="max-w-7xl mx-auto px-4 py-8">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-6 animate-in">
            <h1 class="font-heading text-2xl font-bold text-white">Monitor</h1>
            <div class="flex items-center gap-3">
                <span class="text-xs text-slate-600 uppercase tracking-wider">Last scan: ${timeAgo(results.last_scan)}</span>
                <button onclick="triggerScan()" class="bg-cyan-500 hover:bg-cyan-400 text-body font-bold px-3 py-1.5 rounded text-xs uppercase tracking-wider transition-colors">Scan Now</button>
            </div>
        </div>

        <div class="flex items-center gap-5 mb-6 animate-in stagger-1">
            <label class="inline-flex items-center gap-2 text-sm text-slate-400 cursor-pointer select-none">
                <input type="checkbox" ${hidePoorMatch ? "checked" : ""} onchange="toggleFilter('hidePoorMatch')">
                <span>Hide poor match${hidePoorMatch ? ` <span class="text-slate-600">(${jobs.filter(j => j.status === "poor_match").length})</span>` : ""}</span>
            </label>
            <label class="inline-flex items-center gap-2 text-sm text-slate-400 cursor-pointer select-none">
                <input type="checkbox" ${hideApplied ? "checked" : ""} onchange="toggleFilter('hideApplied')">
                <span>Hide applied${hideApplied ? ` <span class="text-slate-600">(${jobs.filter(j => j.already_applied || j.status === "applied").length})</span>` : ""}</span>
            </label>
            ${hiddenCount > 0 ? `<span class="text-xs text-slate-600">${hiddenCount} hidden</span>` : ""}
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <div class="bg-surface border border-slate-800 rounded-lg p-4 card-glow animate-in stagger-1 flex items-start gap-3">
                <div class="bg-cyan-400 w-1 h-10 rounded-full flex-shrink-0 mt-0.5"></div>
                <div>
                    <p class="text-2xl font-bold text-white">${results.total_active}</p>
                    <p class="text-xs text-slate-500 uppercase tracking-wider mt-0.5">Active Matches</p>
                </div>
            </div>
            <div class="bg-surface border border-slate-800 rounded-lg p-4 card-glow animate-in stagger-2 flex items-start gap-3">
                <div class="bg-accent-emerald w-1 h-10 rounded-full flex-shrink-0 mt-0.5"></div>
                <div>
                    <p class="text-2xl font-bold text-accent-emerald">${results.new_since_last}</p>
                    <p class="text-xs text-slate-500 uppercase tracking-wider mt-0.5">New Since Last Scan</p>
                </div>
            </div>
            <div class="bg-surface border border-slate-800 rounded-lg p-4 card-glow animate-in stagger-3 flex items-start gap-3">
                <div class="bg-purple-400 w-1 h-10 rounded-full flex-shrink-0 mt-0.5"></div>
                <div>
                    <p class="text-2xl font-bold text-white">${companies.length}</p>
                    <p class="text-xs text-slate-500 uppercase tracking-wider mt-0.5">Companies Tracked</p>
                </div>
            </div>
        </div>

        ${sectorEntries.map(([sector, sectorJobs], si) => `
        <div class="bg-surface border border-slate-800 rounded-lg mb-5 animate-in card-glow">
            <div class="px-4 py-3 border-b border-slate-800 flex items-center gap-2">
                <div class="bg-${sectorColors[si % sectorColors.length]} w-1 h-4 rounded-full"></div>
                <h2 class="text-sm font-bold text-white uppercase tracking-wider">${esc(sector)}</h2>
                <span class="text-xs text-slate-600 ml-1">${sectorJobs.length}</span>
            </div>
            <ul>
                ${sectorJobs.map((j, ji) => `
                <li class="px-4 py-3 hover:bg-surface-light transition-colors ${ji < sectorJobs.length - 1 ? 'border-b border-slate-800/50' : ''}">
                    <div class="flex items-center justify-between gap-4">
                        <div class="min-w-0">
                            <p class="text-sm font-medium text-white truncate">${esc(j.title)}</p>
                            <p class="text-xs text-slate-500 mt-0.5">
                                ${esc(j.company)}
                                &middot; ${esc(j.location)} ${flagEmoji(j.location_flag)}
                                &middot; ${esc(j.first_seen || "")}
                                ${j.already_applied ? '<span class="ml-2 inline-flex px-1.5 py-0.5 text-[10px] font-medium rounded bg-accent-amber/15 text-accent-amber">Applied</span>' : ""}
                                ${j.applied_at_company ? '<span class="ml-2 inline-flex px-1.5 py-0.5 text-[10px] font-medium rounded bg-slate-700/50 text-slate-400">At company</span>' : ""}
                            </p>
                        </div>
                        <div class="flex items-center gap-2 flex-shrink-0">
                            <span class="inline-flex px-2 py-0.5 text-[10px] font-medium rounded-full ${jobStatusColor(j.status)}">${esc(j.status || "")}</span>
                            ${j.status !== "poor_match" ? `<button onclick="markJob('${esc(j.sk)}', 'poor_match')" class="text-accent-amber/70 hover:text-accent-amber text-xs px-1.5 py-0.5 border border-accent-amber/30 rounded hover:bg-accent-amber/10 transition-colors" title="Poor match">Skip</button>` : ""}
                            <a href="${esc(j.url)}" target="_blank" class="text-cyan-400 hover:text-cyan-300 text-sm transition-colors">&rarr;</a>
                        </div>
                    </div>
                </li>`).join("")}
            </ul>
        </div>`).join("")}
    </div>`;
}

async function markJob(jobHash, status) {
    try {
        await api(`/api/monitor/jobs/${jobHash}`, {
            method: "PATCH",
            body: JSON.stringify({ status }),
        });
        showToast("Job marked as " + status, "success");
        render();
    } catch (err) {
        showToast("Error: " + err.message, "error");
    }
}

async function triggerScan() {
    try {
        await api("/api/monitor/scan", { method: "POST" });
        showToast("Scan triggered! Refresh in a minute to see results.", "info");
    } catch (err) {
        showToast("Error: " + err.message, "error");
    }
}

// --- Helpers ---

function esc(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function timeAgo(isoString) {
    if (!isoString) return "Never";
    const date = new Date(isoString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    if (seconds < 60) return "just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
}

function flagEmoji(flag) {
    if (flag === "good") return '<span title="Good location" class="text-accent-emerald">&#10003;</span>';
    if (flag === "bad") return '<span title="Bad location" class="text-accent-rose">&#10007;</span>';
    return '<span title="Unknown location" class="text-slate-600">?</span>';
}

function statusColor(status) {
    if (!status) return "bg-slate-700/50 text-slate-400";
    const s = status.toLowerCase();
    if (s === "applied") return "bg-blue-500/15 text-blue-400";
    if (s.includes("interview") || s.includes("screen") || s.includes("recruiter")) return "bg-emerald-500/15 text-accent-emerald";
    if (s === "offer") return "bg-cyan-500/15 text-cyan-400";
    if (s === "rejected") return "bg-rose-500/15 text-accent-rose";
    if (s === "withdrawn") return "bg-slate-700/50 text-slate-400";
    if (s === "hiring freeze") return "bg-amber-500/15 text-accent-amber";
    return "bg-slate-700/50 text-slate-400";
}

function jobStatusColor(status) {
    if (!status) return "bg-slate-700/50 text-slate-400";
    if (status === "new") return "bg-emerald-500/15 text-accent-emerald";
    if (status === "reviewed") return "bg-blue-500/15 text-blue-400";
    if (status === "applied") return "bg-cyan-500/15 text-cyan-400";
    if (status === "skipped") return "bg-slate-700/50 text-slate-400";
    if (status === "poor_match") return "bg-amber-500/15 text-accent-amber";
    if (status === "gone") return "bg-rose-500/15 text-accent-rose";
    return "bg-slate-700/50 text-slate-400";
}

// --- Init ---

window.addEventListener("hashchange", render);
render();
