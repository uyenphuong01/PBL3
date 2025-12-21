const API_BASE_URL = 'http://localhost:5000';
const API_VIOLATIONS = `${API_BASE_URL}/api/violations`;

document.addEventListener('DOMContentLoaded', function () {
    fetchViolations();
    // Auto refresh mỗi 5 giây
    setInterval(fetchViolations, 5000);
});

async function fetchViolations() {
    try {
        const response = await fetch(API_VIOLATIONS);
        const data = await response.json();

        renderTable(data);
        updateStats(data);
    } catch (error) {
        console.error('❌ Lỗi kết nối API:', error);
        document.getElementById("apiStatus").innerText = "Offline";
        document.getElementById("apiStatus").className = "badge bg-danger";
    }
}

function renderTable(violations) {
    const tableBody = document.getElementById('violationsTable');
    tableBody.innerHTML = '';

    violations
        .slice()
        .reverse() // mới nhất lên đầu
        .forEach(v => {
            const plate = v.plate && v.plate !== "N/A" ? v.plate : "UNKNOWN";

            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${v.time}</td>
                <td>
                    <span class="plate-display">${plate}</span>
                </td>
                <td>
                    <span class="badge bg-danger">${v.type}</span>
                </td>
                <td>Intersection</td>
                <td>
                    <img 
                        src="${API_BASE_URL}/evidence/images/${v.image}" 
                        class="image-preview rounded"
                        onclick="showImage('${API_BASE_URL}/evidence/images/${v.image}', '${plate}')"
                    >
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" 
                        onclick="showImage('${API_BASE_URL}/evidence/images/${v.image}', '${plate}')">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });

    document.getElementById("violationCount").innerText = violations.length;
    document.getElementById("totalCount").innerText = violations.length;
    document.getElementById("showingCount").innerText = violations.length;
}

function updateStats(data) {
    document.getElementById("totalViolations").innerText = data.length;

    const today = new Date().toISOString().slice(0, 10);
    const todayCount = data.filter(v => v.time.includes(today)).length;
    document.getElementById("todayViolations").innerText = todayCount;

    const uniquePlates = new Set(
        data
            .map(v => v.plate)
            .filter(p => p && p !== "N/A")
    );
    document.getElementById("uniquePlates").innerText = uniquePlates.size;
}

function showImage(src, plate) {
    document.getElementById("modalImage").src = src;
    document.getElementById("imageDetails").innerHTML =
        `<b>License Plate:</b> ${plate}`;
    new bootstrap.Modal(document.getElementById("imageModal")).show();
}
