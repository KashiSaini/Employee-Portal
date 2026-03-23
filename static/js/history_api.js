function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function normalizeList(data) {
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.results)) return data.results;
    return [];
}

async function fetchList(url) {
    const response = await fetch(url, {
        credentials: "same-origin",
        headers: { "Accept": "application/json" }
    });

    if (!response.ok) {
        throw new Error(`Unable to load list from ${url}`);
    }

    return normalizeList(await response.json());
}

function buildUrl(pattern, id) {
    return pattern.replace("/0/", `/${id}/`);
}

function badge(status, label) {
    return `<span class="status-badge status-${escapeHtml((status || "").toLowerCase())}">${escapeHtml(label || status || "-")}</span>`;
}

function getUserLabel(item) {
    return (
        item.user_display ||
        item.user_name ||
        item.employee_name ||
        item.employee ||
        item.full_name ||
        item.user ||
        "-"
    );
}

function setHtml(selector, html) {
    const el = document.querySelector(selector);
    if (el) {
        el.innerHTML = html;
    }
}

function setText(selector, value) {
    const el = document.querySelector(selector);
    if (el) {
        el.textContent = value;
    }
}

function renderClaims(page, items) {
    setText("[data-total-claims]", items.length);
    setText("[data-pending-claims]", items.filter(i => i.status === "pending").length);

    setHtml("#claims-table-body", items.map(item => `
        <tr>
            <td>${escapeHtml(item.title)}</td>
            <td>${escapeHtml(item.claim_type_display || item.claim_type)}</td>
            <td>₹${escapeHtml(item.amount)}</td>
            <td>${escapeHtml(item.expense_date)}</td>
            <td>
                ${item.receipt_url
                    ? `<a href="${item.receipt_url}" target="_blank" class="receipt-link">View Receipt</a>`
                    : '<span class="muted-text">No file</span>'}
            </td>
            <td>${badge(item.status, item.status_display)}</td>
            <td>${escapeHtml(item.submitted_at || "")}</td>
            <td>
                <div class="table-actions">
                    <a href="${buildUrl(page.dataset.editPattern, item.id)}" class="btn-table-edit">Edit</a>
                    <a href="${buildUrl(page.dataset.deletePattern, item.id)}" class="btn-table-delete">Delete</a>
                </div>
            </td>
        </tr>
        <tr class="claim-desc-row">
            <td colspan="8"><strong>Description:</strong> ${escapeHtml(item.description || "-")}</td>
        </tr>
    `).join("") || `<tr><td colspan="8" class="empty-cell">No claims found.</td></tr>`);
}

function renderTimesheet(page, items) {
    setHtml("#timesheet-table-body", items.map(item => `
        <tr>
            <td>${escapeHtml(item.project_name || item.project)}</td>
            <td>${escapeHtml(item.work_date)}</td>
            <td>${escapeHtml(item.hours)}</td>
            <td>${escapeHtml(item.description || "")}</td>
            <td>${badge(item.status, item.status_display)}</td>
            <td>${escapeHtml(item.updated_at || "")}</td>
            <td>
                <div class="table-actions">
                    <a href="${buildUrl(page.dataset.editPattern, item.id)}" class="btn-table-edit">Edit</a>
                    <a href="${buildUrl(page.dataset.deletePattern, item.id)}" class="btn-table-delete">Delete</a>
                </div>
            </td>
        </tr>
    `).join("") || `<tr><td colspan="7" class="empty-cell">No timesheet entries found.</td></tr>`);
}

function renderLeave(page, leaves, shortLeaves) {
    setText("[data-total-leaves]", leaves.length);
    setText("[data-total-short-leaves]", shortLeaves.length);

    setHtml("#leave-table-body", leaves.map(item => `
        <tr>
            <td>${escapeHtml(item.leave_type_display || item.leave_type)}</td>
            <td>${escapeHtml(item.start_date)}</td>
            <td>${escapeHtml(item.end_date)}</td>
            <td>${escapeHtml(item.total_days)}</td>
            <td>${badge(item.status, item.status_display)}</td>
            <td>${escapeHtml(item.reason || "")}</td>
            <td>${escapeHtml(item.applied_at || "")}</td>
        </tr>
    `).join("") || `<tr><td colspan="7" class="empty-cell">No leave requests found.</td></tr>`);

    setHtml("#short-leave-table-body", shortLeaves.map(item => `
        <tr>
            <td>${escapeHtml(item.leave_date)}</td>
            <td>${escapeHtml(item.start_time)}</td>
            <td>${escapeHtml(item.end_time)}</td>
            <td>${badge(item.status, item.status_display)}</td>
            <td>${escapeHtml(item.reason || "")}</td>
            <td>${escapeHtml(item.applied_at || "")}</td>
        </tr>
    `).join("") || `<tr><td colspan="6" class="empty-cell">No short leave requests found.</td></tr>`);
}

