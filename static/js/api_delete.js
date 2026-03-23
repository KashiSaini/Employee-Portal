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
    const forms = document.querySelectorAll('form[data-api-delete="true"]');
    if (!forms.length) return;

    forms.forEach((form) => {
        const messageBox = document.querySelector("[data-api-delete-message]");
        const submitBtn = form.querySelector('button[type="submit"]');

        form.addEventListener("submit", async function (event) {
            event.preventDefault();

            const apiUrl = form.dataset.apiUrl;
            const redirectUrl = form.dataset.redirectUrl || "";
            const successMessage = form.dataset.successMessage || "Deleted successfully.";
            const csrfToken = getCookie("csrftoken");

            if (messageBox) {
                messageBox.style.display = "none";
                messageBox.className = "api-message";
                messageBox.textContent = "";
            }

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.dataset.originalText = submitBtn.dataset.originalText || submitBtn.textContent;
                submitBtn.textContent = "Deleting...";
            }

            try {
                const response = await fetch(apiUrl, {
                    method: "DELETE",
                    credentials: "same-origin",
                    headers: {
                        "X-CSRFToken": csrfToken,
                        "Accept": "application/json"
                    }
                });

                if (response.ok) {
                    if (messageBox) {
                        messageBox.style.display = "block";
                        messageBox.className = "api-message api-message-success";
                        messageBox.textContent = successMessage;
                    }

                    if (redirectUrl) {
                        setTimeout(() => {
                            window.location.href = redirectUrl;
                        }, 700);
                    }
                    return;
                }

                let errorText = "Unable to delete record.";
                try {
                    const data = await response.json();
                    if (data && typeof data === "object") {
                        errorText = Object.entries(data)
                            .map(([field, errors]) => {
                                const text = Array.isArray(errors) ? errors.join(", ") : String(errors);
                                return `${field}: ${text}`;
                            })
                            .join(" | ");
                    }
                } catch (e) {
                    // ignore json parse errors
                }

                if (messageBox) {
                    messageBox.style.display = "block";
                    messageBox.className = "api-message api-message-error";
                    messageBox.textContent = errorText;
                }
            } catch (error) {
                if (messageBox) {
                    messageBox.style.display = "block";
                    messageBox.className = "api-message api-message-error";
                    messageBox.textContent = "Network error. Please try again.";
                }
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = submitBtn.dataset.originalText || "Delete";
                }
            }
        });
    });
});