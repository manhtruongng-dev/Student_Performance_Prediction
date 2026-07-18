const API_BASE_URL = "http://127.0.0.1:8000";

const form = document.getElementById("predict-form");
const submitBtn = document.getElementById("submit-btn");
const resultBox = document.getElementById("result-box");
const resultStatus = document.getElementById("result-status");
const resultScore = document.getElementById("result-score");
const resultAdvice = document.getElementById("result-advice");
const errorBox = document.getElementById("error-box");
const historyBody = document.getElementById("history-body");

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function hideError() {
  errorBox.classList.add("hidden");
}

function showResult(data) {
  const isPass = data.prediction === "PASS";
  resultBox.classList.remove("hidden", "pass", "fail");
  resultBox.classList.add(isPass ? "pass" : "fail");

  resultStatus.textContent = `Kết quả: ${data.prediction}`;
  resultScore.textContent = `Điểm số dự kiến (G3): ${data.score} / 20`;
  resultAdvice.textContent = `Lời khuyên: ${data.advice}`;
}

function renderHistory(history) {
  if (!history || history.length === 0) {
    historyBody.innerHTML = '<tr><td colspan="9" class="empty-row">Chưa có dữ liệu</td></tr>';
    return;
  }

  historyBody.innerHTML = history
    .map((item) => {
      const tagClass = item.result === "PASS" ? "pass" : "fail";
      return `
        <tr>
          <td>${item.G1}</td>
          <td>${item.G2}</td>
          <td>${item.failures}</td>
          <td>${item.age}</td>
          <td>${item.studytime}</td>
          <td>${item.goout}</td>
          <td><span class="tag ${tagClass}">${item.result}</span></td>
          <td><b>${item.score}</b></td>
          <td>${item.date}</td>
        </tr>
      `;
    })
    .join("");
}

async function fetchHistory() {
  try {
    const res = await fetch(`${API_BASE_URL}/history`);
    if (!res.ok) throw new Error("Không lấy được lịch sử");
    const data = await res.json();
    renderHistory(data);
  } catch (err) {
    console.error("Lỗi khi tải lịch sử:", err);
  }
}

async function handleSubmit(event) {
  event.preventDefault();
  hideError();

  const formData = new FormData(form);
  const payload = {
    G1: parseFloat(formData.get("G1")),
    G2: parseFloat(formData.get("G2")),
    failures: parseInt(formData.get("failures"), 10),
    age: parseInt(formData.get("age"), 10),
    traveltime: parseInt(formData.get("traveltime"), 10),
    goout: parseInt(formData.get("goout"), 10),
    studytime: parseInt(formData.get("studytime"), 10),
    Medu: parseInt(formData.get("Medu"), 10),
    Fedu: parseInt(formData.get("Fedu"), 10),
    absences: parseInt(formData.get("absences"), 10),
  };

  submitBtn.disabled = true;
  submitBtn.textContent = "Đang phân tích...";

  try {
    const res = await fetch(`${API_BASE_URL}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Lỗi kết nối Backend!");
    }

    const data = await res.json();
    showResult(data);
    fetchHistory();
  } catch (err) {
    showError(err.message || "Đã có lỗi xảy ra, vui lòng thử lại.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Bắt đầu phân tích AI";
  }
}

form.addEventListener("submit", handleSubmit);
window.addEventListener("DOMContentLoaded", fetchHistory);