function renderWFH(page, items) {
    setText("[data-total-wfh]", items.length);
    setText("[data-pending-wfh]", items.filter(i => i.status === "pending").length);

    setHtml("#wfh-table-body", items.map(item => `
        <tr>
            <td>${escapeHtml(item.start_date)}</td>
            <td>${escapeHtml(item.end_date)}</td>
            <td>${escapeHtml(item.total_days)}</td>
            <td>${escapeHtml(item.reason || "")}</td>
            <td>${escapeHtml(item.work_plan || "-")}</td>
            <td>${badge(item.status, item.status_display)}</td>
            <td>${escapeHtml(item.applied_at || "")}</td>
            <td>
                <div class="table-actions">
                    <a href="${buildUrl(page.dataset.editPattern, item.id)}" class="btn-table-edit">Edit</a>
                    <a href="${buildUrl(page.dataset.deletePattern, item.id)}" class="btn-table-delete">Delete</a>
                </div>
            </td>
        </tr>
    `).join("") || `<tr><td colspan="8" class="empty-cell">No WFH requests found.</td></tr>`);
}

function renderApprovalDashboard(page, leaves, shortLeaves, timesheets, claims, wfh) {
    setText("[data-approval-total]", leaves.length + shortLeaves.length + timesheets.length + claims.length + wfh.length);
    setText("[data-approval-leave]", leaves.length);
    setText("[data-approval-short-leave]", shortLeaves.length);
    setText("[data-approval-timesheet]", timesheets.length);
    setText("[data-approval-claim]", claims.length);
    setText("[data-approval-wfh]", wfh.length);

    setHtml("#approval-leave-body", leaves.slice(0, 5).map(item => `
        <tr>
            <td>${escapeHtml(getUserLabel(item))}</td>
            <td>${escapeHtml(item.leave_type_display || item.leave_type)}</td>
            <td>${escapeHtml(item.start_date)}</td>
            <td>${escapeHtml(item.end_date)}</td>
            <td>${escapeHtml(item.total_days)}</td>
            <td>${escapeHtml(item.reason || "")}</td>
            <td><a href="${buildUrl(page.dataset.leaveReviewPattern, item.id)}" class="btn-table-review">Review</a></td>
        </tr>
    `).join("") || `<tr><td colspan="7" class="empty-cell">No pending leave requests.</td></tr>`);

    setHtml("#approval-short-leave-body", shortLeaves.slice(0, 5).map(item => `
        <tr>
            <td>${escapeHtml(getUserLabel(item))}</td>
            <td>${escapeHtml(item.leave_date)}</td>
            <td>${escapeHtml(item.start_time)}</td>
            <td>${escapeHtml(item.end_time)}</td>
            <td>${escapeHtml(item.reason || "")}</td>
            <td><a href="${buildUrl(page.dataset.shortLeaveReviewPattern, item.id)}" class="btn-table-review">Review</a></td>
        </tr>
    `).join("") || `<tr><td colspan="6" class="empty-cell">No pending short leave requests.</td></tr>`);

    setHtml("#approval-timesheet-body", timesheets.slice(0, 5).map(item => `
        <tr>
            <td>${escapeHtml(getUserLabel(item))}</td>
            <td>${escapeHtml(item.project_name || item.project)}</td>
            <td>${escapeHtml(item.work_date)}</td>
            <td>${escapeHtml(item.hours)}</td>
            <td>${escapeHtml(item.description || "")}</td>
            <td><a href="${buildUrl(page.dataset.timesheetReviewPattern, item.id)}" class="btn-table-review">Review</a></td>
        </tr>
    `).join("") || `<tr><td colspan="6" class="empty-cell">No pending time sheet entries.</td></tr>`);

    setHtml("#approval-claim-body", claims.slice(0, 5).map(item => `
        <tr>
            <td>${escapeHtml(getUserLabel(item))}</td>
            <td>${escapeHtml(item.title)}</td>
            <td>${escapeHtml(item.claim_type_display || item.claim_type)}</td>
            <td>₹${escapeHtml(item.amount)}</td>
            <td>${escapeHtml(item.expense_date)}</td>
            <td><a href="${buildUrl(page.dataset.claimReviewPattern, item.id)}" class="btn-table-review">Review</a></td>
        </tr>
    `).join("") || `<tr><td colspan="6" class="empty-cell">No pending claims.</td></tr>`);

    setHtml("#approval-wfh-body", wfh.slice(0, 5).map(item => `
        <tr>
            <td>${escapeHtml(getUserLabel(item))}</td>
            <td>${escapeHtml(item.start_date)}</td>
            <td>${escapeHtml(item.end_date)}</td>
            <td>${escapeHtml(item.total_days)}</td>
            <td>${escapeHtml(item.reason || "")}</td>
            <td><a href="${buildUrl(page.dataset.wfhReviewPattern, item.id)}" class="btn-table-review">Review</a></td>
        </tr>
    `).join("") || `<tr><td colspan="6" class="empty-cell">No pending WFH requests.</td></tr>`);
}

