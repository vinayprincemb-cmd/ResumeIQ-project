const views = document.querySelectorAll(".view");
const csrfToken = document.querySelector("meta[name='csrf-token']")?.content || "";
const nativeFetch = window.fetch.bind(window);
window.fetch = (resource, options = {}) => {
    const headers = new Headers(options.headers || {});
    const method = String(options.method || "GET").toUpperCase();
    if (!["GET", "HEAD", "OPTIONS"].includes(method) && csrfToken && !headers.has("X-CSRF-Token")) {
        headers.set("X-CSRF-Token", csrfToken);
    }
    return nativeFetch(resource, { ...options, headers });
};
const navLinks = document.querySelectorAll("[data-view-link]");
const pageTitle = document.querySelector("#page-title");
const menuToggle = document.querySelector("#menu-toggle");
const sidebarOverlay = document.querySelector("#sidebar-overlay");
const themeToggle = document.querySelector("#theme-toggle");
const themeSelect = document.querySelector("#theme-select");
const accentPicker = document.querySelector("#accent-picker");
const accentThemeSelect = document.querySelector("#accent-theme-select");
const toastStack = document.querySelector("#toast-stack");
const appFrame = document.querySelector(".app-frame");
const isAuthenticated = appFrame?.dataset.authenticated === "true";
const currentUserId = appFrame?.dataset.userId || "guest";
const initialView = appFrame?.dataset.initialView || "home";
const desktopSidebarQuery = window.matchMedia("(min-width: 981px)");

const resumeInput = document.querySelector("#resume");
const compareResumeInput = document.querySelector("#compare_resume");
const fileName = document.querySelector("#file-name");
const compareFileName = document.querySelector("#compare-file-name");
const uploadForm = document.querySelector("#analyze-form");
const submitButton = document.querySelector("#analyze-button");
const buttonText = submitButton?.querySelector(".button-text");
const errorMessage = document.querySelector("#error-message");
const resultsContainer = document.querySelector("#report-area");
const summaryBar = document.querySelector("#summary-bar");
const reportsLayout = document.querySelector("#reports-layout");
const exportButton = document.querySelector("#export-report");

const builderForm = document.querySelector("#builder-form");
const builderSections = document.querySelector("#builder-sections");
const aiSectionSelect = document.querySelector("#ai-section");
const aiOutput = document.querySelector("#ai-output");
const builderError = document.querySelector("#builder-error");
const downloadResumeButton = document.querySelector("#download-resume");
const downloadDocxButton = document.querySelector("#download-docx");
const saveDraftButton = document.querySelector("#save-draft");
const resumePreview = document.querySelector("#resume-preview");
const previewTemplate = document.querySelector("#preview-template");
const builderTabButtons = document.querySelectorAll("[data-builder-tab]");
const builderTabPanels = document.querySelectorAll("[data-builder-panel]");
const templateGallery = document.querySelector("#template-gallery");
const templateSelect = document.querySelector("#template-select");
const colorThemeSelect = document.querySelector("#color-theme-select");
const jobForm = document.querySelector("#job-form");
const jobBoard = document.querySelector("#job-board");

const interviewSetupForm = document.querySelector("#interview-setup-form");
const interviewError = document.querySelector("#interview-error");
const interviewSession = document.querySelector("#interview-session");
const interviewQuestionLabel = document.querySelector("#interview-question-label");
const interviewCompetency = document.querySelector("#interview-competency");
const interviewQuestionText = document.querySelector("#interview-question-text");
const interviewAnswer = document.querySelector("#interview-answer");
const interviewProgress = document.querySelector("#interview-progress");
const interviewTimer = document.querySelector("#interview-timer");
const interviewQuestionMeta = document.querySelector("#interview-question-meta");
const interviewStatsGrid = document.querySelector("#interview-stats-grid");
const interviewReviewPanel = document.querySelector("#interview-review-panel");
const voiceStatus = document.querySelector("#voice-status");
const voiceStatusText = document.querySelector("#voice-status-text");
const interviewReportArea = document.querySelector("#interview-report-area");
const interviewSummary = document.querySelector("#interview-summary");
const interviewReport = document.querySelector("#interview-report");
const downloadInterviewReportButton = document.querySelector("#download-interview-report");
const answerFeedback = document.querySelector("#answer-feedback");
const customRoleField = document.querySelector("#custom-role-field");
const interviewJobRole = document.querySelector("#interview-job-role");
const historyPageList = document.querySelector("#history-page-list");
const historyReportPreview = document.querySelector("#history-report-preview");
const historyReportSummary = document.querySelector("#history-report-summary");
const historyReportContent = document.querySelector("#history-report-content");
const aptitudeCategoryField = document.querySelector("#aptitude-category-field");
const aptitudeSession = document.querySelector("#aptitude-session");
const aptitudeQuestionLabel = document.querySelector("#aptitude-question-label");
const aptitudeMeta = document.querySelector("#aptitude-meta");
const aptitudeQuestionText = document.querySelector("#aptitude-question-text");
const aptitudeQuestionMeta = document.querySelector("#aptitude-question-meta");
const aptitudeOptions = document.querySelector("#aptitude-options");
const aptitudeProgress = document.querySelector("#aptitude-progress");
const aptitudeTimer = document.querySelector("#aptitude-timer");

let currentExportPayload = null;
let currentInterview = null;
let currentInterviewReport = null;
let currentQuestionIndex = 0;
let currentAptitude = null;
let currentAptitudeResult = null;
let currentAptitudeIndex = 0;
let interviewStartedAt = null;
let timerInterval = null;
let aptitudeStartedAt = null;
let aptitudeTimerInterval = null;
let recognition = null;
let voiceIsPaused = false;
let voiceIsRecording = false;

const resumeSections = [
    ["career_objective", "Career Objective", "Write a concise career objective or professional summary."],
    ["education", "Education", "Degree, institution, year, GPA or relevant coursework."],
    ["experience", "Experience", "Role, company, dates, and measurable bullet points."],
    ["projects", "Projects", "Project name, technologies, outcome, and links."],
    ["internships", "Internships", "Internship role, organization, and contributions."],
    ["skills", "Skills", "Core role skills separated by lines or commas."],
    ["technical_skills", "Technical Skills", "Languages, frameworks, databases, tools."],
    ["soft_skills", "Soft Skills", "Communication, ownership, collaboration, leadership."],
    ["achievements", "Achievements", "Awards, wins, rankings, measurable accomplishments."],
    ["certifications", "Certifications", "Certification name, issuer, and year."],
    ["languages", "Languages", "Languages and proficiency."],
    ["interests", "Interests", "Relevant interests or communities."],
    ["references", "References", "Reference details or Available on request."],
    ["social_links", "Social Links", "GitHub, LinkedIn, portfolio, publications."],
];

let currentSectionOrder = resumeSections.map(([key]) => key);

const resumeTemplates = [
    ["Modern", "two", "#2563eb"],
    ["Minimal", "one", "#111827"],
    ["Executive", "one", "#111827"],
    ["Software Engineer", "two", "#0f766e"],
    ["Developer", "two", "#0891b2"],
    ["Professional", "one", "#0f766e"],
    ["Corporate", "two", "#1d4ed8"],
    ["Creative", "two", "#7c3aed"],
    ["Student", "one", "#0891b2"],
    ["Data Analyst", "one", "#2563eb"],
    ["ATS Friendly", "one", "#111827"],
    ["Google Style", "two", "#4285f4"],
    ["Microsoft Style", "two", "#107c10"],
    ["Harvard Style", "one", "#991b1b"],
    ["Stanford Style", "one", "#b45309"],
    ["Two Column", "two", "#7c3aed"],
    ["Single Column", "one", "#374151"],
    ["Elegant", "one", "#be185d"],
    ["Dark", "two", "#111827"],
    ["Light", "one", "#64748b"],
    ["Classic", "one", "#374151"],
    ["Consulting", "one", "#b45309"],
    ["Startup", "two", "#ea580c"],
];

function getTemplateMeta(name) {
    const found = resumeTemplates.find(([templateName]) => templateName === name) || resumeTemplates[0];
    return { name: found[0], layout: found[1], accent: found[2] };
}

function createElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined && text !== null) element.textContent = text;
    return element;
}

function showToast(message) {
    if (!toastStack) return;
    const toast = createElement("div", "toast", message);
    toastStack.appendChild(toast);
    setTimeout(() => toast.remove(), 3600);
}

function formToObject(form) {
    return Object.fromEntries(new FormData(form).entries());
}

function isValidEmailAddress(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(value || "").trim());
}

function getPasswordIssues(value) {
    const password = String(value || "");
    const issues = [];
    if (password.length < 8) issues.push("8+ characters");
    if (!/[A-Z]/.test(password)) issues.push("uppercase letter");
    if (!/[a-z]/.test(password)) issues.push("lowercase letter");
    if (!/[0-9]/.test(password)) issues.push("number");
    if (!/[^A-Za-z0-9]/.test(password)) issues.push("symbol");
    return issues;
}

function renderAuthActions(actions = []) {
    const error = document.querySelector("#auth-error");
    if (!error || !actions.length) return;
    const row = createElement("span", "auth-error-actions");
    actions.forEach((action) => {
        const link = createElement("a", "", action.label);
        link.href = action.href;
        row.appendChild(link);
    });
    error.appendChild(row);
}

async function parseAuthResponse(response) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
        return response.json();
    }
    return {
        success: false,
        error: "The server returned an unexpected response. Please try again.",
    };
}

async function submitAuthForm(form, endpoint) {
    const error = document.querySelector("#auth-error");
    hideError(error);
    const payload = formToObject(form);
    payload.remember = Boolean(form.querySelector("[name='remember']")?.checked);
    if (payload.email && !isValidEmailAddress(payload.email)) {
        showError(error, "Enter a valid email address.");
        return;
    }
    if ((endpoint.includes("signup") || endpoint.includes("reset")) && "password" in payload) {
        const issues = getPasswordIssues(payload.password);
        if (issues.length) {
            showError(error, `Password needs ${issues.join(", ")}.`);
            return;
        }
    }
    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify(payload),
        });
        const data = await parseAuthResponse(response);
        if (!response.ok || !data.success) {
            showError(error, data.error || data.message || "Request failed. Please try again.");
            renderAuthActions(data.actions || []);
            return;
        }
        if (data.redirect) {
            showToast(data.message || "Done.");
            setTimeout(() => {
                window.location.href = data.redirect;
            }, endpoint.includes("signup") ? 1000 : 0);
            return;
        }
        showToast(data.message || "Done.");
    } catch (_error) {
        showError(error, "We could not reach the server. Please check your connection and try again.");
    }
}

document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
        const input = button.parentElement?.querySelector("input");
        if (!input) return;
        input.type = input.type === "password" ? "text" : "password";
        button.textContent = input.type === "password" ? "Show" : "Hide";
    });
});

document.querySelector("#login-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    submitAuthForm(event.currentTarget, "/auth/login");
});
document.querySelector("#signup-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    submitAuthForm(event.currentTarget, "/auth/signup");
});
document.querySelector("#forgot-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    submitAuthForm(event.currentTarget, "/auth/forgot-password");
});
document.querySelector("#reset-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    submitAuthForm(event.currentTarget, "/auth/reset-password");
});
document.querySelector("#verify-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    submitAuthForm(event.currentTarget, "/auth/verify-email");
});

