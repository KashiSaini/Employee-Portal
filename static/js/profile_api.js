function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function fetchProfile(url) {
    const response = await fetch(url, {
        credentials: "same-origin",
        headers: { "Accept": "application/json" }
    });

    if (!response.ok) {
        throw new Error("Unable to load profile.");
    }
    return await response.json();
}

function setField(selector, value) {
    const el = document.querySelector(selector);
    if (el) el.textContent = value || "-";
}

function fillForm(data) {
    Object.entries(data).forEach(([key, value]) => {
        const field = document.querySelector(`[name="${key}"]`);
        if (!field) return;

        if (field.tagName === "SELECT") {
            field.value = value ?? "";
        } else if (field.type === "date") {
            field.value = value ?? "";
        } else {
            field.value = value ?? "";
        }
    });
}

document.addEventListener("DOMContentLoaded", async function () {
    const detailBox = document.querySelector("[data-profile-detail]");
    const form = document.querySelector("[data-profile-update-form]");

    const apiUrl = document.body.dataset.profileApiUrl;
    if (!apiUrl) return;

    try {
        const data = await fetchProfile(apiUrl);

        if (detailBox) {
            setField('[data-profile-field="full_name"]', data.full_name);
            setField('[data-profile-field="employee_id"]', data.employee_id);
            setField('[data-profile-field="email"]', data.email);
            setField('[data-profile-field="phone"]', data.phone);
            setField('[data-profile-field="department"]', data.department);
            setField('[data-profile-field="designation"]', data.designation);
            setField('[data-profile-field="date_of_birth"]', data.date_of_birth);
            setField('[data-profile-field="join_date"]', data.join_date);
            setField('[data-profile-field="gender"]', data.gender);
            setField('[data-profile-field="blood_group"]', data.blood_group);
            setField('[data-profile-field="emergency_contact_name"]', data.emergency_contact_name);
            setField('[data-profile-field="emergency_contact_phone"]', data.emergency_contact_phone);
            setField('[data-profile-field="permanent_address"]', data.permanent_address);
            setField('[data-profile-field="current_address"]', data.current_address);
            setField('[data-profile-field="city"]', data.city);
            setField('[data-profile-field="state"]', data.state);
            setField('[data-profile-field="country"]', data.country);
            setField('[data-profile-field="postal_code"]', data.postal_code);
            setField('[data-profile-field="father_name"]', data.father_name);
            setField('[data-profile-field="mother_name"]', data.mother_name);
            setField('[data-profile-field="spouse_name"]', data.spouse_name);
            setField('[data-profile-field="highest_qualification"]', data.highest_qualification);
            setField('[data-profile-field="institute_name"]', data.institute_name);
            setField('[data-profile-field="passing_year"]', data.passing_year);
            setField('[data-profile-field="skills"]', data.skills);
            setField('[data-profile-field="bio"]', data.bio);
        }

        if (form) {
            fillForm(data);
        }
    } catch (error) {
        console.error(error);
    }
});