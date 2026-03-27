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

function buildUrl(pattern, id) {
    return pattern.replace("/0/", `/${id}/`);
}

document.addEventListener("DOMContentLoaded", function () {
    const page = document.querySelector("[data-project-management-page]");
    if (!page) return;

    const summaryApiUrl = page.dataset.summaryApiUrl;
    const projectApiUrl = page.dataset.projectApiUrl;
    const projectDetailPattern = page.dataset.projectDetailPattern;
    const projectAssignPattern = page.dataset.projectAssignPattern;
    const searchForm = page.querySelector("[data-project-search-form]");
    const searchInput = page.querySelector("[data-project-search-input]");
    const clearLink = page.querySelector("[data-project-clear-link]");
    const counts = page.querySelector("[data-project-counts]");
    const messageBox = page.querySelector("[data-project-message]");
    const tableBody = page.querySelector("[data-project-table-body]");
    const roleNote = page.querySelector("[data-project-role-note]");
    const formCard = page.querySelector("[data-project-form-card]");
    const projectForm = page.querySelector("[data-project-form]");
    const formTitle = page.querySelector("[data-project-form-title]");
    const formDescription = page.querySelector("[data-project-form-description]");
    const submitButton = page.querySelector("[data-project-submit-button]");
    const cancelButton = page.querySelector("[data-project-cancel-button]");
    const projectIdInput = projectForm?.querySelector('[name="project_id"]');
    const managerSelect = projectForm?.querySelector('[name="team_manager"]');
    const csrfToken = getCookie("csrftoken");

    let currentQuery = "";
    let canManageProjects = false;
    let currentManagerChoices = [];
    let currentProjects = new Map();

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

    function updateBrowserQuery(query) {
        const nextUrl = query
            ? `${window.location.pathname}?q=${encodeURIComponent(query)}`
            : window.location.pathname;
        window.history.replaceState({}, "", nextUrl);
    }

    function renderManagerOptions(selectedValue = "") {
        const options = ['<option value="">Select manager</option>'];

        for (const manager of currentManagerChoices) {
            const label = `${manager.full_name || manager.username} (${manager.employee_id})${manager.team_display ? ` - ${manager.team_display}` : ""}`;
            const isSelected = String(manager.id) === String(selectedValue);
            options.push(`
                <option value="${escapeHtml(manager.id)}" ${isSelected ? "selected" : ""}>
                    ${escapeHtml(label)}
                </option>
            `);
        }

        return options.join("");
    }

    function resetProjectForm() {
        if (!projectForm) return;

        projectForm.reset();
        if (projectIdInput) {
            projectIdInput.value = "";
        }
        if (managerSelect) {
            managerSelect.innerHTML = renderManagerOptions("");
        }

        const activeCheckbox = projectForm.querySelector('[name="is_active"]');
        if (activeCheckbox) {
            activeCheckbox.checked = true;
        }

        if (formTitle) {
            formTitle.textContent = "Create Project";
        }
        if (formDescription) {
            formDescription.textContent = "Create a project and assign it to a team manager.";
        }
        if (submitButton) {
            submitButton.textContent = "Save Project";
        }
        if (cancelButton) {
            cancelButton.style.display = "none";
        }
    }

    function fillProjectForm(project) {
        if (!projectForm || !project) return;

        if (projectIdInput) {
            projectIdInput.value = project.id;
        }
        projectForm.querySelector('[name="code"]').value = project.code || "";
        projectForm.querySelector('[name="name"]').value = project.name || "";
        projectForm.querySelector('[name="description"]').value = project.description || "";
        projectForm.querySelector('[name="is_active"]').checked = Boolean(project.is_active);
        if (managerSelect) {
            managerSelect.innerHTML = renderManagerOptions(project.team_manager || "");
        }

        if (formTitle) {
            formTitle.textContent = `Edit ${project.code}`;
        }
        if (formDescription) {
            formDescription.textContent = "Update the manager, details, or active status for this project.";
        }
        if (submitButton) {
            submitButton.textContent = "Update Project";
        }
        if (cancelButton) {
            cancelButton.style.display = "inline-block";
        }

        formCard?.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function renderAssignedEmployees(project) {
        const employees = Array.isArray(project.assigned_employees) ? project.assigned_employees : [];
        if (!employees.length) {
            return '<span class="muted-text">No employees assigned.</span>';
        }

        return `
            <div class="project-pill-row">
                ${employees.map((employee) => `
                    <span class="project-pill">
                        ${escapeHtml(employee.full_name || employee.username)} (${escapeHtml(employee.employee_id)})
                    </span>
                `).join("")}
            </div>
        `;
    }

    function renderAssignableOptions(project) {
        const selectedEmployeeIds = new Set(Array.isArray(project.assigned_employee_ids) ? project.assigned_employee_ids.map(String) : []);
        const employees = Array.isArray(project.assignable_employees) ? project.assignable_employees : [];

        return employees.map((employee) => {
            const isSelected = selectedEmployeeIds.has(String(employee.id));
            const label = `${employee.full_name || employee.username} (${employee.employee_id})`;
            return `
                <option value="${escapeHtml(employee.id)}" ${isSelected ? "selected" : ""}>
                    ${escapeHtml(label)}
                </option>
            `;
        }).join("");
    }

    function renderAssignmentControl(project) {
        if (!project.can_assign_members) {
            return '<p class="read-only-note">View only. Employee assignment is not available for this project.</p>';
        }

        if (!project.team_manager) {
            return '<p class="read-only-note">Assign a team manager first to unlock employee assignment.</p>';
        }

        const employees = Array.isArray(project.assignable_employees) ? project.assignable_employees : [];
        if (!employees.length) {
            return '<p class="read-only-note">No active employees are available in this team yet.</p>';
        }

        return `
            <form class="project-assignment-form" data-project-assignment-form data-project-id="${project.id}">
                <label class="salary-update-field">
                    <span>Team Members</span>
                    <select name="employee_ids" class="project-multiselect" multiple size="${Math.min(Math.max(employees.length, 2), 5)}">
                        ${renderAssignableOptions(project)}
                    </select>
                </label>
                <button type="submit" class="btn-primary btn-small">Save Assignees</button>
            </form>
        `;
    }

    function renderProjects(data) {
        currentQuery = data.search_query || "";
        canManageProjects = Boolean(data.can_manage_projects);
        currentManagerChoices = Array.isArray(data.manager_choices) ? data.manager_choices : [];

        if (searchInput) {
            searchInput.value = currentQuery;
        }
        if (clearLink) {
            clearLink.style.display = currentQuery ? "" : "none";
        }
        if (counts) {
            counts.textContent = `Showing ${data.filtered_count} of ${data.total_projects} project${data.total_projects === 1 ? "" : "s"}.`;
        }
        if (roleNote) {
            roleNote.textContent = canManageProjects
                ? "Superadmin and HR can create or edit projects. Assigned team managers can map employees from their own team."
                : "You can manage team-member assignment for projects mapped to you as team manager.";
        }
        if (formCard) {
            formCard.style.display = canManageProjects ? "block" : "none";
        }

        const projects = Array.isArray(data.projects) ? data.projects : [];
        currentProjects = new Map(projects.map((project) => [String(project.id), project]));

        tableBody.innerHTML = projects.length
            ? projects.map((project) => {
                const managerMeta = project.team_manager_name
                    ? `
                        <strong>${escapeHtml(project.team_manager_name)}</strong>
                        <p class="project-manager-meta">
                            ${escapeHtml(project.team_manager_employee_id || "")}${project.team_manager_team_display ? `<br>${escapeHtml(project.team_manager_team_display)}` : ""}
                        </p>
                    `
                    : '<span class="muted-text">No team manager assigned.</span>';
                const editActions = canManageProjects
                    ? `<div class="table-actions"><button type="button" class="btn-table-edit" data-project-edit="${project.id}">Edit</button></div>`
                    : "";
                const statusClass = project.is_active ? "status-active" : "status-inactive";
                const statusLabel = project.is_active ? "Active" : "Inactive";

                return `
                    <tr>
                        <td class="project-cell">
                            <strong>${escapeHtml(project.code)} - ${escapeHtml(project.name)}</strong>
                            <p>${escapeHtml(project.description || "No description added.")}</p>
                        </td>
                        <td class="project-cell">${managerMeta}</td>
                        <td>${renderAssignedEmployees(project)}</td>
                        <td><span class="status-badge ${statusClass}">${statusLabel}</span></td>
                        <td>
                            <div class="project-actions-col">
                                ${editActions}
                                ${renderAssignmentControl(project)}
                            </div>
                        </td>
                    </tr>
                `;
            }).join("")
            : '<tr><td colspan="5" class="empty-cell">No projects matched your search.</td></tr>';

        if (canManageProjects) {
            const activeProject = projectIdInput?.value ? currentProjects.get(projectIdInput.value) : null;
            if (activeProject) {
                fillProjectForm(activeProject);
            } else {
                resetProjectForm();
            }
        }
    }

    async function loadProjects(searchQuery = "", updateUrl = false) {
        const url = new URL(summaryApiUrl, window.location.origin);
        if (searchQuery) {
            url.searchParams.set("q", searchQuery);
        }

        try {
            const response = await fetch(url, {
                credentials: "same-origin",
                headers: { "Accept": "application/json" },
            });
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(data.detail || formatErrors(data));
            }

            setMessage("", "");
            renderProjects(data);

            if (updateUrl) {
                updateBrowserQuery(data.search_query || "");
            }
        } catch (error) {
            setMessage(error.message || "Failed to load projects.", "error");
            tableBody.innerHTML = '<tr><td colspan="5" class="empty-cell">Failed to load projects.</td></tr>';
            if (counts) {
                counts.textContent = "Unable to load project count.";
            }
        }
    }

    searchForm?.addEventListener("submit", function (event) {
        event.preventDefault();
        loadProjects((searchInput?.value || "").trim(), true);
    });

    clearLink?.addEventListener("click", function (event) {
        event.preventDefault();
        if (searchInput) {
            searchInput.value = "";
        }
        loadProjects("", true);
    });

    cancelButton?.addEventListener("click", function () {
        resetProjectForm();
    });

    page.addEventListener("click", function (event) {
        const editButton = event.target.closest("[data-project-edit]");
        if (!editButton) return;

        const project = currentProjects.get(String(editButton.dataset.projectEdit));
        if (project) {
            fillProjectForm(project);
        }
    });

    projectForm?.addEventListener("submit", async function (event) {
        event.preventDefault();
        if (!canManageProjects) return;

        const originalText = submitButton?.textContent || "Save Project";
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = projectIdInput?.value ? "Updating..." : "Saving...";
        }

        const payload = {
            code: projectForm.querySelector('[name="code"]').value.trim(),
            name: projectForm.querySelector('[name="name"]').value.trim(),
            description: projectForm.querySelector('[name="description"]').value.trim(),
            team_manager: managerSelect?.value ? Number(managerSelect.value) : null,
            is_active: Boolean(projectForm.querySelector('[name="is_active"]').checked),
        };

        const projectId = projectIdInput?.value || "";
        const requestUrl = projectId ? buildUrl(projectDetailPattern, projectId) : projectApiUrl;
        const requestMethod = projectId ? "PATCH" : "POST";

        try {
            const response = await fetch(requestUrl, {
                method: requestMethod,
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify(payload),
            });
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(data.detail || formatErrors(data));
            }

            setMessage(projectId ? "Project updated successfully." : "Project created successfully.", "success");
            resetProjectForm();
            await loadProjects(currentQuery, false);
        } catch (error) {
            setMessage(error.message || "Failed to save project.", "error");
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        }
    });

    page.addEventListener("submit", async function (event) {
        const assignmentForm = event.target.closest("[data-project-assignment-form]");
        if (!assignmentForm) return;

        event.preventDefault();
        const assignmentButton = assignmentForm.querySelector('button[type="submit"]');
        const employeeSelect = assignmentForm.querySelector('[name="employee_ids"]');
        const employeeIds = Array.from(employeeSelect?.selectedOptions || []).map((option) => Number(option.value));
        const projectId = assignmentForm.dataset.projectId;
        const originalText = assignmentButton?.textContent || "Save Assignees";

        if (assignmentButton) {
            assignmentButton.disabled = true;
            assignmentButton.textContent = "Saving...";
        }

        try {
            const response = await fetch(buildUrl(projectAssignPattern, projectId), {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify({ employee_ids: employeeIds }),
            });
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(data.detail || formatErrors(data));
            }

            setMessage(data.message || "Project assignments updated successfully.", "success");
            await loadProjects(currentQuery, false);
        } catch (error) {
            setMessage(error.message || "Failed to update project assignments.", "error");
        } finally {
            if (assignmentButton) {
                assignmentButton.disabled = false;
                assignmentButton.textContent = originalText;
            }
        }
    });

    currentQuery = new URLSearchParams(window.location.search).get("q") || "";
    loadProjects(currentQuery, false);
});