function setTheme(theme) {
    const nextTheme = theme === "light" ? "light" : "dark";
    document.body.classList.toggle("light", nextTheme === "light");
    localStorage.setItem("resumeiq-theme", nextTheme);
    if (themeSelect) themeSelect.value = nextTheme;
}

function setSidebarExpandedState() {
    const expanded = document.body.classList.contains("nav-open");
    menuToggle?.setAttribute("aria-expanded", expanded ? "true" : "false");
}

function closeMobileSidebar() {
    document.body.classList.remove("nav-open");
    localStorage.setItem("resumeiq-sidebar-open", "false");
    setSidebarExpandedState();
}

function setDesktopSidebarCollapsed(collapsed, persist = true) {
    document.body.classList.toggle("sidebar-collapsed", collapsed);
    document.body.classList.toggle("nav-open", !collapsed);
    if (persist) localStorage.setItem("resumeiq-sidebar-open", collapsed ? "false" : "true");
    setSidebarExpandedState();
}

function toggleSidebar() {
    document.body.classList.toggle("nav-open");
    localStorage.setItem("resumeiq-sidebar-open", document.body.classList.contains("nav-open") ? "true" : "false");
    setSidebarExpandedState();
}

function builderDraftKey() {
    return `resumeiq-builder-draft:${currentUserId}`;
}

function setAccent(color) {
    const nextColor = color || "#24c6a8";
    document.documentElement.style.setProperty("--accent", nextColor);
    localStorage.setItem("resumeiq-accent", nextColor);
    if (accentPicker) accentPicker.value = nextColor;
    if (accentThemeSelect) accentThemeSelect.value = nextColor;
}

function setView(name) {
    const viewName = name || "home";
    views.forEach((view) => view.classList.toggle("active", view.id === `view-${viewName}`));
    navLinks.forEach((link) => link.classList.toggle("active", link.dataset.viewLink === viewName));
    const activeView = document.querySelector(`#view-${viewName}`);
    if (activeView && pageTitle) pageTitle.textContent = activeView.dataset.title || "ResumeIQ+";
    closeMobileSidebar();
}

function showError(target, message) {
    if (!target) return;
    target.textContent = message;
    target.classList.remove("hidden");
    showToast(message);
}

function hideError(target) {
    if (!target) return;
    target.textContent = "";
    target.classList.add("hidden");
}

