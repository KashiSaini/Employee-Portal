async function fetchApiList(url) {
    const response = await fetch(url, {
        credentials: "same-origin",
        headers: { "Accept": "application/json" }
    });

    const data = await response.json();
    return Array.isArray(data) ? data : (data.results || []);
}

document.addEventListener("DOMContentLoaded", async function () {
    const salaryPage = document.querySelector("[data-salary-slip-page]");
    const policyPage = document.querySelector("[data-policy-page]");
    const documentsPage = document.querySelector("[data-company-documents-page]");

    if (salaryPage) {
        const items = await fetchApiList(salaryPage.dataset.apiUrl);
        document.querySelector("#salary-slip-body").innerHTML = items.map(item => `
            <tr>
                <td>${item.month}</td>
                <td>${item.year}</td>
                <td>${item.uploaded_at || ""}</td>
                <td><a href="${item.file}" target="_blank" class="receipt-link">Download Slip</a></td>
            </tr>
        `).join("") || `<tr><td colspan="4" class="empty-cell">No salary slips available yet.</td></tr>`;
    }

    if (policyPage) {
        const items = await fetchApiList(policyPage.dataset.apiUrl);
        document.querySelector("#policy-grid").innerHTML = items.map(item => `
            <div class="document-card">
                <div class="document-meta-row">
                    <span class="doc-badge">${item.category}</span>
                    <span class="doc-date">${item.effective_date || ""}</span>
                </div>
                <h4>${item.title}</h4>
                <p>${item.description || "No description added."}</p>
                <a href="${item.file}" target="_blank" class="btn-secondary">Open Policy</a>
            </div>
        `).join("") || `<div class="section-card"><p class="muted-text">No active policy documents available.</p></div>`;
    }

    if (documentsPage) {
        const items = await fetchApiList(documentsPage.dataset.apiUrl);
        document.querySelector("#company-document-grid").innerHTML = items.map(item => `
            <div class="document-card">
                <div class="document-meta-row">
                    <span class="doc-badge">${item.doc_type}</span>
                    <span class="doc-date">${item.uploaded_at || ""}</span>
                </div>
                <h4>${item.title}</h4>
                <p>${item.description || "No description added."}</p>
                <a href="${item.file}" target="_blank" class="btn-secondary">Open Document</a>
            </div>
        `).join("") || `<div class="section-card"><p class="muted-text">No company documents available.</p></div>`;
    }
});