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
    const form = document.querySelector("[data-login-api-form]");
    if (!form) return;

    const messageBox = document.querySelector("[data-login-message]");
    const submitBtn = form.querySelector('button[type="submit"]');

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const csrfToken = getCookie("csrftoken");
        const formData = new FormData(form);

        if (messageBox) {
            messageBox.style.display = "none";
            messageBox.className = "login-error";
            messageBox.textContent = "";
        }

        submitBtn.disabled = true;
        const oldText = submitBtn.textContent;
        submitBtn.textContent = "Logging in...";

        try {
            const response = await fetch(form.dataset.apiUrl, {
                method: "POST",
                body: formData,
                credentials: "same-origin",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "Accept": "application/json"
                }
            });

            const data = await response.json().catch(() => ({}));

            if (response.ok) {
                window.location.href = data.redirect_url || "/dashboard/";
                return;
            }

            if (messageBox) {
                messageBox.style.display = "block";
                messageBox.textContent = data.detail || "Login failed.";
            }
        } catch (error) {
            if (messageBox) {
                messageBox.style.display = "block";
                messageBox.textContent = "Network error. Please try again.";
            }
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = oldText;
        }
    });
});