async function loadJobs() {
    if (!jobBoard) return;
    const response = await fetch("/api/jobs");
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.error || "Could not load applications.");
    jobBoard.innerHTML = "";
    if (!data.jobs.length) {
        jobBoard.appendChild(createElement("p", "summary-text", "No applications yet. Add roles you want to track here."));
        return;
    }
    data.jobs.forEach((job) => {
        const card = createElement("article", "job-card");
        const heading = createElement("div", "job-card-heading");
        heading.appendChild(createElement("strong", "", job.company));
        heading.appendChild(createElement("span", "job-status", job.status));
        card.appendChild(heading);
        card.appendChild(createElement("p", "", job.role));
        if (job.notes) card.appendChild(createElement("small", "", job.notes));
        const timeline = createElement("small", "job-timeline", (job.timeline || []).map((entry) => `${entry.status} · ${new Date(entry.at).toLocaleDateString()}`).join(" → "));
        card.appendChild(timeline);
        const actions = createElement("div", "history-actions");
        const status = document.createElement("select");
        ["Wishlist", "Applied", "Assessment", "Interview", "Offer", "Rejected"].forEach((value) => {
            const option = new Option(value, value, false, value === job.status);
            status.add(option);
        });
        status.addEventListener("change", async () => {
            const response = await fetch(`/api/jobs/${job.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: status.value }) });
            const result = await response.json();
            if (!response.ok || !result.success) return showToast(result.error || "Could not update application.");
            showToast("Application updated.");
            loadJobs();
        });
        const remove = createElement("button", "compact-button", "Delete");
        remove.type = "button";
        remove.addEventListener("click", async () => {
            if (!window.confirm(`Delete ${job.company} from your tracker?`)) return;
            const response = await fetch(`/api/jobs/${job.id}`, { method: "DELETE" });
            const result = await response.json();
            if (!response.ok || !result.success) return showToast(result.error || "Could not delete application.");
            loadJobs();
        });
        actions.append(status, remove);
        card.appendChild(actions);
        jobBoard.appendChild(card);
    });
}

function setLoading(isLoading) {
    uploadForm?.classList.toggle("is-loading", isLoading);
    if (submitButton) submitButton.disabled = isLoading;
    if (buttonText) buttonText.textContent = isLoading ? "Analyzing..." : "Analyze Resume";
}

function clearResults() {
    summaryBar.innerHTML = "";
    reportsLayout.innerHTML = "";
    resultsContainer.classList.add("hidden");
    reportsLayout.classList.remove("compare-layout");
    currentExportPayload = null;
}

function scoreClass(score) {
    if (score >= 80) return "score-high";
    if (score >= 55) return "score-mid";
    return "score-low";
}

function appendSummaryItem(container, label, value) {
    const item = createElement("div");
    item.appendChild(createElement("span", "", label));
    item.appendChild(createElement("strong", "", value));
    container.appendChild(item);
}

function renderProgressBar(score, large = true) {
    const track = createElement("div", large ? "progress-track" : "mini-progress");
    const bar = createElement("div", large ? `progress-bar ${scoreClass(score)}` : scoreClass(score));
    bar.style.width = `${Number(score) || 0}%`;
    track.appendChild(bar);
    return track;
}

function renderCardHeading(icon, label, title) {
    const heading = createElement("div", "card-heading");
    heading.appendChild(createElement("span", "card-icon", icon));
    const text = createElement("div");
    text.appendChild(createElement("p", "", label));
    text.appendChild(createElement("h2", "", title));
    heading.appendChild(text);
    return heading;
}

function renderSummary(data) {
    summaryBar.innerHTML = "";
    appendSummaryItem(summaryBar, "Target Role", data.job_role || "Not provided");
    [data.result, data.comparison].filter(Boolean).forEach((report) => {
        const score = report.ats_score !== null && report.ats_score !== undefined ? `${report.ats_score}%` : "N/A";
        appendSummaryItem(summaryBar, report.label || "Resume", score);
    });
}

function renderScoreCard(report) {
    if (report.ats_score === null || report.ats_score === undefined) return null;
    const card = createElement("section", "result-card score-card accent-card");
    card.appendChild(renderCardHeading("%", "ATS Score", `${report.ats_score}%`));
    card.appendChild(renderProgressBar(report.ats_score));
    const subScoreList = createElement("div", "sub-score-list");
    (report.sub_scores || []).forEach((subScore) => {
        const row = createElement("div", "sub-score");
        const labelRow = createElement("div");
        labelRow.appendChild(createElement("span", "", subScore.label));
        labelRow.appendChild(createElement("strong", "", `${subScore.score}%`));
        row.appendChild(labelRow);
        row.appendChild(renderProgressBar(subScore.score, false));
        subScoreList.appendChild(row);
    });
    [
        ["Resume Score", report.resume_score],
        ["Grammar Estimate", report.grammar_estimate],
        ["Formatting Score", report.formatting_score],
        ["Keyword Match", report.keyword_match],
    ].forEach(([label, score]) => {
        if (score === undefined || score === null) return;
        const row = createElement("div", "sub-score");
        const labelRow = createElement("div");
        labelRow.appendChild(createElement("span", "", label));
        labelRow.appendChild(createElement("strong", "", `${score || 0}%`));
        row.appendChild(labelRow);
        row.appendChild(renderProgressBar(score || 0, false));
        subScoreList.appendChild(row);
    });
    if (report.evaluation_type === "Offline Resume Analysis") {
        const note = createElement("p", "summary-text", report.offline_message || "Offline Resume Analysis");
        const button = createElement("button", "compact-button", "Regenerate AI Analysis");
        button.type = "button";
        button.addEventListener("click", () => uploadForm?.requestSubmit());
        subScoreList.appendChild(note);
        subScoreList.appendChild(button);
    }
    card.appendChild(subScoreList);
    return card;
}

function renderKeywordCard(report) {
    if (!report.important_keywords || report.important_keywords.length === 0) return null;
    const card = createElement("section", "result-card keyword-card");
    card.appendChild(renderCardHeading("#", "Important Keywords", "Role Signals"));
    const chipList = createElement("div", "chip-list");
    report.important_keywords.forEach((keyword) => chipList.appendChild(createElement("span", "", keyword)));
    card.appendChild(chipList);
    return card;
}

function renderDetailCard(section) {
    const card = createElement("details", "result-card detail-card");
    if (section.key === "missing_skills") card.open = true;
    const summary = createElement("summary");
    summary.appendChild(createElement("span", "card-icon", section.icon));
    const summaryText = createElement("span");
    summaryText.appendChild(createElement("p", "", section.label));
    summaryText.appendChild(createElement("h2", "", section.title));
    summary.appendChild(summaryText);
    card.appendChild(summary);
    if (section.type === "text") {
        card.appendChild(createElement("p", "summary-text", section.content));
    } else {
        const list = createElement("ul");
        (section.items || []).forEach((item) => list.appendChild(createElement("li", "", item)));
        card.appendChild(list);
    }
    return card;
}

function renderReport(report) {
    const column = createElement("article", "report-column");
    const title = createElement("div", "report-title");
    const score = report.ats_score !== null && report.ats_score !== undefined ? `${report.ats_score}%` : "N/A";
    title.appendChild(createElement("span", "", report.label || "Resume"));
    title.appendChild(createElement("strong", "", score));
    column.appendChild(title);
    [renderScoreCard(report), renderKeywordCard(report)].filter(Boolean).forEach((card) => column.appendChild(card));
    (report.sections || []).forEach((section) => column.appendChild(renderDetailCard(section)));
    return column;
}

function renderResults(data) {
    clearResults();
    currentExportPayload = data.export_payload;
    renderSummary(data);
    const reports = [data.result, data.comparison].filter(Boolean);
    reportsLayout.classList.toggle("compare-layout", reports.length > 1);
    reports.forEach((report) => reportsLayout.appendChild(renderReport(report)));
    resultsContainer.classList.remove("hidden");
    resultsContainer.scrollIntoView({ behavior: "smooth", block: "start" });
    showToast("Resume analysis complete.");
    loadDashboard();
}

async function downloadBlob(response, fallbackName) {
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fallbackName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
}

async function exportPDF() {
    if (!currentExportPayload) {
        showError(errorMessage, "Please analyze a resume before exporting the PDF.");
        return;
    }
    exportButton.disabled = true;
    exportButton.textContent = "Exporting...";
    try {
        const response = await fetch("/export-pdf", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(currentExportPayload),
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || "Could not export the report PDF.");
        }
        await downloadBlob(response, "resumeiq-plus-report.pdf");
        showToast("Analysis report downloaded.");
    } catch (error) {
        showError(errorMessage, error.message);
    } finally {
        exportButton.disabled = false;
        exportButton.textContent = "Export Report";
    }
}

function updateText(selector, text) {
    const node = document.querySelector(selector);
    if (node) node.textContent = text;
}

function renderRecentList(container, rows, emptyText, scoreKey = "ats_score") {
    if (!container) return;
    container.innerHTML = "";
    if (!rows.length) {
        container.appendChild(createElement("p", "lead", emptyText));
        return;
    }
    rows.forEach((item) => {
        const row = createElement("article", "recent-item");
        const text = createElement("div");
        text.appendChild(createElement("strong", "", item.filename || item.full_name || item.job_role || item.category || "Untitled"));
        const detail = item.target_role || item.interview_type || item.category || item.job_role || "ResumeIQ+";
        text.appendChild(createElement("span", "", `${detail} - ${new Date(item.created_at).toLocaleString()}`));
        row.appendChild(text);
        if (scoreKey in item) row.appendChild(createElement("span", "recent-score", `${item[scoreKey] ?? 0}%`));
        container.appendChild(row);
    });
}

function formatDate(value) {
    if (!value) return "Unknown date";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function renderInterviewHistoryList(rows) {
    if (!historyPageList) return;
    historyPageList.innerHTML = "";
    updateText("#history-page-count", `${rows.length} session${rows.length === 1 ? "" : "s"}`);
    if (!rows.length) {
        historyPageList.appendChild(createElement("p", "lead", "No interview sessions saved yet."));
        return;
    }

    rows.forEach((item) => {
        const row = createElement("article", "history-item");
        const text = createElement("div");
        const isAptitude = item.record_type === "aptitude";
        text.appendChild(createElement("strong", "", isAptitude ? `${item.candidate_name || "Candidate"} - ${item.category || "Aptitude Test"}` : `${item.candidate_name || "Candidate"} - ${item.job_role || "Role"}`));
        text.appendChild(createElement("span", "", `${item.interview_type || "Mixed"} - ${item.difficulty || "Medium"} - ${formatDate(item.created_at)}`));
        row.appendChild(text);
        row.appendChild(createElement("span", "recent-score", `${item.overall_score ?? 0}%`));
        const actions = createElement("div", "history-actions");
        [
            ["View", () => isAptitude ? loadStoredAptitudeResult(item.id) : loadStoredInterviewReport(item.id)],
            ["PDF", () => isAptitude ? downloadStoredAptitudeReport(item.id) : downloadStoredInterviewReport(item.id)],
            ["Delete", () => isAptitude ? deleteStoredAptitudeResult(item.id) : deleteStoredInterviewReport(item.id)],
        ].forEach(([label, handler]) => {
            const button = createElement("button", "compact-button", label);
            button.type = "button";
            button.addEventListener("click", handler);
            actions.appendChild(button);
        });
        row.appendChild(actions);
        historyPageList.appendChild(row);
    });
}

async function loadStoredAptitudeResult(testId) {
    const response = await fetch(`/aptitude/history/${testId}`);
    const data = await response.json();
    if (!response.ok || !data.success) return showToast(data.error || "Could not load aptitude report.");
    renderAptitudeResult(data.result);
}

async function downloadStoredAptitudeReport(testId) {
    const response = await fetch(`/aptitude/history/${testId}/report-pdf`);
    if (!response.ok) return showToast("Could not download aptitude report.");
    await downloadBlob(response, "resumeiq-plus-aptitude-report.pdf");
}

async function deleteStoredAptitudeResult(testId) {
    if (!window.confirm("Delete this aptitude report?")) return;
    const response = await fetch(`/aptitude/history/${testId}`, { method: "DELETE" });
    const data = await response.json();
    if (!response.ok || !data.success) return showToast(data.error || "Could not delete aptitude report.");
    loadInterviewHistory();
    showToast("Aptitude report deleted.");
}

function renderInterviewComparison(rows) {
    const chart = document.querySelector("#interview-comparison-chart");
    if (!chart) return;
    chart.innerHTML = "";
    const recent = rows.slice(0, 8).reverse();
    if (!recent.length) {
        chart.appendChild(createElement("p", "lead", "Complete interviews to compare scores."));
        return;
    }
    recent.forEach((item) => {
        const bar = createElement("div", "comparison-row");
        bar.appendChild(createElement("span", "", item.job_role || "Interview"));
        const track = createElement("div", "mini-progress");
        const fill = createElement("div", scoreClass(item.overall_score || 0));
        fill.style.width = `${item.overall_score || 0}%`;
        track.appendChild(fill);
        bar.appendChild(track);
        bar.appendChild(createElement("strong", "", `${item.overall_score || 0}%`));
        chart.appendChild(bar);
    });
}

async function loadInterviewHistory() {
    try {
        const response = await fetch("/interview/history");
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || "Could not load interview history.");
        renderInterviewHistoryList(data.interviews || []);
        renderInterviewComparison(data.interviews || []);
    } catch (error) {
        if (historyPageList) historyPageList.innerHTML = `<p class="lead">${error.message}</p>`;
    }
}

function updateDashboard(data) {
    const stats = data.stats || {};
    const recent = data.recent || [];
    const recentResumes = data.recent_resumes || [];
    const interviews = data.recent_interviews || [];
    const aptitudeTests = data.recent_aptitude_tests || [];
    const interviewAnalytics = data.interview_analytics || {};
    const profile = data.profile || {};
    const avg = Number(stats.avg_score) || 0;
    const best = Number(stats.best_score) || 0;
    const interviewAvg = Number(stats.avg_interview_score) || 0;
    updateText("#stat-total", stats.total_resumes || 0);
    updateText("#stat-average", `${avg}%`);
    updateText("#stat-best", `${best}%`);
    updateText("#dashboard-ats", `${avg}%`);
    updateText("#dashboard-interview", `${interviewAvg}%`);
    updateText("#dashboard-total-interviews", stats.total_interviews || 0);
    updateText("#analytics-total-interviews", stats.total_interviews || 0);
    updateText("#analytics-average-interview", `${interviewAvg}%`);
    updateText("#analytics-best-interview", `${stats.best_interview_score || 0}%`);
    updateText("#analytics-average-aptitude", `${stats.avg_aptitude_score || 0}%`);
    updateText("#analytics-total-aptitude", stats.total_aptitude_tests || 0);
    updateText("#hero-score", `${avg}%`);
    updateText("#dashboard-health", avg >= 80 ? "Strong" : avg >= 55 ? "Improving" : "Needs focus");
    updateText("#dashboard-health-copy", avg ? "Keep improving keywords, metrics, and formatting." : "Upload a resume to unlock quality signals.");
    updateText("#recent-count", `${recent.length} item${recent.length === 1 ? "" : "s"}`);
    updateText("#recent-resume-count", `${recentResumes.length} version${recentResumes.length === 1 ? "" : "s"}`);
    updateText("#interview-history-count", `${interviews.length} session${interviews.length === 1 ? "" : "s"}`);
    updateText("#welcome-name", `${(profile.name || "Vinay").split(" ")[0]}, your career workspace is ready.`);
    updateText("#mini-profile-name", profile.name || "Vinay Prince");
    updateText("#profile-name", profile.name || "Vinay Prince");
    updateText("#profile-goal", profile.career_goal || "Manage your career workspace.");
    updateText("#profile-email", profile.email || "-");
    updateText("#profile-menu-name", profile.name || "User");
    updateText("#profile-menu-email", profile.email || "");
    updateProfileAvatars(profile);
    updateText("#profile-resume-count", profile.resume_count || 0);
    updateText("#profile-interview-count", profile.interview_count || 0);
    updateText("#profile-interview-score", `${profile.average_interview_score || 0}%`);
    const heroScoreBar = document.querySelector("#hero-score-bar");
    if (heroScoreBar) heroScoreBar.style.width = `${avg}%`;
    const profileCompletion = document.querySelector("#profile-completion");
    if (profileCompletion) profileCompletion.textContent = `${Math.min(100, 40 + (avg ? 20 : 0) + (recentResumes.length ? 20 : 0) + (interviews.length ? 20 : 0))}%`;

    renderRecentList(document.querySelector("#recent-list"), recent, "No resumes analyzed yet.");
    renderRecentList(document.querySelector("#recent-resume-list"), recentResumes, "No generated resumes yet.", "missing_score");
    renderRecentList(document.querySelector("#interview-history-list"), interviews, "No interview sessions yet.", "overall_score");
    renderRecentList(document.querySelector("#dashboard-recent-interviews"), interviews, "No interview sessions yet.", "overall_score");
    renderRecentList(document.querySelector("#dashboard-recent-aptitude"), aptitudeTests, "No aptitude tests yet.", "final_score");
    renderScoreTrend(avg, interviewAvg, best);
    renderInterviewTrendLines(interviewAnalytics);

    const skills = document.querySelector("#profile-skills");
    if (!skills) return;
    skills.innerHTML = "";
    (profile.skills || []).forEach((skill) => skills.appendChild(createElement("span", "", skill)));
    renderNotifications(data.notifications || []);
    populateProfileForm(data.profile || {});
}

function initialsFromName(name) {
    return String(name || "User").split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "U";
}

function updateProfileAvatars(profile) {
    const image = String(profile.profile_picture || "").trim();
    ["#mini-profile-avatar", "#profile-menu-avatar", ".profile-panel .avatar.large"].forEach((selector) => {
        const avatar = document.querySelector(selector);
        if (!avatar) return;
        avatar.textContent = initialsFromName(profile.name);
        avatar.classList.toggle("has-image", Boolean(image));
        avatar.style.backgroundImage = image ? `url("${image.replace(/"/g, "%22")}")` : "";
    });
}

function populateProfileForm(profile) {
    const form = document.querySelector("#profile-form");
    if (!form) return;
    const map = {
        full_name: profile.name,
        email: profile.email,
        skills: (profile.skills || []).join(", "),
    };
    Object.entries({ ...profile, ...map }).forEach(([key, value]) => {
        const field = form.elements[key];
        if (field) field.value = Array.isArray(value) ? value.join(", ") : (value || "");
    });
}

function renderNotifications(items) {
    const list = document.querySelector("#notification-list");
    if (!list) return;
    list.innerHTML = "";
    if (!items.length) {
        list.appendChild(createElement("p", "lead", "No notifications yet."));
        return;
    }
    items.forEach((item) => {
        const row = createElement("article", "recent-item");
        row.appendChild(createElement("strong", "", item.title || "Notification"));
        row.appendChild(createElement("span", "", item.body || ""));
        row.appendChild(createElement("small", "", formatDate(item.created_at)));
        list.appendChild(row);
    });
}

function renderResumeLibrary(items) {
    const list = document.querySelector("#resume-library-list");
    if (!list) return;
    list.innerHTML = "";
    if (!items.length) {
        list.appendChild(createElement("p", "lead", "No resumes found."));
        return;
    }
    items.forEach((item) => {
        const row = createElement("article", "history-item");
        const text = createElement("div");
        text.appendChild(createElement("strong", "", item.title || item.full_name || "Untitled Resume"));
        text.appendChild(createElement("span", "", `${item.template || "Template"} - ${item.target_role || "No role"} - ${item.status || "active"}`));
        row.appendChild(text);
        const actions = createElement("div", "history-actions");
        [
            ["Duplicate", "duplicate"],
            [item.is_favorite ? "Unfavorite" : "Favorite", "favorite"],
            [item.status === "archived" ? "Restore" : "Archive", item.status === "archived" ? "restore" : "archive"],
            ["Delete", "delete"],
        ].forEach(([label, action]) => {
            const button = createElement("button", "compact-button", label);
            button.type = "button";
            button.addEventListener("click", () => runResumeAction(item.id, action));
            actions.appendChild(button);
        });
        row.appendChild(actions);
        list.appendChild(row);
    });
}

async function loadResumeLibrary() {
    const query = document.querySelector("#resume-search")?.value || "";
    const response = await fetch(`/api/resumes?q=${encodeURIComponent(query)}&status=all`);
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.error || "Could not load resumes.");
    renderResumeLibrary(data.resumes || []);
}