document.addEventListener("DOMContentLoaded", async function () {
    const page = document.querySelector("[data-history-page]");
    if (!page) return;

    const type = page.dataset.historyPage;

    try {
        if (type === "claims") {
            const items = await fetchList(page.dataset.apiUrl);
            renderClaims(page, items);
        }

        if (type === "timesheet") {
            const items = await fetchList(page.dataset.apiUrl);
            renderTimesheet(page, items);
        }

        if (type === "leave") {
            const [leaves, shortLeaves] = await Promise.all([
                fetchList(page.dataset.leaveApiUrl),
                fetchList(page.dataset.shortLeaveApiUrl),
            ]);
            renderLeave(page, leaves, shortLeaves);
        }

        if (type === "wfh") {
            const items = await fetchList(page.dataset.apiUrl);
            renderWFH(page, items);
        }

        if (type === "approval-dashboard") {
            const [leaves, shortLeaves, timesheets, claims, wfh] = await Promise.all([
                fetchList(page.dataset.leaveApiUrl),
                fetchList(page.dataset.shortLeaveApiUrl),
                fetchList(page.dataset.timesheetApiUrl),
                fetchList(page.dataset.claimApiUrl),
                fetchList(page.dataset.wfhApiUrl),
            ]);

            renderApprovalDashboard(page, leaves, shortLeaves, timesheets, claims, wfh);
        }
    } catch (error) {
        console.error(error);

        if (type === "claims") {
            setHtml("#claims-table-body", `<tr><td colspan="8" class="empty-cell">Failed to load claims.</td></tr>`);
        }

        if (type === "timesheet") {
            setHtml("#timesheet-table-body", `<tr><td colspan="7" class="empty-cell">Failed to load time sheet entries.</td></tr>`);
        }

        if (type === "leave") {
            setHtml("#leave-table-body", `<tr><td colspan="7" class="empty-cell">Failed to load leave requests.</td></tr>`);
            setHtml("#short-leave-table-body", `<tr><td colspan="6" class="empty-cell">Failed to load short leave requests.</td></tr>`);
        }

        if (type === "wfh") {
            setHtml("#wfh-table-body", `<tr><td colspan="8" class="empty-cell">Failed to load WFH requests.</td></tr>`);
        }

        if (type === "approval-dashboard") {
            setHtml("#approval-leave-body", `<tr><td colspan="7" class="empty-cell">Failed to load pending leave requests.</td></tr>`);
            setHtml("#approval-short-leave-body", `<tr><td colspan="6" class="empty-cell">Failed to load pending short leave requests.</td></tr>`);
            setHtml("#approval-timesheet-body", `<tr><td colspan="6" class="empty-cell">Failed to load pending time sheet entries.</td></tr>`);
            setHtml("#approval-claim-body", `<tr><td colspan="6" class="empty-cell">Failed to load pending claims.</td></tr>`);
            setHtml("#approval-wfh-body", `<tr><td colspan="6" class="empty-cell">Failed to load pending WFH requests.</td></tr>`);
        }
    }
});