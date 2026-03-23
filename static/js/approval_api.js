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
    const form = document.querySelector("[data-review-form]");
    if (!form) return;

    const messageBox = document.querySelector("[data-api-message]");
    const approveBtn = form.querySelector('[data-review-action="approve"]');
    const rejectBtn = form.querySelector('[data-review-action="reject"]');
    const redirectUrl = form.dataset.redirectUrl;

    async function submitReview(action) {
        const url = action === "approve" ? form.dataset.approveUrl : form.dataset.rejectUrl;
        const csrfToken = getCookie("csrftoken");
        const formData = new FormData(form);

        if (messageBox) {
            messageBox.style.display = "none";
            messageBox.className = "api-message";
            messageBox.textContent = "";
        }

        approveBtn.disabled = true;
        rejectBtn.disabled = true;

        try {
            const response = await fetch(url, {
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
                if (messageBox) {
                    messageBox.style.display = "block";
                    messageBox.className = "api-message api-message-success";
                    messageBox.textContent = action === "approve"
                        ? "Record approved successfully."
                        : "Record rejected successfully.";
                }

                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 700);
                return;
            }

            if (messageBox) {
                messageBox.style.display = "block";
                messageBox.className = "api-message api-message-error";
                messageBox.textContent = JSON.stringify(data);
            }
        } catch (error) {
            if (messageBox) {
                messageBox.style.display = "block";
                messageBox.className = "api-message api-message-error";
                messageBox.textContent = "Network error. Please try again.";
            }
        } finally {
            approveBtn.disabled = false;
            rejectBtn.disabled = false;
        }
    }

    approveBtn.addEventListener("click", () => submitReview("approve"));
    rejectBtn.addEventListener("click", () => submitReview("reject"));
});