async function runResumeAction(id, action) {
    const response = await fetch(`/api/resumes/${id}/${action}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.error || "Could not update resume.");
    showToast("Resume library updated.");
    await loadResumeLibrary();
}

function renderSearchResults(results) {
    const list = document.querySelector("#global-search-results");
    if (!list) return;
    list.innerHTML = "";
    const groups = Object.entries(results || {});
    if (!groups.some(([, rows]) => rows.length)) {
        list.appendChild(createElement("p", "lead", "No results found."));
        return;
    }
    groups.forEach(([group, rows]) => {
        rows.forEach((item) => {
            const row = createElement("article", "history-item");
            row.appendChild(createElement("strong", "", `${group}: ${item.title || item.name || item.filename || item.job_role || "Result"}`));
            row.appendChild(createElement("span", "", item.target_role || item.category || item.created_at || ""));
            list.appendChild(row);
        });
    });
}

async function runGlobalSearch() {
    const query = document.querySelector("#global-search-input")?.value || "";
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.error || "Search failed.");
    renderSearchResults(data.results || {});
}

async function loadAdminDashboard() {
    const counts = document.querySelector("#admin-counts");
    if (!counts) return;
    const response = await fetch("/api/admin");
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.error || "Could not load admin.");
    counts.innerHTML = "";
    Object.entries(data.admin.counts || {}).forEach(([label, value]) => {
        const card = createElement("article", "metric-card");
        card.appendChild(createElement("span", "", label.replace("_", " ")));
        card.appendChild(createElement("strong", "", value));
        counts.appendChild(card);
    });
    const users = document.querySelector("#admin-users");
    const uploads = document.querySelector("#admin-uploads");
    if (users) {
        users.innerHTML = "";
        (data.admin.users || []).forEach((user) => {
            const row = createElement("article", "history-item");
            row.appendChild(createElement("strong", "", user.full_name || user.email));
            row.appendChild(createElement("span", "", `${user.email} - ${user.is_admin ? "Admin" : "User"}`));
            users.appendChild(row);
        });
    }
    if (uploads) {
        uploads.innerHTML = "";
        (data.admin.uploaded_resumes || []).forEach((upload) => {
            const row = createElement("article", "history-item");
            row.appendChild(createElement("strong", "", upload.filename));
            row.appendChild(createElement("span", "", `${upload.job_role} - ${upload.ats_score || 0}%`));
            uploads.appendChild(row);
        });
    }
}

function renderInterviewTrendLines(analytics) {
    const chart = document.querySelector("#interview-trends");
    if (!chart) return;
    chart.innerHTML = "";
    const technical = analytics.technical_trend || [];
    const communication = analytics.communication_trend || [];
    const latest = [technical.slice(-6), communication.slice(-6)];
    const labels = ["Technical Trend", "Communication Trend"];
    latest.forEach((series, index) => {
        const row = createElement("div", "trend-row");
        row.appendChild(createElement("span", "", labels[index]));
        const bars = createElement("div", "trend-bars");
        if (!series.length) {
            bars.appendChild(createElement("small", "", "No data"));
        } else {
            series.forEach((point) => {
                const bar = createElement("strong", "", `${point.score || 0}`);
                bar.style.height = `${Math.max(18, Math.min(point.score || 0, 100) * 1.3)}px`;
                bars.appendChild(bar);
            });
        }
        row.appendChild(bars);
        chart.appendChild(row);
    });
}

function renderScoreTrend(avg, interviewAvg, best) {
    const chart = document.querySelector("#score-trend");
    if (!chart) return;
    const values = [Math.max(12, avg - 18), Math.max(18, avg - 8), avg || 24, best || avg || 32, interviewAvg || 28, Math.max(avg, interviewAvg, best, 42)];
    chart.innerHTML = "";
    values.forEach((value) => {
        const bar = createElement("span", "", `${Math.round(value)}%`);
        bar.style.height = `${Math.max(34, Math.min(value, 100) * 1.65)}px`;
        chart.appendChild(bar);
    });
}

async function loadDashboard() {
    try {
        const response = await fetch("/dashboard-data");
        const data = await response.json();
        if (data.success) updateDashboard(data);
    } catch (_error) {
        document.querySelector("#recent-list").innerHTML = "<p class=\"lead\">Dashboard data is unavailable.</p>";
    }
}

function renderBuilderSections() {
    if (!builderSections || !aiSectionSelect) return;
    builderSections.innerHTML = "";
    aiSectionSelect.innerHTML = "";
    const sectionMap = new Map(resumeSections.map((section) => [section[0], section]));
    currentSectionOrder.forEach((key) => {
        const section = sectionMap.get(key);
        if (!section) return;
        const [, label, placeholder] = section;
        const option = document.createElement("option");
        option.value = key;
        option.textContent = label;
        aiSectionSelect.appendChild(option);

        const wrapper = createElement("label", "builder-section");
        wrapper.dataset.section = key;
        wrapper.draggable = true;
        const header = createElement("div", "builder-section-header");
        header.appendChild(createElement("span", "", label));
        const controls = createElement("div", "section-order-buttons");
        [["Up", -1], ["Down", 1]].forEach(([text, delta]) => {
            const button = createElement("button", "", text);
            button.type = "button";
            button.addEventListener("click", () => moveBuilderSection(key, delta));
            controls.appendChild(button);
        });
        header.appendChild(controls);
        wrapper.appendChild(header);
        const area = document.createElement("textarea");
        area.name = key;
        area.placeholder = placeholder;
        const existing = builderForm?.querySelector(`[name="${key}"]`)?.value;
        if (existing) area.value = existing;
        wrapper.appendChild(area);
        builderSections.appendChild(wrapper);
    });
    aiSectionSelect.value = "career_objective";
}

function setBuilderTab(tabName = "profile") {
    const target = ["profile", "content", "templates", "design", "export"].includes(tabName) ? tabName : "profile";
    builderTabButtons.forEach((button) => button.classList.toggle("active", button.dataset.builderTab === target));
    builderTabPanels.forEach((panel) => panel.classList.toggle("hidden", panel.dataset.builderPanel !== target));
    builderTabPanels.forEach((panel) => panel.classList.toggle("active", panel.dataset.builderPanel === target));
    updateResumePreview();
}

function moveBuilderSection(key, delta) {
    const index = currentSectionOrder.indexOf(key);
    const nextIndex = index + delta;
    if (index < 0 || nextIndex < 0 || nextIndex >= currentSectionOrder.length) return;
    [currentSectionOrder[index], currentSectionOrder[nextIndex]] = [currentSectionOrder[nextIndex], currentSectionOrder[index]];
    renderBuilderSections();
    saveBuilderDraft();
    updateResumePreview();
}

function renderTemplateGallery() {
    if (!templateGallery || !templateSelect) return;
    templateGallery.innerHTML = "";
    templateSelect.innerHTML = "";
    resumeTemplates.forEach(([name, layout, accent]) => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        templateSelect.appendChild(option);

        const card = createElement("button", "template-card");
        card.type = "button";
        card.dataset.template = name;
        card.style.setProperty("--template-accent", accent);
        card.appendChild(createElement("strong", "", name));
        card.appendChild(createElement("span", "", `${layout === "two" ? "Two column" : "One column"} · PDF/DOCX ready`));
        const mock = createElement("div", `template-mini ${layout === "two" ? "two" : "one"}`);
        mock.appendChild(createElement("i"));
        mock.appendChild(createElement("i"));
        mock.appendChild(createElement("i"));
        card.appendChild(mock);
        card.addEventListener("click", () => applyTemplate(name));
        templateGallery.appendChild(card);
    });
    applyTemplate(templateSelect.value || resumeTemplates[0][0], false);
}

function applyTemplate(name, persist = true) {
    const meta = getTemplateMeta(name);
    const templateInput = builderForm?.querySelector("[name='template']");
    const layoutInput = builderForm?.querySelector("[name='layout']");
    const accentInput = builderForm?.querySelector("[name='accent_color']");
    if (templateInput) templateInput.value = meta.name;
    if (layoutInput) layoutInput.value = meta.layout;
    if (accentInput) accentInput.value = meta.accent;
    if (colorThemeSelect) colorThemeSelect.value = meta.accent;
    document.querySelectorAll(".template-card").forEach((card) => card.classList.toggle("active", card.dataset.template === meta.name));
    updateResumePreview();
    if (persist) saveBuilderDraft();
}

function syncTemplateSelection() {
    const name = builderForm?.querySelector("[name='template']")?.value || "Executive";
    document.querySelectorAll(".template-card").forEach((card) => card.classList.toggle("active", card.dataset.template === name));
    if (templateSelect) templateSelect.value = name;
}

function getBuilderPayload() {
    const formData = new FormData(builderForm);
    const personalKeys = ["full_name", "email", "phone", "location", "linkedin", "portfolio"];
    const personalDetails = {};
    personalKeys.forEach((key) => {
        personalDetails[key] = String(formData.get(key) || "").trim();
    });
    const resume = {
        personal_details: personalDetails,
        target_role: String(formData.get("target_role") || "").trim(),
        template: String(formData.get("template") || "Executive"),
        font: String(formData.get("font") || "Inter"),
        accent_color: String(formData.get("accent_color") || "#24c6a8"),
        color_theme: String(formData.get("color_theme") || formData.get("accent_color") || "#24c6a8"),
        layout: String(formData.get("layout") || "one"),
        show_photo: Boolean(formData.get("show_photo")),
        section_order: currentSectionOrder.slice(),
    };
    resumeSections.forEach(([key]) => {
        const value = String(formData.get(key) || "").trim();
        resume[key] = key === "career_objective" ? value : value.split("\n").map((line) => line.trim()).filter(Boolean);
    });
    return resume;
}

function saveBuilderDraft() {
    if (!builderForm) return;
    localStorage.setItem(builderDraftKey(), JSON.stringify(getBuilderPayload()));
    if (saveDraftButton) saveDraftButton.textContent = "Saved";
    setTimeout(() => {
        if (saveDraftButton) saveDraftButton.textContent = "Auto save on";
    }, 1200);
}

function loadBuilderDraft() {
    const raw = localStorage.getItem(builderDraftKey());
    if (!raw || !builderForm) return;
    try {
        const draft = JSON.parse(raw);
        Object.entries(draft.personal_details || {}).forEach(([key, value]) => {
            const input = builderForm.querySelector(`[name="${key}"]`);
            if (input) input.value = value;
        });
        ["target_role", "template", "font", "accent_color", "color_theme", "layout"].forEach((key) => {
            const input = builderForm.querySelector(`[name="${key}"]`);
            if (input && draft[key]) input.value = draft[key];
        });
        const photoInput = builderForm.querySelector("[name='show_photo']");
        if (photoInput) photoInput.checked = Boolean(draft.show_photo);
        if (Array.isArray(draft.section_order)) {
            const valid = new Set(resumeSections.map(([key]) => key));
            currentSectionOrder = draft.section_order.filter((key) => valid.has(key));
            resumeSections.forEach(([key]) => {
                if (!currentSectionOrder.includes(key)) currentSectionOrder.push(key);
            });
            renderBuilderSections();
        }
        resumeSections.forEach(([key]) => {
            const input = builderForm.querySelector(`[name="${key}"]`);
            const value = draft[key];
            if (input && Array.isArray(value)) input.value = value.join("\n");
            if (input && typeof value === "string") input.value = value;
        });
        updateResumePreview();
    } catch (_error) {
        localStorage.removeItem(builderDraftKey());
    }
}

function updateResumePreview() {
    if (!resumePreview || !builderForm) return;
    const resume = getBuilderPayload();
    const name = resume.personal_details.full_name || "Your Name";
    const role = resume.target_role || "Target role";
    const objective = resume.career_objective || "Resume sections will preview here as you type.";
    const skills = Array.isArray(resume.skills) ? resume.skills.slice(0, 4).join(" | ") : "";
    const templateMeta = getTemplateMeta(resume.template);
    resumePreview.innerHTML = "";
    resumePreview.className = `resume-preview ${resume.layout === "two" ? "two-column-preview" : "one-column-preview"}`;
    resumePreview.style.setProperty("--resume-accent", resume.accent_color || templateMeta.accent);
    resumePreview.style.fontFamily = resume.font || "Inter";
    if (resume.show_photo) resumePreview.appendChild(createElement("div", "preview-photo", name.slice(0, 1).toUpperCase()));
    resumePreview.appendChild(createElement("strong", "", name));
    resumePreview.appendChild(createElement("span", "", role));
    resumePreview.appendChild(createElement("p", "", objective));
    if (skills) resumePreview.appendChild(createElement("small", "", skills));
    if (previewTemplate) previewTemplate.textContent = resume.template || "Executive";
}

async function runAiAssist(action) {
    hideError(builderError);
    const section = aiSectionSelect.value;
    const textarea = builderForm.querySelector(`[name="${section}"]`);
    const targetRole = builderForm.querySelector("[name='target_role']").value;
    const content = textarea.value.trim();
    if (!content) {
        showError(builderError, "Add draft content to the selected section before using AI.");
        return;
    }
    aiOutput.classList.remove("hidden");
    aiOutput.textContent = "Working with Gemini...";
    document.querySelectorAll("[data-ai-action]").forEach((button) => (button.disabled = true));
    try {
        const response = await fetch("/ai-assist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action, section, content, target_role: targetRole }),
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || "AI assistance failed.");
        const result = data.result || {};
        textarea.value = result.content || textarea.value;
        aiOutput.textContent = [result.content, ...(result.suggestions || []).map((item) => `- ${item}`)].filter(Boolean).join("\n\n");
        updateResumePreview();
        saveBuilderDraft();
        showToast("AI writing update applied.");
    } catch (error) {
        showError(builderError, error.message);
        aiOutput.textContent = "";
        aiOutput.classList.add("hidden");
    } finally {
        document.querySelectorAll("[data-ai-action]").forEach((button) => (button.disabled = false));
    }
}

async function downloadResumePdf() {
    hideError(builderError);
    const resume = getBuilderPayload();
    if (!resume.personal_details.full_name) {
        showError(builderError, "Add a full name before downloading the resume.");
        return;
    }
    downloadResumeButton.disabled = true;
    downloadResumeButton.textContent = "Generating...";
    try {
        const response = await fetch("/resume-pdf", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ resume }),
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || "Could not generate resume PDF.");
        }
        await downloadBlob(response, "resume.pdf");
        showToast("Resume PDF downloaded.");
        loadDashboard();
    } catch (error) {
        showError(builderError, error.message);
    } finally {
        downloadResumeButton.disabled = false;
        downloadResumeButton.textContent = "Download PDF";
    }
}

async function downloadResumeDocx() {
    hideError(builderError);
    const resume = getBuilderPayload();
    if (!resume.personal_details.full_name) {
        showError(builderError, "Add a full name before downloading the resume.");
        return;
    }
    downloadDocxButton.disabled = true;
    downloadDocxButton.textContent = "Generating...";
    try {
        const response = await fetch("/resume-docx", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ resume }),
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || "Could not generate resume DOCX.");
        }
        await downloadBlob(response, "resume.docx");
        showToast("Resume DOCX downloaded.");
        loadDashboard();
    } catch (error) {
        showError(builderError, error.message);
    } finally {
        downloadDocxButton.disabled = false;
        downloadDocxButton.textContent = "Download DOCX";
    }
}

function persistCurrentAnswer() {
    if (!currentInterview) return;
    currentInterview.answers[currentQuestionIndex] = interviewAnswer.value.trim();
    sessionStorage.setItem("resumeiq-current-interview", JSON.stringify(currentInterview));
    renderInterviewStats();
    saveInterviewSession();
}

let saveInterviewTimer = null;

function saveInterviewSession(status = "active") {
    if (!currentInterview?.sessionId) return;
    clearTimeout(saveInterviewTimer);
    saveInterviewTimer = setTimeout(async () => {
        try {
            await fetch(`/interview/session/${currentInterview.sessionId}/answers`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    setup: currentInterview.setup,
                    questions: currentInterview.questions,
                    answers: currentInterview.answers,
                    status,
                }),
            });
        } catch (_error) {
            sessionStorage.setItem("resumeiq-current-interview", JSON.stringify(currentInterview));
        }
    }, 350);
}

function estimatedQuestionTime(question) {
    const difficulty = String(question?.difficulty || "Medium").toLowerCase();
    if (difficulty === "hard") return "4 min";
    if (difficulty === "easy") return "2 min";
    return "3 min";
}

function renderQuestionMeta(target, items) {
    if (!target) return;
    target.innerHTML = "";
    items.forEach(([label, value]) => {
        const item = createElement("div", "question-meta-item");
        item.appendChild(createElement("span", "", label));
        item.appendChild(createElement("strong", "", value || "-"));
        target.appendChild(item);
    });
}

function renderInterviewStats() {
    if (!interviewStatsGrid || !currentInterview) return;
    const answers = currentInterview.answers || [];
    const total = currentInterview.questions.length;
    const answered = answers.filter((answer) => String(answer || "").trim()).length;
    const skipped = total - answered;
    const bookmarked = Object.keys(currentInterview.bookmarks || {}).length;
    interviewStatsGrid.innerHTML = "";
    [
        ["Remaining", Math.max(total - currentQuestionIndex - 1, 0)],
        ["Answered", answered],
        ["Skipped", skipped],
        ["Bookmarked", bookmarked],
    ].forEach(([label, value]) => {
        const item = createElement("div");
        item.appendChild(createElement("span", "", label));
        item.appendChild(createElement("strong", "", String(value)));
        interviewStatsGrid.appendChild(item);
    });
}

function renderInterviewQuestion() {
    if (!currentInterview) return;
    const question = currentInterview.questions[currentQuestionIndex];
    interviewQuestionLabel.textContent = `Question ${currentQuestionIndex + 1} of ${currentInterview.questions.length}`;
    interviewCompetency.textContent = question.competency || "Role fit";
    renderQuestionMeta(interviewQuestionMeta, [
        ["Question", `${currentQuestionIndex + 1}/${currentInterview.questions.length}`],
        ["Category", question.category || question.type || currentInterview.setup.interview_type],
        ["Topic", question.topic || question.competency || "Role fit"],
        ["Difficulty", question.difficulty || currentInterview.setup.difficulty],
        ["Estimated Time", estimatedQuestionTime(question)],
    ]);
    interviewQuestionText.textContent = question.question;
    interviewAnswer.value = currentInterview.answers[currentQuestionIndex] || "";
    renderAnswerWritingAssistant();
    interviewProgress.style.width = `${((currentQuestionIndex + 1) / currentInterview.questions.length) * 100}%`;
    renderInterviewStats();
    interviewReviewPanel?.classList.add("hidden");
    renderAnswerFeedback(null);
}

function renderAnswerWritingAssistant() {
    const indicators = document.querySelector("#answer-quality-indicators");
    const suggestion = document.querySelector("#answer-writing-suggestion");
    if (!indicators || !suggestion || !interviewAnswer) return;
    const text = interviewAnswer.value.trim();
    const words = text ? text.split(/\s+/).filter(Boolean) : [];
    const sentences = text ? text.split(/[.!?]+/).filter((sentence) => sentence.trim()) : [];
    const grammar = (!text || /^[A-Z]/.test(text)) && (!text || /[.!?]$/.test(text)) && !/\b(\w+)\s+\1\b/i.test(text);
    const clarity = words.length >= 20 && !/\b(very|really|basically|actually|stuff|things)\b/i.test(text);
    const confidence = /\b(I led|I built|I delivered|I improved|I implemented|I achieved)\b/i.test(text);
    const completeness = sentences.length >= 2 && /\b(result|outcome|impact|because|therefore|learned)\b/i.test(text);
    const length = words.length >= 35;
    indicators.innerHTML = "";
    [["Grammar", grammar], ["Clarity", clarity], ["Confidence", confidence], ["Answer Length", length], ["Completeness", completeness]].forEach(([label, passed]) => {
        indicators.appendChild(createElement("span", passed ? "is-good" : "needs-work", `${passed ? "✓" : "!"} ${label}`));
    });
    if (!text) suggestion.textContent = "Start typing for grammar, clarity, and answer-quality guidance.";
    else if (!length) suggestion.textContent = `Your answer is ${words.length} words. Add specific actions and results for a stronger response.`;
    else if (!grammar) suggestion.textContent = "Check capitalization, punctuation, or repeated words. Browser spellcheck underlines spelling mistakes as you type.";
    else if (!clarity || !completeness) suggestion.textContent = "Improve clarity by using a concise situation, action, and measurable result.";
    else suggestion.textContent = "Voice captured successfully. Your answer is clear and ready for review.";
}

function renderAnswerFeedback(evaluation) {
    if (!answerFeedback) return;
    answerFeedback.innerHTML = "";
    if (!evaluation) {
        answerFeedback.classList.add("hidden");
        return;
    }
    answerFeedback.classList.remove("hidden");
    const heading = createElement("div", "section-header tight");
    heading.appendChild(createElement("h3", "", "AI Evaluation"));
    heading.appendChild(createElement("strong", "", `${evaluation.overall_score || 0}%`));
    answerFeedback.appendChild(heading);
    const grid = createElement("div", "feedback-scores");
    [
        ["Technical", evaluation.technical_score],
        ["Communication", evaluation.communication_score],
        ["Confidence", evaluation.confidence_score],
        ["Grammar", evaluation.grammar_score],
        ["Problem Solving", evaluation.problem_solving_score],
    ].forEach(([label, score]) => {
        const item = createElement("div");
        item.appendChild(createElement("span", "", label));
        item.appendChild(createElement("strong", "", `${score || 0}%`));
        item.appendChild(renderProgressBar(score || 0, false));
        grid.appendChild(item);
    });
    answerFeedback.appendChild(grid);
    if (evaluation.better_sample_answer) {
        answerFeedback.appendChild(createElement("p", "summary-text", `Better sample answer: ${evaluation.better_sample_answer}`));
    }
    [
        ["Strengths", evaluation.strengths],
        ["Weaknesses", evaluation.weaknesses],
        ["Suggestions", evaluation.improvement_suggestions],
    ].forEach(([title, items]) => {
        if (!items || !items.length) return;
        const list = createElement("ul");
        items.forEach((item) => list.appendChild(createElement("li", "", item)));
        const block = createElement("div", "feedback-list");
        block.appendChild(createElement("strong", "", title));
        block.appendChild(list);
        answerFeedback.appendChild(block);
    });
}

function startTimer() {
    interviewStartedAt = Date.now();
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        const total = Math.floor((Date.now() - interviewStartedAt) / 1000);
        const minutes = String(Math.floor(total / 60)).padStart(2, "0");
        const seconds = String(total % 60).padStart(2, "0");
        interviewTimer.textContent = `${minutes}:${seconds}`;
    }, 1000);
}

async function startInterview(event) {
    event.preventDefault();
    hideError(interviewError);
    const button = document.querySelector("#start-interview");
    button.disabled = true;
    button.textContent = "Generating...";
    try {
        const payload = Object.fromEntries(new FormData(interviewSetupForm).entries());
        if (payload.job_role === "Custom") payload.job_role = payload.custom_job_role || "";
        if (payload.interview_type === "Aptitude Test") {
            await startAptitude(payload, button);
            return;
        }
        const response = await fetch("/interview/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || "Could not start interview.");
        currentInterview = {
            sessionId: data.session_id,
            setup: data.setup,
            questions: data.questions,
            answers: Array(data.questions.length).fill(""),
            bookmarks: {},
        };
        currentQuestionIndex = 0;
        currentInterviewReport = null;
        interviewReportArea.classList.add("hidden");
        aptitudeSession?.classList.add("hidden");
        interviewSession.classList.remove("hidden");
        renderInterviewQuestion();
        startTimer();
        interviewSession.scrollIntoView({ behavior: "smooth", block: "start" });
        sessionStorage.setItem("resumeiq-current-interview", JSON.stringify(currentInterview));
        showToast(data.message || "Interview session ready. Questions loaded locally.");
    } catch (error) {
        showError(interviewError, error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Start Interview";
    }
}

async function moveQuestion(delta) {
    if (!currentInterview) return;
    persistCurrentAnswer();
    currentQuestionIndex = Math.max(0, Math.min(currentQuestionIndex + delta, currentInterview.questions.length - 1));
    renderInterviewQuestion();
}

function bookmarkQuestion() {
    if (!currentInterview) return;
    const key = String(currentQuestionIndex + 1);
    currentInterview.bookmarks = currentInterview.bookmarks || {};
    if (currentInterview.bookmarks[key]) {
        delete currentInterview.bookmarks[key];
        showToast("Bookmark removed.");
    } else {
        currentInterview.bookmarks[key] = true;
        showToast("Question bookmarked.");
    }
    sessionStorage.setItem("resumeiq-current-interview", JSON.stringify(currentInterview));
    renderInterviewStats();
    saveInterviewSession();
}

function renderInterviewReview() {
    if (!interviewReviewPanel || !currentInterview) return;
    persistCurrentAnswer();
    interviewReviewPanel.innerHTML = "";
    const answered = currentInterview.answers.filter((answer) => String(answer || "").trim()).length;
    const heading = createElement("div", "section-header tight");
    heading.appendChild(createElement("h3", "", "Review Answers"));
    heading.appendChild(createElement("span", "", `${answered}/${currentInterview.questions.length} answered`));
    interviewReviewPanel.appendChild(heading);
    currentInterview.questions.forEach((question, index) => {
        const row = createElement("button", "review-row");
        row.type = "button";
        const hasAnswer = Boolean(String(currentInterview.answers[index] || "").trim());
        row.appendChild(createElement("strong", "", `Q${index + 1}`));
        row.appendChild(createElement("span", "", hasAnswer ? "Answered" : "Skipped"));
        row.appendChild(createElement("small", "", question.topic || question.competency || question.category || "Interview"));
        row.addEventListener("click", () => {
            currentQuestionIndex = index;
            renderInterviewQuestion();
        });
        interviewReviewPanel.appendChild(row);
    });
    interviewReviewPanel.classList.remove("hidden");
    currentInterview.reviewed = true;
}

async function skipQuestion() {
    if (!currentInterview) return;
    interviewAnswer.value = "";
    persistCurrentAnswer();
    await moveQuestion(1);
}

function setVoiceControls(state, message) {
    voiceIsRecording = state === "recording";
    voiceIsPaused = state === "paused";
    document.querySelector("#voice-answer")?.classList.toggle("hidden", state === "recording" || state === "paused");
    document.querySelector("#pause-voice")?.classList.toggle("hidden", state !== "recording");
    document.querySelector("#resume-voice")?.classList.toggle("hidden", state !== "paused");
    document.querySelector("#stop-voice")?.classList.toggle("hidden", state === "idle");
    voiceStatus?.classList.toggle("hidden", state === "idle");
    voiceStatus?.classList.toggle("is-recording", state === "recording");
    if (voiceStatusText) voiceStatusText.textContent = message || "Microphone ready";
}

function startVoiceAnswer() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        showError(interviewError, "Voice input is not supported in this browser.");
        return;
    }
    recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = true;
    let finalTranscript = interviewAnswer.value.trim();
    recognition.onresult = (event) => {
        setVoiceControls("recording", "Processing...");
        let interimTranscript = "";
        for (let index = event.resultIndex; index < event.results.length; index += 1) {
            const transcript = event.results[index][0].transcript;
            if (event.results[index].isFinal) {
                finalTranscript = `${finalTranscript} ${transcript}`.trim();
            } else {
                interimTranscript = `${interimTranscript} ${transcript}`.trim();
            }
        }
        interviewAnswer.value = `${finalTranscript} ${interimTranscript}`.trim();
        persistCurrentAnswer();
        if (finalTranscript) setVoiceControls("recording", "Voice captured successfully.");
    };
    recognition.onend = () => {
        if (voiceIsRecording && !voiceIsPaused) {
            recognition.start();
            return;
        }
        if (!voiceIsPaused) setVoiceControls("idle", "Microphone stopped");
    };
    recognition.onerror = (event) => {
        setVoiceControls("idle", "Microphone stopped");
        showError(interviewError, event.error === "not-allowed" || event.error === "service-not-allowed"
            ? "Microphone permission was denied. Allow microphone access and try again."
            : "Voice capture failed. Check microphone permission and try again.");
    };
    recognition.start();
    setVoiceControls("recording", "Listening...");
    showToast("Microphone recording started.");
}

function pauseVoiceAnswer() {
    if (!recognition) return;
    voiceIsPaused = true;
    recognition.stop();
    setVoiceControls("paused", "Recording paused");
}

function resumeVoiceAnswer() {
    if (!recognition) return startVoiceAnswer();
    recognition.start();
    setVoiceControls("recording", "Listening...");
}

function stopVoiceAnswer() {
    if (!recognition) return;
    voiceIsRecording = false;
    voiceIsPaused = false;
    recognition.stop();
    setVoiceControls("idle", "Microphone stopped");
    persistCurrentAnswer();
}

function renderInterviewReport(report, options = {}) {
    const summaryTarget = options.summaryTarget || interviewSummary;
    const reportTarget = options.reportTarget || interviewReport;
    const reportArea = options.reportArea || interviewReportArea;
    if (options.setCurrent !== false) currentInterviewReport = report;
    const scores = report.scores || {};
    summaryTarget.innerHTML = "";
    appendSummaryItem(summaryTarget, "Overall", `${scores.overall_score || 0}%`);
    appendSummaryItem(summaryTarget, "Technical", `${scores.technical_score || 0}%`);
    appendSummaryItem(summaryTarget, "Communication", `${scores.communication_score || 0}%`);
    appendSummaryItem(summaryTarget, "Readiness", `${scores.role_readiness_score || scores.overall_score || 0}%`);
    appendSummaryItem(summaryTarget, "Type", report.evaluation_type || "AI Evaluation");
    appendSummaryItem(summaryTarget, "Recommendation", report.hiring_recommendation || "Review");
    reportTarget.innerHTML = "";

    const scoreCard = createElement("section", "result-card score-card accent-card");
    scoreCard.appendChild(renderCardHeading("%", "Interview Score", `${scores.overall_score || 0}%`));
    scoreCard.appendChild(renderProgressBar(scores.overall_score || 0));
    const subScoreList = createElement("div", "sub-score-list");
    [
        ["Technical", scores.technical_score],
        ["Communication", scores.communication_score],
        ["Confidence", scores.confidence_score],
        ["Grammar", scores.grammar_score],
        ["Vocabulary", scores.vocabulary_score],
        ["Problem Solving", scores.problem_solving_score],
        ["Role Readiness", scores.role_readiness_score || scores.overall_score],
        ["Overall Percentage", scores.overall_percentage || scores.overall_score],
    ].forEach(([label, score]) => {
        const row = createElement("div", "sub-score");
        const labelRow = createElement("div");
        labelRow.appendChild(createElement("span", "", label));
        labelRow.appendChild(createElement("strong", "", `${score || 0}%`));
        row.appendChild(labelRow);
        row.appendChild(renderProgressBar(score || 0, false));
        subScoreList.appendChild(row);
    });
    scoreCard.appendChild(subScoreList);
    reportTarget.appendChild(scoreCard);

    const summaryCard = createElement("section", "result-card");
    summaryCard.appendChild(renderCardHeading("i", "Performance", "Summary"));
    summaryCard.appendChild(createElement("p", "summary-text", report.performance_summary || "No summary available."));
    if (report.detailed_feedback) summaryCard.appendChild(createElement("p", "summary-text", report.detailed_feedback));
    if (report.ai_error) summaryCard.appendChild(createElement("p", "summary-text", report.ai_error));
    if (report.evaluation_type === "Offline Evaluation" && report.id && options.setCurrent !== false) {
        const button = createElement("button", "compact-button", "Generate AI Evaluation");
        button.type = "button";
        button.addEventListener("click", () => generateAiEvaluation(report.id, button));
        summaryCard.appendChild(button);
    }
    reportTarget.appendChild(summaryCard);

    [
        ["+", "Strengths", report.strengths],
        ["!", "Weaknesses", report.weaknesses],
        ["=", "Section Feedback", report.section_wise_feedback],
        ["*", "Improved Sample Answers", report.improved_sample_answers],
        [">", "Improvement Plan", report.improvement_plan],
        ["*", "Suggested Better Answers", report.suggested_better_answers],
        ["#", "Learning Resources", report.learning_resources],
        ["C", "Suggested Courses", report.suggested_courses],
        ["R", "Roadmap", report.roadmap],
    ].forEach(([icon, title, items]) => {
        reportTarget.appendChild(renderDetailCard({ icon, label: title, title, type: "list", items: items || [] }));
    });

    (report.answers || []).forEach((answer, index) => {
        const card = createElement("section", "result-card");
        card.appendChild(renderCardHeading(String(index + 1), "Question Review", `${answer.score || 0}%`));
        card.appendChild(createElement("p", "summary-text", answer.question));
        card.appendChild(createElement("p", "summary-text", `Your answer: ${answer.answer || "Skipped"}`));
        card.appendChild(createElement("p", "summary-text", `Better answer: ${answer.better_answer || "No sample available."}`));
        reportTarget.appendChild(card);
    });

    reportArea.classList.remove("hidden");
    reportArea.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function generateAiEvaluation(interviewId, button) {
    if (!interviewId) return;
    button.disabled = true;
    button.textContent = "Generating...";
    try {
        const response = await fetch(`/interview/history/${interviewId}/generate-ai`, { method: "POST" });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || "Could not generate AI evaluation.");
        renderInterviewReport(data.report);
        showToast("AI evaluation generated.");
        loadDashboard();
        loadInterviewHistory();
    } catch (error) {
        showError(interviewError, error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Generate AI Evaluation";
    }
}

function startAptitudeTimer() {
    aptitudeStartedAt = Date.now();
    clearInterval(aptitudeTimerInterval);
    aptitudeTimerInterval = setInterval(() => {
        const total = Math.floor((Date.now() - aptitudeStartedAt) / 1000);
        const minutes = String(Math.floor(total / 60)).padStart(2, "0");
        const seconds = String(total % 60).padStart(2, "0");
        if (aptitudeTimer) aptitudeTimer.textContent = `${minutes}:${seconds}`;
    }, 1000);
}

async function startAptitude(payload) {
    const response = await fetch("/aptitude/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            candidate_name: payload.candidate_name,
            category: payload.aptitude_category || "Mixed",
            difficulty: payload.difficulty,
            question_count: payload.question_count,
        }),
    });
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.error || "Could not start aptitude test.");
    currentAptitude = {
        setup: data.setup,
        questions: data.questions,
        answerKey: data.answer_key,
        answers: {},
        startedAt: new Date().toISOString(),
    };
    currentAptitudeIndex = 0;
    currentAptitudeResult = null;
    interviewSession?.classList.add("hidden");
    interviewReportArea?.classList.add("hidden");
    aptitudeSession?.classList.remove("hidden");
    renderAptitudeQuestion();
    startAptitudeTimer();
    aptitudeSession?.scrollIntoView({ behavior: "smooth", block: "start" });
    showToast("Aptitude test ready.");
}

function persistAptitudeAnswer() {
    if (!currentAptitude) return;
    const selected = aptitudeOptions?.querySelector("input[name='aptitude-answer']:checked")?.value || "";
    if (selected) currentAptitude.answers[String(currentAptitudeIndex + 1)] = selected;
    sessionStorage.setItem("resumeiq-current-aptitude", JSON.stringify(currentAptitude));
}

function renderAptitudeQuestion() {
    if (!currentAptitude) return;
    const question = currentAptitude.questions[currentAptitudeIndex];
    aptitudeQuestionLabel.textContent = `Question ${currentAptitudeIndex + 1} of ${currentAptitude.questions.length}`;
    aptitudeMeta.textContent = `${question.category || currentAptitude.setup.category} - ${question.difficulty || currentAptitude.setup.difficulty}`;
    renderQuestionMeta(aptitudeQuestionMeta, [
        ["Question", `${currentAptitudeIndex + 1}/${currentAptitude.questions.length}`],
        ["Category", question.category || currentAptitude.setup.category],
        ["Topic", question.topic || "Placement aptitude"],
        ["Difficulty", question.difficulty || currentAptitude.setup.difficulty],
        ["Company Level", question.company_level || "Placement"],
        ["Time Limit", `${question.time_limit || 60}s`],
    ]);
    aptitudeQuestionText.textContent = question.question;
    aptitudeProgress.style.width = `${((currentAptitudeIndex + 1) / currentAptitude.questions.length) * 100}%`;
    aptitudeOptions.innerHTML = "";
    Object.entries(question.options || {}).forEach(([letter, text]) => {
        const label = createElement("label", "aptitude-option");
        const input = document.createElement("input");
        input.type = "radio";
        input.name = "aptitude-answer";
        input.value = letter;
        input.checked = currentAptitude.answers[String(currentAptitudeIndex + 1)] === letter;
        input.addEventListener("change", persistAptitudeAnswer);
        label.appendChild(input);
        label.appendChild(createElement("span", "", `${letter}. ${text}`));
        aptitudeOptions.appendChild(label);
    });
}

function moveAptitudeQuestion(delta) {
    if (!currentAptitude) return;
    persistAptitudeAnswer();
    currentAptitudeIndex = Math.max(0, Math.min(currentAptitudeIndex + delta, currentAptitude.questions.length - 1));
    renderAptitudeQuestion();
}

function skipAptitudeQuestion() {
    if (!currentAptitude) return;
    delete currentAptitude.answers[String(currentAptitudeIndex + 1)];
    moveAptitudeQuestion(1);
}

function renderAptitudeResult(result) {
    currentAptitudeResult = result;
    currentInterviewReport = null;
    interviewSummary.innerHTML = "";
    appendSummaryItem(interviewSummary, "Final Score", `${result.final_score || 0}%`);
    appendSummaryItem(interviewSummary, "Correct", result.correct_answers || 0);
    appendSummaryItem(interviewSummary, "Wrong", result.wrong_answers || 0);
    appendSummaryItem(interviewSummary, "Accuracy", `${result.accuracy || 0}%`);
    interviewReport.innerHTML = "";
    const scoreCard = createElement("section", "result-card score-card accent-card");
    scoreCard.appendChild(renderCardHeading("%", "Aptitude Score", `${result.final_score || 0}%`));
    scoreCard.appendChild(renderProgressBar(result.final_score || 0));
    interviewReport.appendChild(scoreCard);
    [
        ["+", "Strong Areas", result.strong_areas],
        ["!", "Weak Areas", result.weak_areas],
        ["#", "Topic-wise Performance", (result.topic_wise_performance || []).map((item) => `${item.topic}: ${item.accuracy}% (${item.correct}/${item.total})`)],
        [">", "Difficulty Analysis", (result.difficulty_analysis || []).map((item) => `${item.topic}: ${item.accuracy}% (${item.correct}/${item.total})`)],
    ].forEach(([icon, label, items]) => interviewReport.appendChild(renderDetailCard({ icon, label, title: label, type: "list", items: items || [] })));
    (result.questions || []).forEach((question, index) => {
        const card = createElement("section", "result-card");
        card.appendChild(renderCardHeading(String(index + 1), question.is_correct ? "Correct" : "Review", question.is_correct ? "Correct" : "Wrong"));
        card.appendChild(createElement("p", "summary-text", question.question));
        card.appendChild(createElement("p", "summary-text", `Selected: ${question.selected_answer || "Not answered"} | Correct: ${question.correct_answer}`));
        card.appendChild(createElement("p", "summary-text", question.explanation || ""));
        interviewReport.appendChild(card);
    });
    interviewReportArea.classList.remove("hidden");
    interviewReportArea.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function finishAptitude() {
    if (!currentAptitude) return;
    persistAptitudeAnswer();
    const button = document.querySelector("#finish-aptitude");
    button.disabled = true;
    button.textContent = "Scoring...";
    try {
        const response = await fetch("/aptitude/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                setup: currentAptitude.setup,
                questions: currentAptitude.answerKey,
                answers: currentAptitude.answers,
                started_at: currentAptitude.startedAt,
                finished_at: new Date().toISOString(),
            }),
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || "Could not evaluate aptitude test.");
        clearInterval(aptitudeTimerInterval);
        sessionStorage.removeItem("resumeiq-current-aptitude");
        renderAptitudeResult(data.result);
        showToast("Aptitude result ready.");
        loadDashboard();
    } catch (error) {
        showError(interviewError, error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Finish Aptitude Test";
    }
}

async function finishInterview() {
    if (!currentInterview) return;
    persistCurrentAnswer();
    if (!currentInterview.reviewed) {
        renderInterviewReview();
        showToast("Review your answers, then click Finish Interview again.");
        return;
    }
    const answers = currentInterview.questions.map((question, index) => ({
        question: question.question,
        answer: currentInterview.answers[index] || "",
        question_number: question.question_number || index + 1,
        difficulty: question.difficulty,
        type: question.type,
        category: question.category,
        topic: question.topic,
        expected_skills: question.expected_skills || [],
    }));
    if (!answers.some((item) => item.answer.trim())) {
        showError(interviewError, "Answer at least one question before finishing.");
        return;
    }
    const button = document.querySelector("#finish-interview");
    button.disabled = true;
    button.textContent = "Evaluating...";
    try {
        const response = await fetch("/interview/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ setup: currentInterview.setup, answers, session_id: currentInterview.sessionId }),
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || "Could not evaluate interview.");
        clearInterval(timerInterval);
        sessionStorage.removeItem("resumeiq-current-interview");
        renderInterviewReport(data.report);
        showToast(data.offline ? (data.message || "Your interview has been saved. Generate AI feedback later.") : "Interview evaluation complete.");
        loadDashboard();
    } catch (error) {
        showError(interviewError, error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Finish Interview";
    }
}

async function downloadInterviewReport() {
    if (currentAptitudeResult) {
        downloadInterviewReportButton.disabled = true;
        downloadInterviewReportButton.textContent = "Downloading...";
        try {
            const response = await fetch("/aptitude/report-pdf", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ result: currentAptitudeResult }),
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || "Could not download aptitude report.");
            }
            await downloadBlob(response, "resumeiq-plus-aptitude-report.pdf");
            showToast("Aptitude report downloaded.");
        } catch (error) {
            showError(interviewError, error.message);
        } finally {
            downloadInterviewReportButton.disabled = false;
            downloadInterviewReportButton.textContent = "Download Report";
        }
        return;
    }
    if (!currentInterviewReport) {
        showError(interviewError, "Finish an interview before downloading the report.");
        return;
    }
    downloadInterviewReportButton.disabled = true;
    downloadInterviewReportButton.textContent = "Downloading...";
    try {
        const response = await fetch("/interview/report-pdf", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ report: currentInterviewReport }),
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || "Could not download interview report.");
        }
        await downloadBlob(response, "resumeiq-plus-interview-report.pdf");
        showToast("Interview report downloaded.");
    } catch (error) {
        showError(interviewError, error.message);
    } finally {
        downloadInterviewReportButton.disabled = false;
        downloadInterviewReportButton.textContent = "Download Report";
    }
}

async function loadStoredInterviewReport(id) {
    hideError(interviewError);
    try {
        const response = await fetch(`/interview/history/${id}`);
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || "Could not load stored report.");
        renderInterviewReport(data.report, {
            summaryTarget: historyReportSummary,
            reportTarget: historyReportContent,
            reportArea: historyReportPreview,
            setCurrent: false,
        });
    } catch (error) {
        showError(interviewError, error.message);
    }
}

async function downloadStoredInterviewReport(id) {
    try {
        const response = await fetch(`/interview/history/${id}/report-pdf`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || "Could not download stored report.");
        }
        await downloadBlob(response, "resumeiq-plus-interview-report.pdf");
        showToast("Stored interview report downloaded.");
    } catch (error) {
        showError(interviewError, error.message);
    }
}

async function deleteStoredInterviewReport(id) {
    try {
        const response = await fetch(`/interview/history/${id}`, { method: "DELETE" });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || "Could not delete report.");
        showToast("Interview report deleted.");
        historyReportPreview?.classList.add("hidden");
        await loadInterviewHistory();
        await loadDashboard();
    } catch (error) {
        showError(interviewError, error.message);
    }
}

function toggleCustomRoleField() {
    const isCustom = interviewJobRole?.value === "Custom";
    customRoleField?.classList.toggle("hidden", !isCustom);
    const input = customRoleField?.querySelector("input");
    if (input) input.required = Boolean(isCustom);
    const typeSelect = interviewSetupForm?.querySelector("[name='interview_type']");
    const isAptitude = typeSelect?.value === "Aptitude Test";
    aptitudeCategoryField?.classList.toggle("hidden", !isAptitude);
}

function animateLiveCounter(counter) {
    if (!counter || counter.dataset.animated === "true") return;
    counter.dataset.animated = "true";
    const target = Number(counter.dataset.count) || 0;
    const duration = 1200;
    const startedAt = performance.now();
    const tick = (now) => {
        const progress = Math.min(1, (now - startedAt) / duration);
        const eased = 1 - Math.pow(1 - progress, 3);
        counter.textContent = String(Math.round(target * eased));
        if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
}

function initLandingAnimations() {
    const revealItems = document.querySelectorAll(".reveal-on-scroll");
    const counters = document.querySelectorAll(".live-counter");
    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add("is-visible");
                entry.target.querySelectorAll(".live-counter").forEach(animateLiveCounter);
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.12 });
        revealItems.forEach((item) => observer.observe(item));
    } else {
        revealItems.forEach((item) => item.classList.add("is-visible"));
        counters.forEach(animateLiveCounter);
    }

    document.querySelectorAll(".action-ripple").forEach((button) => {
        button.addEventListener("click", (event) => {
            const rect = button.getBoundingClientRect();
            const dot = createElement("span", "ripple-dot");
            dot.style.left = `${event.clientX - rect.left}px`;
            dot.style.top = `${event.clientY - rect.top}px`;
            button.appendChild(dot);
            setTimeout(() => dot.remove(), 650);
        });
    });
}

navLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
        event.preventDefault();
        const view = link.dataset.viewLink;
        history.replaceState(null, "", `#${view}`);
        setView(view);
        if (link.dataset.builderJump) setBuilderTab(link.dataset.builderJump);
    });
});

