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

function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
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
    const page = document.querySelector("[data-user-management-page]");
    if (!page) return;

    const apiUrl = page.dataset.apiUrl;
    const roleApiUrl = page.dataset.roleApiUrl;
    const searchForm = page.querySelector("[data-user-search-form]");
    const searchInput = page.querySelector("[data-user-search-input]");
    const clearLink = page.querySelector("[data-user-clear-link]");
    const counts = page.querySelector("[data-user-counts]");
    const rolesNote = page.querySelector("[data-user-roles-note]");
    const rolesColumn = page.querySelector("[data-user-roles-column]");
    const tableBody = page.querySelector("[data-user-table-body]");
    const messageBox = page.querySelector("[data-users-message]");
    const csrfToken = getCookie("csrftoken");

    let currentQuery = (searchInput?.value || "").trim();
    let currentCanAssignRoles = false;
    let currentTeamChoices = [];

    function setMessage(text, type) {
        if (!messageBox) return;

        if (!text) {
            messageBox.style.display = "none";
            messageBox.className = "api-message";
            messageBox.textContent = "";
            return;
        }

        messageBox.style.display = "block";
        messageBox.className = `api-message api-message-${type}`;
        messageBox.textContent = text;
    }

    function renderRolePills(user) {
        const roleMap = {
            Superadmin: "role-pill-admin",
            HR: "role-pill-hr",
            Manager: "role-pill-manager",
            Employee: "role-pill-user",
        };

        return `
            <div class="role-pill-row">
                ${(user.roles || []).map((role) => `
                    <span class="role-pill ${roleMap[role] || "role-pill-user"}">${escapeHtml(role)}</span>
                `).join("")}
            </div>
        `;
    }

    function renderTeamOptions(user) {
        const options = ['<option value="">Select team</option>'];

        for (const choice of currentTeamChoices) {
            const isSelected = choice.value === (user.team || "");
            options.push(`
                <option value="${escapeHtml(choice.value)}" ${isSelected ? "selected" : ""}>
                    ${escapeHtml(choice.label)}
                </option>
            `);
        }

        return options.join("");
    }

    function renderRoleForm(user) {
        if (!currentCanAssignRoles) {
            return '<p class="read-only-note">View only. Role changes can be made by a superadmin.</p>';
        }

        return `
            <form class="role-form" data-user-role-form data-user-id="${user.id}">
                <label class="role-toggle">
                    <input type="checkbox" name="is_superuser" ${user.is_superuser ? "checked" : ""}>
                    Superadmin
                </label>
                <label class="role-toggle">
                    <input type="checkbox" name="is_hr" ${user.is_hr ? "checked" : ""}>
                    HR
                </label>
                <label class="role-toggle">
                    <input type="checkbox" name="is_manager" ${user.is_manager ? "checked" : ""}>
                    Manager
                </label>
                <label class="role-toggle">
                    <span>Team</span>
                    <select name="team">
                        ${renderTeamOptions(user)}
                    </select>
                </label>
                <button type="submit" class="btn-primary btn-small">Save Roles</button>
            </form>
        `;
    }

    function renderUsers(data) {
        currentCanAssignRoles = Boolean(data.can_assign_roles);
        currentQuery = data.search_query || "";
        currentTeamChoices = Array.isArray(data.team_choices) ? data.team_choices : [];

        if (searchInput) {
            searchInput.value = currentQuery;
        }

        if (clearLink) {
            clearLink.style.display = currentQuery ? "" : "none";
        }

        if (counts) {
            const suffix = data.total_users === 1 ? "" : "s";
            counts.textContent = `Showing ${data.filtered_count} of ${data.total_users} user${suffix}.`;
        }

        if (rolesNote) {
            rolesNote.textContent = currentCanAssignRoles
                ? "Update team assignments and portal roles for existing users."
                : "View only. Contact a superadmin if someone needs a role change.";
        }

        if (rolesColumn) {
            rolesColumn.textContent = currentCanAssignRoles
                ? "Portal Access Roles"
                : "Portal Access Roles (View Only)";
        }

        const users = Array.isArray(data.users) ? data.users : [];
        tableBody.innerHTML = users.length
            ? users.map((user) => `
                <tr>
                    <td class="user-cell">
                        <strong>${escapeHtml(user.full_name || user.username)}</strong>
                        <p>
                            ${escapeHtml(user.employee_id)}<br>
                            ${escapeHtml(user.email || "No email added")}<br>
                            ${escapeHtml(user.username)}<br>
                            Team: ${escapeHtml(user.team_display || "Not assigned")}
                        </p>
                    </td>
                    <td>${renderRolePills(user)}</td>
                    <td>${renderRoleForm(user)}</td>
                </tr>
            `).join("")
            : '<tr><td colspan="3" class="empty-cell">No users matched your search.</td></tr>';
    }

    function updateBrowserQuery(searchQuery) {
        const nextUrl = searchQuery
            ? `${window.location.pathname}?q=${encodeURIComponent(searchQuery)}`
            : window.location.pathname;
        window.history.replaceState({}, "", nextUrl);
    }

    async function loadUsers(searchQuery = "", updateUrl = false) {
        const url = new URL(apiUrl, window.location.origin);
        if (searchQuery) {
            url.searchParams.set("q", searchQuery);
        }

        try {
            const response = await fetch(url, {
                credentials: "same-origin",
                headers: { "Accept": "application/json" }
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(data.detail || formatErrors(data));
            }

            setMessage("", "");
            renderUsers(data);

            if (updateUrl) {
                updateBrowserQuery(data.search_query || "");
            }
        } catch (error) {
            setMessage(error.message || "Failed to load users.", "error");
            tableBody.innerHTML = '<tr><td colspan="3" class="empty-cell">Failed to load users.</td></tr>';
            if (counts) {
                counts.textContent = "Unable to load user count.";
            }
        }
    }

    if (searchForm) {
        searchForm.addEventListener("submit", function (event) {
            event.preventDefault();
            loadUsers((searchInput?.value || "").trim(), true);
        });
    }

    if (clearLink) {
        clearLink.addEventListener("click", function (event) {
            event.preventDefault();
            if (searchInput) {
                searchInput.value = "";
            }
            loadUsers("", true);
        });
    }

    page.addEventListener("submit", async function (event) {
        const form = event.target.closest("[data-user-role-form]");
        if (!form) return;

        event.preventDefault();
        const submitButton = form.querySelector('button[type="submit"]');

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.dataset.originalText = submitButton.dataset.originalText || submitButton.textContent;
            submitButton.textContent = "Saving...";
        }

        const payload = new FormData();
        payload.append("user_id", form.dataset.userId || form.querySelector('[name="user_id"]')?.value || "");
        payload.append("is_superuser", form.querySelector('[name="is_superuser"]').checked ? "true" : "false");
        payload.append("is_hr", form.querySelector('[name="is_hr"]').checked ? "true" : "false");
        payload.append("is_manager", form.querySelector('[name="is_manager"]').checked ? "true" : "false");
        payload.append("team", form.querySelector('[name="team"]')?.value || "");

        try {
            const response = await fetch(roleApiUrl, {
                method: "POST",
                body: payload,
                credentials: "same-origin",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "Accept": "application/json"
                }
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(data.detail || formatErrors(data));
            }

            setMessage(data.message || "Roles updated successfully.", "success");
            await loadUsers(currentQuery, false);
        } catch (error) {
            setMessage(error.message || "Failed to update roles.", "error");
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = submitButton.dataset.originalText || "Save Roles";
            }
        }
    });

    loadUsers(currentQuery, false);
});
