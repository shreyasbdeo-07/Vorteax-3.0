const API_BASE = ""; 

const state = {
    jobs: [],
    matches: [],
    applications: [],
    profile: {
        fullName: "",
        email: "",
        education: "",
        phone: "",
        degree: "",
        branch: "",
        college: "",
        graduationYear: "",
        experience: "",
        skills: "",
        bio: ""
    },
    passportVerified: false
};

const $ = (id) => document.getElementById(id);

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        },
        credentials: "include"
    });

    if (response.status === 204) return null;
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.message || `Request failed: ${response.status}`);
    return payload;
}

function showMessage(elementId, message, isError = false) {
    const element = $(elementId);

    if (!element) return;

    element.textContent = message;
    element.style.color = isError ? "#c52f47" : "#16875d";
}

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

function getJobId(job) {
    return job.id ?? job.job_id;
}

function getJobTitle(job) {
    return job.title ?? job.job_title ?? "Untitled Position";
}

function getCompanyName(job) {
    return job.company_name ?? job.company ?? "Company";
}

function getJobDescription(job) {
    return job.description ?? job.job_description ?? "No description available.";
}

function getJobSkills(job) {
    const skills = job.skills ?? job.required_skills ?? [];

    if (Array.isArray(skills)) {
        return skills;
    }

    return String(skills)
        .split(",")
        .map((skill) => skill.trim())
        .filter(Boolean);
}

function renderJobs(jobs, containerId, showMatchScore = false) {
    const container = $(containerId);

    if (!container) return;

    if (!jobs.length) {
        container.innerHTML = `
            <p class="empty-state">
                No jobs found. Try again later.
            </p>`;
        return;
    }

    container.innerHTML = jobs.map((job) => {
        const id = getJobId(job);
        const title = escapeHTML(getJobTitle(job));
        const company = escapeHTML(getCompanyName(job));
        const description = escapeHTML(getJobDescription(job));
        const location = escapeHTML(job.location ?? "Location not specified");
        const jobType = escapeHTML(job.job_type ?? job.employment_type ?? "Not specified");

        const skills = getJobSkills(job)
            .map((skill) => `<span>${escapeHTML(skill)}</span>`)
            .join("");

        const score = job.match_score ?? job.match_percentage;

        const matchHTML = showMatchScore && score !== undefined
            ? `<span class="match-score">${escapeHTML(score)}% match</span>`
            : "";

        const safeId = escapeHTML(id ?? "");

        return `
            <article class="job-card">
                <h3>${title}</h3>
                <p class="job-company">${company}</p>
                <p class="job-description">${description}</p>

                <div class="job-meta">
                    <span>${location}</span>
                    <span>${jobType}</span>
                    ${skills}
                </div>

                <div class="job-actions">
                    ${matchHTML}
                    <button
                        class="primary-btn apply-btn"
                        data-job-id="${safeId}"
                        ${id == null ? "disabled" : ""}>
                        Apply Now
                    </button>
                </div>
            </article>`;
    }).join("");
}

function renderApplications(applications) {
    const container = $("applicationsList");

    if (!container) return;

    if (!applications.length) {
        container.innerHTML = `
            <tr>
                <td colspan="4" class="empty-state">
                    You haven't applied for any jobs yet.
                </td>
            </tr>`;
        return;
    }

    container.innerHTML = applications.map((application) => {
        const title = escapeHTML(
            application.job_title ?? application.title ?? "Job"
        );

        const company = escapeHTML(
            application.company_name ?? application.company ?? "Company"
        );

        const dateValue = application.applied_at ?? application.created_at;
        const date = dateValue
            ? escapeHTML(String(dateValue).slice(0, 10))
            : "—";

        const status = String(application.status ?? "Pending")
            .toLowerCase();

        const safeStatus = escapeHTML(status);
        const displayStatus = escapeHTML(
            status.replace(/[-_]/g, " ")
                .replace(/\b\w/g, (letter) => letter.toUpperCase())
        );

        return `
            <tr>
                <td>${title}</td>
                <td>${company}</td>
                <td>${date}</td>
                <td>
                    <span class="status ${safeStatus}">
                        ${displayStatus}
                    </span>
                </td>
            </tr>`;
    }).join("");
}