menuToggle?.addEventListener("click", toggleSidebar);
sidebarOverlay?.addEventListener("click", closeMobileSidebar);
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMobileSidebar();
});
desktopSidebarQuery.addEventListener?.("change", () => {
    closeMobileSidebar();
    setDesktopSidebarCollapsed(localStorage.getItem("resumeiq-sidebar-open") !== "true", false);
});
themeToggle?.addEventListener("click", () => setTheme(document.body.classList.contains("light") ? "dark" : "light"));
const profileMenu = document.querySelector("#profile-menu");
const profileMenuTrigger = document.querySelector("#profile-menu-trigger");
profileMenuTrigger?.addEventListener("click", () => {
    const open = profileMenu?.classList.toggle("is-open");
    profileMenuTrigger.setAttribute("aria-expanded", open ? "true" : "false");
});
document.addEventListener("click", (event) => {
    if (!profileMenu?.contains(event.target)) {
        profileMenu?.classList.remove("is-open");
        profileMenuTrigger?.setAttribute("aria-expanded", "false");
    }
});
document.querySelectorAll("[data-profile-view]").forEach((link) => link.addEventListener("click", (event) => {
    event.preventDefault();
    const view = link.dataset.profileView;
    history.replaceState(null, "", `#${view}`);
    setView(view);
    profileMenu?.classList.remove("is-open");
    profileMenuTrigger?.setAttribute("aria-expanded", "false");
}));
document.querySelector("#profile-theme-toggle")?.addEventListener("click", () => {
    setTheme(document.body.classList.contains("light") ? "dark" : "light");
    profileMenu?.classList.remove("is-open");
});
document.querySelectorAll('a[href="/logout"]').forEach((link) => link.addEventListener("click", () => {
    // Saved records stay in the database; only this browser session's transient state is removed.
    sessionStorage.removeItem("resumeiq-current-interview");
    localStorage.removeItem(builderDraftKey());
}));
themeSelect?.addEventListener("change", () => setTheme(themeSelect.value));
accentPicker?.addEventListener("input", () => setAccent(accentPicker.value));
accentThemeSelect?.addEventListener("change", () => setAccent(accentThemeSelect.value));
document.querySelector("#refresh-dashboard")?.addEventListener("click", loadDashboard);
document.querySelector("#refresh-interview-history")?.addEventListener("click", loadInterviewHistory);
document.querySelector("#refresh-resumes")?.addEventListener("click", () => loadResumeLibrary().catch((error) => showToast(error.message)));
document.querySelector("#global-search-button")?.addEventListener("click", () => runGlobalSearch().catch((error) => showToast(error.message)));
document.querySelector("#refresh-admin")?.addEventListener("click", () => loadAdminDashboard().catch((error) => showToast(error.message)));
document.querySelector("#refresh-jobs")?.addEventListener("click", () => loadJobs().catch((error) => showToast(error.message)));
jobForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const response = await fetch("/api/jobs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formToObject(jobForm)) });
    const data = await response.json();
    if (!response.ok || !data.success) return showToast(data.error || "Could not add application.");
    jobForm.reset();
    showToast("Job added to your tracker.");
    loadJobs();
});
document.querySelector("#profile-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const response = await fetch("/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formToObject(event.currentTarget)),
    });
    const data = await response.json();
    if (!response.ok || !data.success) return showToast(data.error || "Could not save profile.");
    showToast("Profile saved.");
    await loadDashboard();
});
document.querySelector("#profile-image-input")?.addEventListener("change", async (event) => {
    const image = event.target.files?.[0];
    if (!image) return;
    const formData = new FormData();
    formData.append("profile_image", image);
    try {
        const response = await fetch("/api/profile/image", { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || "Could not upload profile image.");
        updateProfileAvatars(data.profile || {});
        showToast(data.message || "Profile image updated.");
    } catch (error) {
        showToast(error.message);
    } finally {
        event.target.value = "";
    }
});
document.querySelector("#onboarding-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const response = await fetch("/api/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formToObject(event.currentTarget)),
    });
    const data = await response.json();
    if (!response.ok || !data.success) return showToast(data.error || "Could not complete onboarding.");
    showToast("Onboarding complete.");
    await loadDashboard();
});
document.querySelector("#notification-select")?.addEventListener("change", async (event) => {
    await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notifications: event.target.value }),
    });
    showToast("Notification settings saved.");
});
interviewJobRole?.addEventListener("change", toggleCustomRoleField);
interviewSetupForm?.querySelector("[name='interview_type']")?.addEventListener("change", toggleCustomRoleField);

