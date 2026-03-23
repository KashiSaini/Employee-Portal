function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener("DOMContentLoaded", function () {
    const logoutBtn = document.querySelector("[data-api-logout]");
    const signOffBtn = document.querySelector("[data-api-signoff]");
    const summaryBox = document.querySelector("[data-signoff-summary]");

    async function postAction(url) {
        const csrfToken = getCookie("csrftoken");

        const response = await fetch(url, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "X-CSRFToken": csrfToken,
                "Accept": "application/json"
            }
        });

        return await response.json();
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", async function (event) {
            event.preventDefault();
            const data = await postAction(logoutBtn.dataset.apiLogout);
            window.location.href = data.redirect_url || "/";
        });
    }

    if (signOffBtn) {
        signOffBtn.addEventListener("click", async function (event) {
            event.preventDefault();
            const data = await postAction(signOffBtn.dataset.apiSignoff);

            if (summaryBox) {
                summaryBox.innerHTML = `
                    <div class="form-card mt-20">
                        <div class="section-card-header">
                            <h3>Today's Work Summary</h3>
                        </div>
                        <div class="detail-grid">
                            <div class="detail-item"><span>Date</span><strong>${data.work_date || "-"}</strong></div>
                            <div class="detail-item"><span>First Login</span><strong>${data.first_login || "-"}</strong></div>
                            <div class="detail-item"><span>Sign Off Time</span><strong>${data.sign_off_time || "-"}</strong></div>
                            <div class="detail-item"><span>Total Worked Hours</span><strong>${data.total_work_hours || "00:00"}</strong></div>
                            <div class="detail-item"><span>Work Mode</span><strong>${data.work_mode || "-"}</strong></div>
                            <div class="detail-item"><span>Status</span><strong>${data.is_signed_off ? "Signed Off" : "Open"}</strong></div>
                        </div>
                    </div>
                `;
                summaryBox.scrollIntoView({ behavior: "smooth" });
            }
        });
    }
});