function updateStats() {
    const skills = (Array.isArray(state.profile.skills) ? state.profile.skills : String(state.profile.skills || "").split(","))
        .map((skill) => String(skill).trim())
        .filter(Boolean);

    const filledFields = [
        state.profile.fullName,
        state.profile.email,
        state.profile.education,
        state.profile.experience,
        state.profile.skills,
        state.profile.bio
    ].filter((value) => String(value).trim() !== "").length;

    const completion = Math.round((filledFields / 6) * 100);

    $("profileCompletion").textContent = `${completion}%`;
    $("profileProgress").style.width = `${completion}%`;
    $("matchCount").textContent = state.matches.length;
    $("applicationCount").textContent = state.applications.length;
    $("skillCount").textContent = skills.length;

    $("candidateName").textContent =
        state.profile.fullName || "Candidate";

    $("welcome").textContent = state.profile.fullName
        ? `Welcome, ${state.profile.fullName}`
        : "Candidate Dashboard";

    $("userAvatar").textContent =
        (state.profile.fullName || "C").charAt(0).toUpperCase();

    $("passportStatus").textContent =
        state.passportVerified ? "Verified" : "Not Verified";

    $("passportStatus").classList.toggle(
        "verified",
        state.passportVerified
    );

    $("passportDescription").textContent = state.passportVerified
        ? "Your Skill Passport is verified. Keep your skills and assessments updated."
        : "Complete the required verification and skill assessments to unlock your Skill Passport.";
}

let selectedSkills = [];

function renderSelectedSkills() {
    const holder = $("selectedSkills");
    if (!holder) return;
    holder.innerHTML = "";
    selectedSkills.forEach((skill) => {
        const chip = document.createElement("span");
        chip.className = "status";
        chip.style.cssText = "display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:16px";
        chip.textContent = skill;
        const remove = document.createElement("button");
        remove.type = "button"; remove.textContent = "×"; remove.setAttribute("aria-label", `Remove ${skill}`);
        remove.style.cssText = "border:0;background:transparent;cursor:pointer;font-size:18px";
        remove.addEventListener("click", () => { selectedSkills = selectedSkills.filter(s => s !== skill); syncSkills(); renderSelectedSkills(); updateStats(); });
        chip.appendChild(remove); holder.appendChild(chip);
    });
    const hidden = $("skills"); if (hidden) hidden.value = selectedSkills.join(", ");
}
function syncSkills() { state.profile.skills = selectedSkills.join(", "); }
async function loadProfileOptions() {
    const [options, skills] = await Promise.all([apiRequest("/api/profile-options"), apiRequest("/api/skills")]);
    const fill = (id, values, placeholder) => { const el=$(id); if(!el)return; el.innerHTML=`<option value="">${placeholder}</option>`; values.forEach(v=>{const o=document.createElement("option");o.value=typeof v === "string"?v:v.name;o.textContent=typeof v === "string"?v:v.name;el.appendChild(o);}); };
    fill("degree", options.degrees, "Select degree"); fill("branch", options.branches, "Select branch"); fill("college", options.colleges, "Select college"); fill("skillSelect", skills, "Select a skill");
}
function populateProfileForm() {
    ["fullName","email","phone","degree","branch","college","graduationYear","experience","bio"].forEach(id=>{const el=$(id);if(el){const key={fullName:"fullName",graduationYear:"graduationYear"}[id]||id;el.value=state.profile[key]??"";}});
    const edu=$("education"); if(edu) edu.value=[state.profile.degree,state.profile.branch].filter(Boolean).join(" ");
    selectedSkills=state.profile.skills ? (Array.isArray(state.profile.skills)?state.profile.skills:state.profile.skills.split(",")).map(s=>String(s).trim()).filter(Boolean) : [];
    renderSelectedSkills();
}
function readProfileForm() {
    return {fullName:$("fullName").value.trim(),email:$("email").value.trim(),phone:$("phone").value.trim(),degree:$("degree").value,branch:$("branch").value,college:$("college").value,graduationYear:$("graduationYear").value,experience:$("experience").value.trim(),skills:[...selectedSkills],bio:$("bio").value.trim()};
}
async function loadProfile() {
    try {
        const profile=await apiRequest("/api/candidate/profile");
        state.profile={fullName:profile.full_name||"",email:profile.email||"",phone:profile.phone||"",degree:profile.degree||"",branch:profile.branch||"",college:profile.college||"",graduationYear:profile.graduation_year||"",education:[profile.degree,profile.branch].filter(Boolean).join(" "),experience:profile.experience||"",skills:profile.skills||[],bio:profile.bio||""};
        state.passportVerified=Boolean(profile.passport_verified);
        populateProfileForm(); updateStats(); await loadPassport();
    } catch(error) { showMessage("profileMessage","Could not load profile. Check your database setup and sign-in.",true); console.error("Profile load error",error); }
}
function setFeatureLock(id, locked, message) {
    const section = $(id);
    if (!section) return;
    section.classList.toggle("locked-panel", Boolean(locked));
    section.dataset.lockMessage = locked ? message : "";
    section.setAttribute("aria-busy", locked ? "true" : "false");
}