resumeInput?.addEventListener("change", () => {
    const file = resumeInput.files?.[0];
    fileName.textContent = file ? `${file.name} selected` : "Required PDF, max 8 MB";
});

compareResumeInput?.addEventListener("change", () => {
    const file = compareResumeInput.files?.[0];
    compareFileName.textContent = file ? `${file.name} selected` : "Optional PDF comparison";
});

uploadForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideError(errorMessage);
    clearResults();
    setLoading(true);
    try {
        const response = await fetch("/analyze", { method: "POST", body: new FormData(uploadForm) });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || "Resume analysis failed. Please try again.");
        renderResults(data);
    } catch (error) {
        showError(errorMessage, error.message);
    } finally {
        setLoading(false);
    }
});

exportButton?.addEventListener("click", exportPDF);
document.querySelectorAll("[data-ai-action]").forEach((button) => {
    button.addEventListener("click", () => runAiAssist(button.dataset.aiAction));
});
downloadResumeButton?.addEventListener("click", downloadResumePdf);
downloadDocxButton?.addEventListener("click", downloadResumeDocx);
document.querySelector("#export-tab-pdf")?.addEventListener("click", downloadResumePdf);
document.querySelector("#export-tab-docx")?.addEventListener("click", downloadResumeDocx);
saveDraftButton?.addEventListener("click", () => {
    saveBuilderDraft();
    showToast("Draft saved locally.");
});
builderTabButtons.forEach((button) => {
    button.addEventListener("click", () => setBuilderTab(button.dataset.builderTab));
});
templateSelect?.addEventListener("change", () => applyTemplate(templateSelect.value));
colorThemeSelect?.addEventListener("change", () => {
    const accentInput = builderForm?.querySelector("[name='accent_color']");
    if (accentInput) accentInput.value = colorThemeSelect.value;
    updateResumePreview();
    saveBuilderDraft();
});
builderForm?.querySelector("[name='accent_color']")?.addEventListener("input", (event) => {
    if (colorThemeSelect) colorThemeSelect.value = event.target.value;
});
builderForm?.addEventListener("input", () => {
    updateResumePreview();
    clearTimeout(window.resumeiqSaveTimer);
    window.resumeiqSaveTimer = setTimeout(saveBuilderDraft, 600);
});

