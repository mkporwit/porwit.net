/**
 * JobTracker SPA
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
        clearToken();
        render();
        throw new Error("Unauthorized");
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
        app.innerHTML = nav + `<div class="p-8"><p class="text-gray-500">Page not found</p></div>`;
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
            ? "bg-indigo-700 text-white px-3 py-2 rounded-md text-sm font-medium"
            : "text-indigo-100 hover:bg-indigo-500 px-3 py-2 rounded-md text-sm font-medium";
        return `<a href="#${l.path}" class="${cls}">${l.label}</a>`;
    }).join("");

    return `
    <nav class="bg-indigo-600 shadow">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center space-x-4">
                    <span class="text-white font-bold text-lg">JobTracker</span>
                    ${linkHtml}
                </div>
                <button onclick="clearToken(); render();" class="text-indigo-200 hover:text-white text-sm">
                    Logout
                </button>
            </div>
        </div>
    </nav>`;
}

function renderLogin() {
    return `
    <div class="flex items-center justify-center min-h-screen bg-gray-50">
        <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-sm">
            <h1 class="text-2xl font-bold text-gray-900 mb-6 text-center">Job Tracker</h1>
            <form id="login-form" onsubmit="handleLogin(event)">
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
                    <input type="text" name="username" required
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500">
                </div>
                <div class="mb-6">
                    <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input type="password" name="password" required
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500">
                </div>
                <div id="login-error" class="text-red-600 text-sm mb-4 hidden"></div>
                <button type="submit"
                    class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 font-medium">
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
    return `<div class="p-8"><p class="text-gray-500">Loading ${section}...</p></div>`;
}

function renderDashboard(stats, monitor) {
    const newJobs = monitor.jobs || [];
    return `
    <div class="max-w-7xl mx-auto px-4 py-8">
        <h1 class="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="bg-white rounded-lg shadow p-4">
                <p class="text-sm text-gray-500">Total Applications</p>
                <p class="text-3xl font-bold text-gray-900">${stats.total_applications}</p>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
                <p class="text-sm text-gray-500">This Month</p>
                <p class="text-3xl font-bold text-gray-900">${stats.this_month}</p>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
                <p class="text-sm text-gray-500">Interview Rate</p>
                <p class="text-3xl font-bold text-gray-900">${(stats.interview_rate * 100).toFixed(1)}%</p>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
                <p class="text-sm text-gray-500">Active Monitor Matches</p>
                <p class="text-3xl font-bold text-gray-900">${stats.monitor.active_matches}</p>
            </div>
        </div>

        ${newJobs.length > 0 ? `
        <div class="bg-white rounded-lg shadow mb-8">
            <div class="px-4 py-3 border-b border-gray-200">
                <h2 class="text-lg font-semibold text-gray-900">New Roles Found</h2>
            </div>
            <ul class="divide-y divide-gray-200">
                ${newJobs.map(j => `
                <li class="px-4 py-3 flex items-center justify-between">
                    <div>
                        <p class="font-medium text-gray-900">${esc(j.title)}</p>
                        <p class="text-sm text-gray-500">${esc(j.company)} &middot; ${esc(j.location)} ${flagEmoji(j.location_flag)}</p>
                    </div>
                    <a href="${esc(j.url)}" target="_blank" class="text-indigo-600 hover:underline text-sm">View</a>
                </li>`).join("")}
            </ul>
        </div>` : ""}

        <div class="bg-white rounded-lg shadow">
            <div class="px-4 py-3 border-b border-gray-200">
                <h2 class="text-lg font-semibold text-gray-900">Status Breakdown</h2>
            </div>
            <div class="p-4">
                ${Object.entries(stats.by_status || {}).sort((a,b) => b[1]-a[1]).map(([status, count]) =>
                    `<div class="flex justify-between py-1"><span class="text-gray-700">${esc(status)}</span><span class="font-medium">${count}</span></div>`
                ).join("")}
            </div>
        </div>
    </div>`;
}

function renderApplications(data) {
    const apps = data.applications || [];
    return `
    <div class="max-w-7xl mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-2xl font-bold text-gray-900">Applications (${data.count})</h1>
        </div>
        <div class="bg-white rounded-lg shadow overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Level</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Link</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                    ${apps.map(a => `
                    <tr class="hover:bg-gray-50">
                        <td class="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">${esc(a.date || "")}</td>
                        <td class="px-4 py-2 text-sm text-gray-900">${esc(a.company || "")}</td>
                        <td class="px-4 py-2 text-sm text-gray-900">${esc(a.role || "")}</td>
                        <td class="px-4 py-2 text-sm text-gray-500">${esc(a.level || "")}</td>
                        <td class="px-4 py-2 text-sm">
                            <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full ${statusColor(a.status)}">${esc(a.status || "")}</span>
                        </td>
                        <td class="px-4 py-2 text-sm text-gray-500">${esc(a.source || "")}</td>
                        <td class="px-4 py-2 text-sm">${a.link ? `<a href="${esc(a.link)}" target="_blank" class="text-indigo-600 hover:underline">Link</a>` : ""}</td>
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

    return `
    <div class="max-w-7xl mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-2xl font-bold text-gray-900">Monitor</h1>
            <div class="flex items-center gap-3">
                <span class="text-sm text-gray-500">Last scan: ${timeAgo(results.last_scan)}</span>
                <button onclick="triggerScan()" class="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700">Scan Now</button>
            </div>
        </div>

        <div class="flex items-center gap-4 mb-4">
            <label class="inline-flex items-center gap-1.5 text-sm text-gray-700 cursor-pointer">
                <input type="checkbox" ${hidePoorMatch ? "checked" : ""} onchange="toggleFilter('hidePoorMatch')" class="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500">
                Hide poor match${hidePoorMatch ? ` (${jobs.filter(j => j.status === "poor_match").length})` : ""}
            </label>
            <label class="inline-flex items-center gap-1.5 text-sm text-gray-700 cursor-pointer">
                <input type="checkbox" ${hideApplied ? "checked" : ""} onchange="toggleFilter('hideApplied')" class="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500">
                Hide applied${hideApplied ? ` (${jobs.filter(j => j.already_applied || j.status === "applied").length})` : ""}
            </label>
            ${hiddenCount > 0 ? `<span class="text-sm text-gray-400">${hiddenCount} hidden</span>` : ""}
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div class="bg-white rounded-lg shadow p-4">
                <p class="text-sm text-gray-500">Active Matches</p>
                <p class="text-2xl font-bold">${results.total_active}</p>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
                <p class="text-sm text-gray-500">New Since Last Scan</p>
                <p class="text-2xl font-bold text-green-600">${results.new_since_last}</p>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
                <p class="text-sm text-gray-500">Companies Tracked</p>
                <p class="text-2xl font-bold">${companies.length}</p>
            </div>
        </div>

        ${Object.entries(bySector).map(([sector, sectorJobs]) => `
        <div class="bg-white rounded-lg shadow mb-6">
            <div class="px-4 py-3 border-b border-gray-200">
                <h2 class="text-lg font-semibold text-gray-900">${esc(sector)}</h2>
            </div>
            <ul class="divide-y divide-gray-200">
                ${sectorJobs.map(j => `
                <li class="px-4 py-3">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="font-medium text-gray-900">${esc(j.title)}</p>
                            <p class="text-sm text-gray-500">
                                ${esc(j.company)}
                                &middot; ${esc(j.location)} ${flagEmoji(j.location_flag)}
                                &middot; Found: ${esc(j.first_seen || "")}
                                ${j.already_applied ? '<span class="ml-2 inline-flex px-2 py-0.5 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">Applied</span>' : ""}
                                ${j.applied_at_company ? '<span class="ml-2 inline-flex px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-600">Applied at company</span>' : ""}
                            </p>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full ${jobStatusColor(j.status)}">${esc(j.status || "")}</span>
                            ${j.status !== "poor_match" ? `<button onclick="markJob('${esc(j.sk)}', 'poor_match')" class="text-orange-500 hover:text-orange-700 text-sm px-1 border border-orange-300 rounded hover:bg-orange-50" title="Poor match">Skip</button>` : ""}
                            <a href="${esc(j.url)}" target="_blank" class="text-indigo-600 hover:underline text-sm">View</a>
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
        render();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function triggerScan() {
    try {
        await api("/api/monitor/scan", { method: "POST" });
        alert("Scan triggered! Refresh in a minute to see results.");
    } catch (err) {
        alert("Error: " + err.message);
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
    if (flag === "good") return '<span title="Good location" class="text-green-600">&#10003;</span>';
    if (flag === "bad") return '<span title="Bad location" class="text-red-600">&#10007;</span>';
    return '<span title="Unknown location" class="text-gray-400">?</span>';
}

function statusColor(status) {
    if (!status) return "bg-gray-100 text-gray-800";
    const s = status.toLowerCase();
    if (s === "applied") return "bg-blue-100 text-blue-800";
    if (s.includes("interview") || s.includes("screen") || s.includes("recruiter")) return "bg-green-100 text-green-800";
    if (s === "offer") return "bg-emerald-100 text-emerald-800";
    if (s === "rejected") return "bg-red-100 text-red-800";
    if (s === "withdrawn") return "bg-gray-100 text-gray-800";
    if (s === "hiring freeze") return "bg-yellow-100 text-yellow-800";
    return "bg-gray-100 text-gray-800";
}

function jobStatusColor(status) {
    if (!status) return "bg-gray-100 text-gray-800";
    if (status === "new") return "bg-green-100 text-green-800";
    if (status === "reviewed") return "bg-blue-100 text-blue-800";
    if (status === "applied") return "bg-indigo-100 text-indigo-800";
    if (status === "skipped") return "bg-gray-100 text-gray-800";
    if (status === "poor_match") return "bg-orange-100 text-orange-800";
    if (status === "gone") return "bg-red-100 text-red-800";
    return "bg-gray-100 text-gray-800";
}

// --- Init ---

window.addEventListener("hashchange", render);
render();