async function loadPassport() {
    try {
        const data=await apiRequest("/api/skill-passport");
        state.passportVerified=Boolean(data.issued);
        const code=$("passportCode");
        if(code) code.textContent=data.issued
            ? `Verified Passport ID: ${data.passport_code}`
            : `${data.lock_reason || "Complete all required steps to unlock your Skill Passport."} Completed assessments: ${data.completed_skills}/${data.total_skills}.`;
        const holder=$("passportSkills");
        if(holder) holder.innerHTML=(data.skills||[]).map(s=>`<p>${escapeHTML(s.name)} — ${s.latest_status === "COMPLETED" && s.best_percentage !== null ? `${Number(s.best_percentage).toFixed(1)}% · Completed` : "Not verified"}</p>`).join("")||"<p>No skills selected yet.</p>";
        setFeatureLock("passport", !state.passportVerified, data.lock_reason || "Complete every selected skill assessment to unlock your verified Skill Passport.");
        setFeatureLock("matches", !state.passportVerified, "Job Match and Job Recommendations unlock after your verified Skill Passport is generated.");
        updateStats();
        if (state.passportVerified) await loadMatches();
        else {
            state.matches=[];
            const matches=$("matchesList");
            if(matches) matches.innerHTML="<p class=\"empty-state\">Complete all selected skill assessments to unlock job matches and recommendations.</p>";
        }
    } catch(error) {
        state.passportVerified=false;
        setFeatureLock("passport", true, "Could not verify passport status. Refresh or contact support.");
        setFeatureLock("matches", true, "Job Match and Job Recommendations are locked until passport status can be verified.");
        console.warn("Passport could not load",error);
    }
}

async function saveProfile(event) {
    event.preventDefault(); const p=readProfileForm();
    if(!p.fullName || !p.email || !p.phone || !p.degree || !p.branch || !p.college){showMessage("profileMessage","Complete name, email, phone, degree, branch and college.",true);return;}
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p.email)){showMessage("profileMessage","Enter a valid email address.",true);return;}
    const button=$("saveProfileBtn"); if(button)button.disabled=true;
    try {
        await apiRequest("/api/candidate/profile",{method:"PUT",body:JSON.stringify({full_name:p.fullName,email:p.email,phone:p.phone,degree:p.degree,branch:p.branch,college:p.college,graduation_year:p.graduationYear,experience:p.experience,skills:p.skills,bio:p.bio})});
        state.profile={...p,education:[p.degree,p.branch].join(" "),skills:p.skills}; syncSkills(); updateStats(); showMessage("profileMessage","Profile saved. Redirecting to your assessments..."); window.location.href="/assessments";
    } catch(error) { showMessage("profileMessage",error.message||"Unable to save profile. Check required database tables.",true);console.error("Profile save error",error); }
    finally {if(button)button.disabled=false;}
}

async function loadJobs(searchTerm = "") {
    const container = $("jobsList");

    container.innerHTML = `<p class="empty-state">Loading jobs...</p>`;

    try {
        const query = searchTerm
            ? `?search=${encodeURIComponent(searchTerm)}`
            : "";

        /*
         * Replace /api/jobs with your actual jobs endpoint.
         * Expected response: an array or an object containing a jobs array.
         */
        const result = await apiRequest(`/api/jobs${query}`);

        state.jobs = Array.isArray(result)
            ? result
            : result.jobs ?? result.data ?? [];

        renderJobs(state.jobs, "jobsList");
    } catch (error) {
        container.innerHTML = `
            <p class="empty-state">
                Could not load jobs. Connect the dashboard to your backend API.
            </p>`;

        console.info("Jobs API is not connected yet.", error.message);
    }
}