interviewSetupForm?.addEventListener("submit", startInterview);
document.querySelector("#prev-question")?.addEventListener("click", () => moveQuestion(-1));
document.querySelector("#next-question")?.addEventListener("click", () => moveQuestion(1));
document.querySelector("#skip-question")?.addEventListener("click", skipQuestion);
document.querySelector("#bookmark-question")?.addEventListener("click", bookmarkQuestion);
document.querySelector("#voice-answer")?.addEventListener("click", startVoiceAnswer);
document.querySelector("#pause-voice")?.addEventListener("click", pauseVoiceAnswer);
document.querySelector("#resume-voice")?.addEventListener("click", resumeVoiceAnswer);
document.querySelector("#stop-voice")?.addEventListener("click", stopVoiceAnswer);
document.querySelector("#review-interview")?.addEventListener("click", renderInterviewReview);
document.querySelector("#finish-interview")?.addEventListener("click", finishInterview);
document.querySelector("#prev-aptitude-question")?.addEventListener("click", () => moveAptitudeQuestion(-1));
document.querySelector("#next-aptitude-question")?.addEventListener("click", () => moveAptitudeQuestion(1));
document.querySelector("#skip-aptitude-question")?.addEventListener("click", skipAptitudeQuestion);
document.querySelector("#finish-aptitude")?.addEventListener("click", finishAptitude);
downloadInterviewReportButton?.addEventListener("click", downloadInterviewReport);
interviewAnswer?.addEventListener("input", () => {
    persistCurrentAnswer();
    renderAnswerWritingAssistant();
});

setDesktopSidebarCollapsed(localStorage.getItem("resumeiq-sidebar-open") !== "true", false);
setTheme(localStorage.getItem("resumeiq-theme") || "dark");
setAccent(localStorage.getItem("resumeiq-accent") || "#24c6a8");
toggleCustomRoleField();
if (builderForm) {
    renderBuilderSections();
    renderTemplateGallery();
    loadBuilderDraft();
    syncTemplateSelection();
    setBuilderTab("profile");
}
initLandingAnimations();
if (views.length) {
    setView(location.hash.replace("#", "") || initialView || "home");
    if (isAuthenticated) {
        loadDashboard();
        loadInterviewHistory();
        loadResumeLibrary().catch(() => {});
        loadJobs().catch(() => {});
        loadAdminDashboard().catch(() => {});
    }
}
