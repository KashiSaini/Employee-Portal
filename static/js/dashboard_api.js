function qs(selector) {
    return document.querySelector(selector);
}

function setText(selector, value) {
    const el = qs(selector);
    if (el) {
        el.textContent = value ?? "-";
    }
}

function setHtml(selector, value) {
    const el = qs(selector);
    if (el) {
        el.innerHTML = value;
    }
}

function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

document.addEventListener("DOMContentLoaded", async function () {
    const page = qs("[data-dashboard-page]");
    if (!page) return;

    try {
        const response = await fetch(page.dataset.apiUrl, {
            credentials: "same-origin",
            headers: { "Accept": "application/json" }
        });

        if (!response.ok) {
            throw new Error("Dashboard API failed.");
        }

        const data = await response.json();

        // Profile
        setText("[data-dashboard-name]", data.profile?.full_name || "-");
        setText("[data-dashboard-employee-id]", data.profile?.employee_id || "-");
        setText("[data-dashboard-email]", data.profile?.email || "-");
        setText("[data-dashboard-phone]", data.profile?.phone || "-");
        setText("[data-dashboard-department]", data.profile?.department || "-");
        setText("[data-dashboard-designation]", data.profile?.designation || "-");
        setText("[data-dashboard-join-date]", data.profile?.join_date || "-");
        setText("[data-dashboard-dob]", data.profile?.date_of_birth || "-");
        setText("[data-dashboard-work-mode]", data.profile?.work_mode || "-");
        setText("[data-dashboard-profile-completion]", `${data.profile?.completion_percentage ?? 0}%`);

        const fillBar = qs("[data-dashboard-profile-fill]");
        if (fillBar) {
            fillBar.style.width = `${data.profile?.completion_percentage ?? 0}%`;
        }

        // Counts
        setText("[data-dashboard-pending-total]", data.employee_counts?.pending_total ?? 0);
        setText("[data-dashboard-leave-total]", data.employee_counts?.leave_total ?? 0);
        setText("[data-dashboard-short-leave-total]", data.employee_counts?.short_leave_total ?? 0);
        setText("[data-dashboard-timesheet-total]", data.employee_counts?.timesheet_total ?? 0);
        setText("[data-dashboard-claim-total]", data.employee_counts?.claim_total ?? 0);
        setText("[data-dashboard-wfh-total]", data.employee_counts?.wfh_total ?? 0);

        // Alerts
        const alerts = Array.isArray(data.alerts) ? data.alerts : [];
        setHtml(
            "[data-dashboard-alerts]",
            alerts.length
                ? alerts.map(item => `<li>${escapeHtml(item)}</li>`).join("")
                : "<li>No alerts available.</li>"
        );

        // Birthdays
        const birthdays = Array.isArray(data.birthdays) ? data.birthdays : [];
        setHtml(
            "[data-dashboard-birthdays]",
            birthdays.length
                ? birthdays.map(item => `
                    <div class="mini-list-item">
                        <div>
                            <strong>${escapeHtml(item.name)}</strong>
                            <p>${escapeHtml(item.days_left)} day(s) left</p>
                        </div>
                        <span>${escapeHtml(item.date)}</span>
                    </div>
                `).join("")
                : "<p>No birthday data available.</p>"
        );

        // Anniversaries
        const anniversaries = Array.isArray(data.anniversaries) ? data.anniversaries : [];
        setHtml(
            "[data-dashboard-anniversaries]",
            anniversaries.length
                ? anniversaries.map(item => `
                    <div class="mini-list-item">
                        <div>
                            <strong>${escapeHtml(item.name)}</strong>
                            <p>${escapeHtml(item.years)} year(s)</p>
                        </div>
                        <span>${escapeHtml(item.date)}</span>
                    </div>
                `).join("")
                : "<p>No anniversary data available.</p>"
        );

        // Recent activity
        const activity = Array.isArray(data.recent_activity) ? data.recent_activity : [];
        setHtml(
            "[data-dashboard-activity]",
            activity.length
                ? activity.map(item => `
                    <div class="activity-item">
                        <div>
                            <strong>${escapeHtml(item.title)}</strong>
                            <p>${escapeHtml(item.meta)}</p>
                        </div>
                        <span class="status-badge status-${escapeHtml((item.status || "").toLowerCase())}">
                            ${escapeHtml(item.status || "-")}
                        </span>
                    </div>
                `).join("")
                : `<div class="empty-activity">No recent activity found.</div>`
        );

        // Today's work status
        const workStatusHtml = `
            <div class="mini-list">
                <div class="mini-list-item">
                    <div>
                        <strong>First Login</strong>
                        <p>${escapeHtml(data.today_work_log?.first_login || "-")}</p>
                    </div>
                    <span>${escapeHtml(data.today_work_log?.total_work_hours || "00:00")}</span>
                </div>

                <div class="mini-list-item">
                    <div>
                        <strong>Signed Off</strong>
                        <p>${data.today_work_log?.is_signed_off ? "Yes" : "No"}</p>
                    </div>
                    <span>${escapeHtml(data.profile?.work_mode || "-")}</span>
                </div>
            </div>
        `;
        setHtml("[data-dashboard-work-status]", workStatusHtml);

        // Approval section
        const approvalSection = qs("[data-dashboard-approvals]");
        if (approvalSection) {
            if (data.can_review) {
                approvalSection.style.display = "block";
                setText("[data-dashboard-approval-total]", data.approval_counts?.total ?? 0);
                setText("[data-dashboard-approval-leave]", data.approval_counts?.leave ?? 0);
                setText("[data-dashboard-approval-short-leave]", data.approval_counts?.short_leave ?? 0);
                setText("[data-dashboard-approval-timesheet]", data.approval_counts?.timesheet ?? 0);
                setText("[data-dashboard-approval-claim]", data.approval_counts?.claim ?? 0);
                setText("[data-dashboard-approval-wfh]", data.approval_counts?.wfh ?? 0);
            } else {
                approvalSection.style.display = "none";
            }
        }

    } catch (error) {
        console.error("Dashboard API Error:", error);

        setHtml("[data-dashboard-work-status]", "<p>Failed to load work status.</p>");
        setHtml("[data-dashboard-birthdays]", "<p>Failed to load birthdays.</p>");
        setHtml("[data-dashboard-anniversaries]", "<p>Failed to load anniversaries.</p>");
        setHtml("[data-dashboard-activity]", `<div class="empty-activity">Failed to load recent activity.</div>`);
    }
});