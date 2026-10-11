/* VORTEXA Company Dashboard — front-end preview only.
   Replace demo arrays with API calls after the team's backend contract is confirmed. */
"use strict";

const initialJobs = [
  { id: 1, title: "Senior Frontend Developer", department: "Engineering", location: "Pune / Hybrid", applicants: 42, status: "Open" },
  { id: 2, title: "Product Designer", department: "Design", location: "Remote", applicants: 28, status: "Open" },
  { id: 3, title: "Backend Engineer", department: "Engineering", location: "Pune / Hybrid", applicants: 36, status: "Open" },
  { id: 4, title: "Growth Marketing Manager", department: "Marketing", location: "Mumbai", applicants: 19, status: "Paused" }
];

const applicants = [
  { id: 1, name: "Aarav Sharma", email: "aarav.sharma@example.com", initials: "AS", job: "Senior Frontend Developer", applied: "Today", status: "New" },
  { id: 2, name: "Mira Patel", email: "mira.patel@example.com", initials: "MP", job: "Product Designer", applied: "Today", status: "Shortlisted" },
  { id: 3, name: "Ishaan Mehta", email: "ishaan.mehta@example.com", initials: "IM", job: "Backend Engineer", applied: "Yesterday", status: "Interview" },
  { id: 4, name: "Ananya Rao", email: "ananya.rao@example.com", initials: "AR", job: "Senior Frontend Developer", applied: "Yesterday", status: "New" },
  { id: 5, name: "Kabir Singh", email: "kabir.singh@example.com", initials: "KS", job: "Growth Marketing Manager", applied: "12 Oct 2026", status: "Rejected" }
];

let jobs = [...initialJobs];
let toastTimer;

const $ = (selector) => document.querySelector(selector);
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[char]);

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove("show"), 3000);
}

function renderJobs() {
  const body = $("#jobsTableBody");
  body.innerHTML = jobs.map((job) => `
    <tr>
      <td><div class="job-cell"><span class="company-logo">${escapeHTML(job.department.slice(0, 1))}</span>
        <span><span class="job-name">${escapeHTML(job.title)}</span><span class="job-meta">${escapeHTML(job.department)} · ${escapeHTML(job.location || "Location not set")}</span></span></div></td>
      <td>${job.applicants}</td>
      <td><span class="status ${job.status === "Open" ? "status-open" : "status-paused"}">${escapeHTML(job.status)}</span></td>
      <td><button class="row-menu" data-job-action="${job.id}" aria-label="Change ${escapeHTML(job.title)} status" title="Toggle job status">⋯</button></td>
    </tr>`).join("");
  $("#activeJobsCount").textContent = jobs.filter((job) => job.status === "Open").length + 4;
  $("#jobsEmpty").classList.toggle("hidden", jobs.length > 0);
}

function renderApplicants() {
  const query = $("#applicantSearch").value.trim().toLowerCase();
  const status = $("#statusFilter").value;
  const filtered = applicants.filter((person) => {
    const matchesText = `${person.name} ${person.email} ${person.job}`.toLowerCase().includes(query);
    return matchesText && (status === "all" || person.status === status);
  });
  $("#applicantsTableBody").innerHTML = filtered.map((person) => `
    <tr>
      <td><div class="candidate-cell"><span class="candidate-avatar">${escapeHTML(person.initials)}</span><span><span class="candidate-name">${escapeHTML(person.name)}</span><span class="candidate-email">${escapeHTML(person.email)}</span></span></div></td>
      <td>${escapeHTML(person.job)}</td><td>${escapeHTML(person.applied)}</td>
      <td><span class="status status-${person.status.toLowerCase()}">${escapeHTML(person.status)}</span></td>
      <td><select class="action-select" data-applicant-id="${person.id}" aria-label="Update status for ${escapeHTML(person.name)}">
        ${["New", "Shortlisted", "Interview", "Rejected"].map((option) => `<option${option === person.status ? " selected" : ""}>${option}</option>`).join("")}
      </select></td>
    </tr>`).join("");
  $("#applicantsEmpty").classList.toggle("hidden", filtered.length > 0);
}