async function loadMatches() {
    const container = $("matchesList");
    if (!state.passportVerified) {
        if (container) container.innerHTML = `<p class="empty-state">Complete all selected skill assessments to unlock job matches and recommendations.</p>`;
        state.matches = [];
        updateStats();
        return;
    }
    container.innerHTML = `<p class="empty-state">Loading recommendations...</p>`;

    try {
        /*
         * Replace this route with your actual recommendation endpoint.
         */
        const result = await apiRequest("/api/jobs/recommendations");

        state.matches = Array.isArray(result)
            ? result
            : result.jobs ?? result.matches ?? result.data ?? [];

        renderJobs(state.matches, "matchesList", true);
        updateStats();
    } catch (error) {
        container.innerHTML = `
            <p class="empty-state">
                Job recommendations will appear when the recommendation API is connected.
            </p>`;

        console.info("Recommendations API is not connected yet.", error.message);
    }
}

async function loadApplications() {
    const container = $("applicationsList");

    container.innerHTML = `
        <tr>
            <td colspan="4" class="empty-state">Loading applications...</td>
        </tr>`;

    try {
        /*
         * Replace /api/my-applications with your actual endpoint.
         */
        const result = await apiRequest("/api/my-applications");

        state.applications = Array.isArray(result)
            ? result
            : result.applications ?? result.data ?? [];

        renderApplications(state.applications);
        updateStats();
    } catch (error) {
        container.innerHTML = `
            <tr>
                <td colspan="4" class="empty-state">
                    Could not load applications. Check the backend API route.
                </td>
            </tr>`;

        console.info("Applications API is not connected yet.", error.message);
    }
}

async function applyForJob(jobId, button) {
    if (!jobId) return;

    if (!confirm("Do you want to apply for this job?")) {
        return;
    }

    button.disabled = true;
    button.textContent = "Applying...";

    try {
        await apiRequest("/api/applications", {
            method: "POST",
            body: JSON.stringify({
                job_id: jobId
            })
        });

        alert("Application submitted successfully.");

        await Promise.all([
            loadApplications(),
            loadJobs($("jobSearch").value.trim()),
            loadMatches()
        ]);
    } catch (error) {
        alert(
            "Unable to submit your application. Make sure you are logged in and the application API is configured."
        );

        console.error("Application error:", error);
    } finally {
        button.disabled = false;
        button.textContent = "Apply Now";
    }
}

function setupEventListeners() {
    $("profileForm").addEventListener("submit", saveProfile);
    if ($("addSkillBtn")) $("addSkillBtn").addEventListener("click", () => { const skill=$("skillSelect").value; if(skill && !selectedSkills.includes(skill)) { selectedSkills.push(skill); syncSkills(); renderSelectedSkills(); updateStats(); } });

    $("editProfileBtn").addEventListener("click", () => {
        $("fullName").focus();
        $("profile").scrollIntoView({ behavior: "smooth" });
    });

    $("searchJobsBtn").addEventListener("click", () => {
        loadJobs($("jobSearch").value.trim());
    });

    $("jobSearch").addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            loadJobs($("jobSearch").value.trim());
        }
    });

    $("refreshJobsBtn").addEventListener("click", () => {
        loadJobs($("jobSearch").value.trim());
    });

    $("refreshApplicationsBtn").addEventListener("click", loadApplications);

    document.addEventListener("click", (event) => {
        const button = event.target.closest(".apply-btn");

        if (button) {
            applyForJob(button.dataset.jobId, button);
        }
    });

    $("assessmentBtn").addEventListener("click", () => {
        /*
         * Replace this with your actual assessment page URL.
         */
        window.location.href = "/assessments";
    });
}

async function initializeDashboard() {
    setupEventListeners();
    populateProfileForm();
    updateStats();

    try { await loadProfileOptions(); } catch(error) { console.error("Could not load profile options",error); }
    await Promise.all([
        loadProfile(),
        loadJobs(),
        loadApplications()
    ]);
}

document.addEventListener("DOMContentLoaded", initializeDashboard);