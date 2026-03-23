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

function formatErrors(data) {
    if (!data || typeof data !== "object") {
        return "Something went wrong.";
    }

    const parts = [];

    for (const [field, errors] of Object.entries(data)) {
        if (Array.isArray(errors)) {
            parts.push(`${field}: ${errors.join(", ")}`);
        } else if (typeof errors === "object" && errors !== null) {
            parts.push(`${field}: ${JSON.stringify(errors)}`);
        } else {
            parts.push(`${field}: ${String(errors)}`);
        }
    }

    return parts.join(" | ") || "Something went wrong.";
}

document.addEventListener("DOMContentLoaded", function () {
    const forms = document.querySelectorAll('form[data-api-form="true"]');
    if (!forms.length) return;

    forms.forEach((form) => {
        const messageBox = form.parentElement.querySelector("[data-api-message]");
        const submitBtn = form.querySelector('button[type="submit"]');

        form.addEventListener("submit", async function (event) {
            event.preventDefault();

            const apiUrl = form.dataset.apiUrl;
            const apiMethod = (form.dataset.apiMethod || "POST").toUpperCase();
            const redirectUrl = form.dataset.redirectUrl || "";
            const successMessage = form.dataset.successMessage || "Saved successfully.";

            if (messageBox) {
                messageBox.style.display = "none";
                messageBox.className = "api-message";
                messageBox.textContent = "";
            }

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.dataset.originalText = submitBtn.dataset.originalText || submitBtn.textContent;
                submitBtn.textContent = apiMethod === "PATCH" ? "Updating..." : "Submitting...";
            }

            const formData = new FormData(form);
            const csrfToken = getCookie("csrftoken");

            try {
                const response = await fetch(apiUrl, {
                    method: apiMethod,
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
                        messageBox.textContent = successMessage;
                    }

                    if (redirectUrl) {
                        setTimeout(() => {
                            window.location.href = redirectUrl;
                        }, 700);
                    }
                    return;
                }

                if (messageBox) {
                    messageBox.style.display = "block";
                    messageBox.className = "api-message api-message-error";
                    messageBox.textContent = formatErrors(data);
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
                    submitBtn.textContent = submitBtn.dataset.originalText || "Submit";
                }
            }
        });
    });
});