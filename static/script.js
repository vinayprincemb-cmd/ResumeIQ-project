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

let currentExportPayload = null;

function createElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    if (text !== undefined && text !== null) {
        element.textContent = text;
    }

    return element;
}

function setLoading(isLoading) {
    uploadForm.classList.toggle("is-loading", isLoading);
    submitButton.disabled = isLoading;
    buttonText.textContent = isLoading ? "Analyzing..." : "Analyze Resume";
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
}

function hideError() {
    errorMessage.textContent = "";
    errorMessage.classList.add("hidden");
}

function clearResults() {
    summaryBar.innerHTML = "";
    reportsLayout.innerHTML = "";
    resultsContainer.classList.add("hidden");
    reportsLayout.classList.remove("compare-layout");
    currentExportPayload = null;
}

function scoreClass(score) {
    if (score >= 80) {
        return "score-high";
    }

    if (score >= 55) {
        return "score-mid";
    }

    return "score-low";
}

function appendSummaryItem(label, value) {
    const item = createElement("div");
    item.appendChild(createElement("span", "", label));
    item.appendChild(createElement("strong", "", value));
    summaryBar.appendChild(item);
}

function renderSummary(data) {
    summaryBar.innerHTML = "";
    appendSummaryItem("Target Role", data.job_role || "Not provided");

    [data.result, data.comparison].filter(Boolean).forEach((report) => {
        const score = report.ats_score !== null && report.ats_score !== undefined ? `${report.ats_score}%` : "N/A";
        appendSummaryItem(report.label || "Resume", score);
    });
}

function renderProgressBar(score, large = true) {
    const track = createElement("div", large ? "progress-track" : "mini-progress");
    const bar = createElement("div", large ? `progress-bar ${scoreClass(score)}` : "");
    bar.style.width = `${score || 0}%`;
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

function renderScoreCard(report) {
    if (report.ats_score === null || report.ats_score === undefined) {
        return null;
    }

    const card = createElement("section", "result-card score-card priority-card");
    const heading = renderCardHeading("%", "ATS Score", `${report.ats_score}%`);
    card.appendChild(heading);
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

    card.appendChild(subScoreList);
    return card;
}

function renderKeywordCard(report) {
    if (!report.important_keywords || report.important_keywords.length === 0) {
        return null;
    }

    const card = createElement("section", "result-card keyword-card");
    card.appendChild(renderCardHeading("*", "Important Keywords", "Role Signals"));

    const chipList = createElement("div", "chip-list");
    report.important_keywords.forEach((keyword) => {
        chipList.appendChild(createElement("span", "", keyword));
    });
    card.appendChild(chipList);

    return card;
}

function renderDetailCard(section) {
    const card = createElement("details", `result-card detail-card ${section.key === "missing_skills" ? "priority-card" : ""}`);

    if (section.key === "missing_skills") {
        card.open = true;
    }

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
        (section.items || []).forEach((item) => {
            list.appendChild(createElement("li", "", item));
        });
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

    const scoreCard = renderScoreCard(report);
    if (scoreCard) {
        column.appendChild(scoreCard);
    }

    const keywordCard = renderKeywordCard(report);
    if (keywordCard) {
        column.appendChild(keywordCard);
    }

    (report.sections || []).forEach((section) => {
        column.appendChild(renderDetailCard(section));
    });

    return column;
}

function renderResults(data) {
    clearResults();
    currentExportPayload = data.export_payload;

    renderSummary(data);

    const reports = [data.result, data.comparison].filter(Boolean);
    reportsLayout.classList.toggle("compare-layout", reports.length > 1);
    reports.forEach((report) => {
        reportsLayout.appendChild(renderReport(report));
    });

    resultsContainer.classList.remove("hidden");
    resultsContainer.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function exportPDF() {
    if (!currentExportPayload) {
        showError("Please analyze a resume before exporting the PDF.");
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

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "resumeiq-report.pdf";
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    } catch (error) {
        showError(error.message);
    } finally {
        exportButton.disabled = false;
        exportButton.textContent = "Export PDF";
    }
}

resumeInput?.addEventListener("change", () => {
    const file = resumeInput.files?.[0];
    fileName.textContent = file ? file.name : "Choose primary resume";
});

compareResumeInput?.addEventListener("change", () => {
    const file = compareResumeInput.files?.[0];
    compareFileName.textContent = file ? file.name : "Add second resume";
});

uploadForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideError();
    clearResults();

    const formData = new FormData(uploadForm);

    setLoading(true);

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Resume analysis failed. Please try again.");
        }

        renderResults(data);
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
});

exportButton?.addEventListener("click", exportPDF);