function renderPipeline() {
  const stages = [
    { label: "New", count: 118, color: "bar-blue" },
    { label: "Screening", count: 64, color: "bar-purple" },
    { label: "Interview", count: 42, color: "bar-orange" },
    { label: "Shortlisted", count: 22, color: "bar-green" }
  ];
  $("#pipelineBars").innerHTML = stages.map((stage) => `
    <div class="pipeline-row"><span>${stage.label}</span><div class="bar-track"><div class="bar-fill ${stage.color}" style="width:${Math.round(stage.count / 118 * 100)}%"></div></div><strong>${stage.count}</strong></div>`).join("");
}

function switchView(view) {
  const labels = { overview: "Overview", jobs: "Job postings", applicants: "Applicants", interviews: "Interviews" };
  $("#breadcrumbCurrent").textContent = labels[view] || "Overview";
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === view));
  if (view === "jobs") $("#jobsPanel").scrollIntoView({ behavior: "smooth", block: "start" });
  else if (view === "applicants") $("#applicantsPanel").scrollIntoView({ behavior: "smooth", block: "start" });
  else if (view === "interviews") showToast("Interview management will be connected when the backend API is available.");
  else window.scrollTo({ top: 0, behavior: "smooth" });
  $("#sidebar").classList.remove("open");
}

function openJobModal() {
  $("#jobForm").reset();
  if (typeof $("#jobModal").showModal === "function") $("#jobModal").showModal();
  else showToast("Your browser does not support this form dialog. Please use a recent browser.");
}

document.addEventListener("DOMContentLoaded", () => {
  $("#year").textContent = new Date().getFullYear();
  $("#todayLabel").textContent = new Intl.DateTimeFormat("en", { weekday: "long", month: "short", day: "numeric" }).format(new Date()).toUpperCase();
  renderJobs();
  renderApplicants();
  renderPipeline();

  document.querySelectorAll(".nav-item").forEach((item) => item.addEventListener("click", () => switchView(item.dataset.view)));
  document.querySelectorAll("[data-go]").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.go)));
  $("#createJobButton").addEventListener("click", openJobModal);
  $("#closeJobModal").addEventListener("click", () => $("#jobModal").close());
  $("#cancelJobButton").addEventListener("click", () => $("#jobModal").close());
  $("#dismissNotice").addEventListener("click", () => document.querySelector(".notice").remove());
  $("#mobileMenu").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
  $("#notificationButton").addEventListener("click", () => showToast("You're all caught up in this preview."));
  $("#helpButton").addEventListener("click", () => showToast("Help centre will be available in a future release."));
  $("#applicantSearch").addEventListener("input", renderApplicants);
  $("#statusFilter").addEventListener("change", renderApplicants);

  $("#jobsTableBody").addEventListener("click", (event) => {
    const button = event.target.closest("[data-job-action]");
    if (!button) return;
    const job = jobs.find((item) => item.id === Number(button.dataset.jobAction));
    if (!job) return;
    job.status = job.status === "Open" ? "Paused" : "Open";
    renderJobs();
    showToast(`${job.title} is now ${job.status.toLowerCase()} (preview only).`);
  });

  $("#applicantsTableBody").addEventListener("change", (event) => {
    const select = event.target.closest("[data-applicant-id]");
    if (!select) return;
    const person = applicants.find((item) => item.id === Number(select.dataset.applicantId));
    if (!person) return;
    person.status = select.value;
    renderApplicants();
    showToast(`${person.name}'s status changed to ${person.status} in this preview.`);
  });

  $("#jobForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const title = String(form.get("title") || "").trim();
    if (!title) return;
    jobs.unshift({
      id: Math.max(0, ...jobs.map((job) => job.id)) + 1,
      title,
      department: String(form.get("department")),
      location: String(form.get("location") || "").trim() || "Location not set",
      applicants: 0,
      status: "Open"
    });
    renderJobs();
    $("#jobModal").close();
    showToast("Preview job added. It has not been saved to the server.");
  });
});
