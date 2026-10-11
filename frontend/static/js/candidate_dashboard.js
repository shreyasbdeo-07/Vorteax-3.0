const API_BASE = ""; 

const state = {
    jobs: [],
    matches: [],
    applications: [],
    projects: [],
    simulatedSkills: [],
    isSimulating: false,
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

    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
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
    const skills = job.skills ?? job.required_skills ?? job.skills_required ?? [];
    if (Array.isArray(skills)) return skills;
    return String(skills).split(",").map((s) => s.trim()).filter(Boolean);
}

// ── Standard Jobs List Renderer ──────────────────────────────────────
function renderJobs(jobs, containerId) {
    const container = $(containerId);
    if (!container) return;

    if (!jobs.length) {
        container.innerHTML = `<p class="empty-state">No jobs found matching your criteria.</p>`;
        return;
    }

    container.innerHTML = jobs.map((job) => {
        const id = getJobId(job);
        const title = escapeHTML(getJobTitle(job));
        const company = escapeHTML(getCompanyName(job));
        const description = escapeHTML(getJobDescription(job));
        const location = escapeHTML(job.location ?? "Location not specified");
        const salary = escapeHTML(job.salary_range ?? "Competitive");

        const skills = getJobSkills(job)
            .map((skill) => `<span class="skill-tag">${escapeHTML(skill)}</span>`)
            .join("");

        const safeId = escapeHTML(id ?? "");

        return `
            <article class="job-card">
                <div class="job-card-top">
                    <div>
                        <h3>${title}</h3>
                        <p class="job-company">${company}</p>
                    </div>
                </div>
                <p class="job-description">${description}</p>
                <div class="job-meta">
                    <span>📍 ${location}</span>
                    <span>💰 ${salary}</span>
                    <div class="job-skills-wrap">${skills}</div>
                </div>
                <div class="job-actions">
                    <button class="primary-btn apply-btn" data-job-id="${safeId}">
                        Apply Now
                    </button>
                </div>
            </article>`;
    }).join("");
}

// ── Ultra-Clean AI Match Cards Renderer ──────────────────────────────
function renderMatches(matches, isSimulation = false) {
    const container = $("matchesList");
    if (!container) return;

    if (!matches.length) {
        container.innerHTML = `<p class="empty-state">No matching opportunities found. Try updating your profile skills.</p>`;
        return;
    }

    container.innerHTML = matches.map((item) => {
        const id = item.job_id ?? item.id;
        const title = escapeHTML(item.job_title ?? item.title ?? "Position");
        const company = escapeHTML(item.company_name ?? item.company ?? "Company");
        const location = escapeHTML(item.location ?? "Pune / Hybrid");
        const salary = escapeHTML(item.salary_range ?? "Competitive");

        const evalData = item.evaluation || {};
        const score = isSimulation ? item.simulated_score : (evalData.match_percentage ?? item.match_score ?? 0);
        const baselineScore = item.baseline_score ?? score;
        const delta = item.score_delta ?? 0;
        const tier = isSimulation ? (item.simulated_tier || "Match") : (evalData.match_tier || "Moderate Match");
        const isEligible = evalData.is_eligible !== false && item.is_eligible !== false;
        const matchedSkills = evalData.matched_skills || item.newly_matched_skills || [];
        const missingSkills = evalData.missing_skills || item.remaining_missing || [];
        const explanation = item.explanation || evalData.explanation || "";
        const recommendations = item.learning_recommendations || evalData.learning_recommendations || [];
        const practicalBoost = evalData.practical_boost || 0;
        const practicalSkills = evalData.practical_skills || [];

        // Tier Color & Badge
        let tierColor = "blue";
        let tierLabel = "Moderate Fit";
        if (score >= 75) {
            tierColor = "green";
            tierLabel = "Top Fit";
        } else if (score < 50) {
            tierColor = "amber";
            tierLabel = "Developing Fit";
        }

        // Score Pill
        let scorePillHTML = "";
        if (isSimulation && delta > 0) {
            scorePillHTML = `
                <div class="match-score-pill sim-boosted" title="Simulated score upgrade">
                    <div class="sim-from-to">
                        <span class="sim-old">${baselineScore}%</span>
                        <span class="sim-arr">➔</span>
                        <span class="sim-new">${score}%</span>
                    </div>
                    <span class="sim-boost-badge">+${delta}% Boost</span>
                </div>
            `;
        } else {
            scorePillHTML = `
                <div class="match-score-pill fit-${tierColor}">
                    <span class="match-pct">${score}%</span>
                    <span class="match-tier-txt">${tierLabel}</span>
                </div>
            `;
        }

        // Skills List
        const matchedHTML = matchedSkills.length
            ? matchedSkills.map(s => `<span class="skill-pill has-skill">✓ ${escapeHTML(s)}</span>`).join("")
            : `<span class="skill-pill muted-skill">No exact skill matched yet</span>`;

        const missingHTML = missingSkills.length
            ? missingSkills.map(s => `<span class="skill-pill need-skill">⚡ ${escapeHTML(s)}</span>`).join("")
            : `<span class="skill-pill all-good-skill">✓ All requirements met!</span>`;

        const practicalBadgeHTML = practicalBoost > 0
            ? `<div class="practical-boost-ribbon">
                   <span>🚀 <strong>+${practicalBoost}% Practical Boost</strong> from verified portfolio projects (${escapeHTML(practicalSkills.join(", "))})</span>
               </div>`
            : "";

        // Learning Roadmap Section
        let roadmapHTML = "";
        if (recommendations && recommendations.length > 0) {
            const steps = recommendations.map(rec => `
                <div class="learning-step-row">
                    <div class="step-skill-col">
                        <span class="step-tag">${escapeHTML(rec.skill)}</span>
                        <strong>${escapeHTML(rec.topic)}</strong>
                    </div>
                    <div class="step-action-col">
                        <a href="${escapeHTML(rec.url)}" target="_blank" rel="noopener noreferrer" class="guide-btn">
                            📖 Guide: ${escapeHTML(rec.resource)} ↗
                        </a>
                        <a href="/assessments" class="verify-btn">
                            ⚡ Verify
                        </a>
                    </div>
                </div>
            `).join("");

            roadmapHTML = `
                <details class="growth-roadmap-details">
                    <summary class="growth-summary">
                        <span>💡 AI Insights & Learning Roadmap (${recommendations.length} Skill Gap${recommendations.length > 1 ? 's' : ''})</span>
                        <span class="toggle-hint">Click to expand guide</span>
                    </summary>
                    <div class="roadmap-expanded-content">
                        <p class="ai-insight-line">"${escapeHTML(explanation)}"</p>
                        <div class="learning-steps-list">
                            ${steps}
                        </div>
                    </div>
                </details>
            `;
        } else {
            roadmapHTML = `
                <div class="ready-to-apply-note">
                    <span>🎉 <strong>Perfect Alignment:</strong> You possess all required skills for this role.</span>
                </div>
            `;
        }

        const safeId = escapeHTML(id ?? "");

        return `
            <article class="job-card clean-match-card fit-border-${tierColor}">
                <div class="card-main-header">
                    <div class="job-meta-header">
                        <div class="company-and-location">
                            <span class="company-badge">${company}</span>
                            <span class="meta-dot">•</span>
                            <span class="location-badge">📍 ${location}</span>
                            <span class="meta-dot">•</span>
                            <span class="salary-badge">💰 ${salary}</span>
                        </div>
                        <h3 class="job-card-title">${title}</h3>
                    </div>
                    ${scorePillHTML}
                </div>

                <!-- Competency Breakdown -->
                <div class="competencies-card-section">
                    <div class="comp-row">
                        <span class="comp-label">Skills You Have:</span>
                        <div class="comp-pills-wrap">${matchedHTML}</div>
                    </div>
                    <div class="comp-row">
                        <span class="comp-label">Skills To Learn:</span>
                        <div class="comp-pills-wrap">${missingHTML}</div>
                    </div>
                    ${practicalBadgeHTML}
                </div>

                <!-- AI Insights & Roadmap -->
                ${roadmapHTML}

                <!-- Action Footer -->
                <div class="card-action-footer">
                    <span class="eligibility-status-text">
                        ${isEligible ? '<span class="status-icon green">✓</span> Meets mandatory criteria' : '<span class="status-icon orange">⚠</span> Has eligibility requirements'}
                    </span>
                    <button class="primary-btn apply-btn-compact apply-btn" data-job-id="${safeId}">
                        Apply for Role
                    </button>
                </div>
            </article>
        `;
    }).join("");
}

// ── Applications Renderer ────────────────────────────────────────────
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
        const title = escapeHTML(application.job_title ?? application.title ?? "Job");
        const company = escapeHTML(application.company_name ?? application.company ?? "Company");
        const dateValue = application.applied_at ?? application.created_at;
        const date = dateValue ? escapeHTML(String(dateValue).slice(0, 10)) : "—";
        const status = String(application.status ?? "Pending").toLowerCase();
        const safeStatus = escapeHTML(status);
        const displayStatus = escapeHTML(status.replace(/[-_]/g, " ").replace(/\b\w/g, l => l.toUpperCase()));

        return `
            <tr>
                <td>${title}</td>
                <td>${company}</td>
                <td>${date}</td>
                <td><span class="status ${safeStatus}">${displayStatus}</span></td>
            </tr>`;
    }).join("");
}

// ── Projects Renderer ────────────────────────────────────────────────
function renderProjects(projects) {
    const container = $("projectsList");
    if (!container) return;

    if (!projects || !projects.length) {
        container.innerHTML = `<p class="empty-state" style="padding: 15px;">No practical projects added yet. Showcase your projects to earn up to +15% practical experience boost!</p>`;
        return;
    }

    container.innerHTML = projects.map(proj => {
        const title = escapeHTML(proj.title);
        const tech = escapeHTML(proj.tech_stack || "");
        const desc = escapeHTML(proj.description || "");
        const github = proj.github_url ? `<a href="${escapeHTML(proj.github_url)}" target="_blank" class="project-link" rel="noopener">📂 GitHub Repo</a>` : "";
        const live = proj.live_url ? `<a href="${escapeHTML(proj.live_url)}" target="_blank" class="project-link" rel="noopener">🌐 Live Demo</a>` : "";

        const techChips = tech ? tech.split(",").map(t => `<span class="chip matched-chip">${escapeHTML(t.trim())}</span>`).join("") : "";

        return `
            <div class="project-card">
                <div class="project-header">
                    <div>
                        <h4 style="font-size: 15px; color: var(--text); font-weight: 700;">${title}</h4>
                        <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top: 6px;">${techChips}</div>
                    </div>
                    <button type="button" class="delete-project-btn" data-project-id="${proj.id}" title="Remove project">×</button>
                </div>
                ${desc ? `<p style="font-size: 13px; color: #555; margin-top: 8px;">${desc}</p>` : ""}
                <div style="display: flex; gap: 15px; margin-top: 10px;">
                    ${github}
                    ${live}
                </div>
            </div>
        `;
    }).join("");
}

// ── Stats Updater ────────────────────────────────────────────────────
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

    if ($("profileCompletion")) $("profileCompletion").textContent = `${completion}%`;
    if ($("profileProgress")) $("profileProgress").style.width = `${completion}%`;
    if ($("matchCount")) $("matchCount").textContent = state.matches.length;
    if ($("applicationCount")) $("applicationCount").textContent = state.applications.length;
    if ($("skillCount")) $("skillCount").textContent = skills.length;

    if ($("candidateName")) $("candidateName").textContent = state.profile.fullName || "Candidate";
    if ($("welcome")) $("welcome").textContent = state.profile.fullName ? `Welcome, ${state.profile.fullName}` : "Candidate Dashboard";
    if ($("userAvatar")) $("userAvatar").textContent = (state.profile.fullName || "C").charAt(0).toUpperCase();

    if ($("passportStatus")) {
        $("passportStatus").textContent = state.passportVerified ? "Verified" : "Not Verified";
        $("passportStatus").classList.toggle("verified", state.passportVerified);
    }

    if ($("passportDescription")) {
        $("passportDescription").textContent = state.passportVerified
            ? "Your Skill Passport is verified. Keep your skills and assessments updated."
            : "Complete the required verification and skill assessments to unlock your Skill Passport.";
    }
}

// ── Profile Form Management ──────────────────────────────────────────
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
        remove.type = "button";
        remove.textContent = "×";
        remove.setAttribute("aria-label", `Remove ${skill}`);
        remove.style.cssText = "border:0;background:transparent;cursor:pointer;font-size:18px";
        remove.addEventListener("click", () => {
            selectedSkills = selectedSkills.filter(s => s !== skill);
            syncSkills();
            renderSelectedSkills();
            updateStats();
        });
        chip.appendChild(remove);
        holder.appendChild(chip);
    });
    const hidden = $("skills");
    if (hidden) hidden.value = selectedSkills.join(", ");
}

function syncSkills() {
    state.profile.skills = selectedSkills.join(", ");
}

async function loadProfileOptions() {
    const [options, skills] = await Promise.all([apiRequest("/api/profile-options"), apiRequest("/api/skills")]);
    const fill = (id, values, placeholder) => {
        const el = $(id);
        if (!el) return;
        el.innerHTML = `<option value="">${placeholder}</option>`;
        values.forEach(v => {
            const o = document.createElement("option");
            o.value = typeof v === "string" ? v : v.name;
            o.textContent = typeof v === "string" ? v : v.name;
            el.appendChild(o);
        });
    };
    fill("degree", options.degrees, "Select degree");
    fill("branch", options.branches, "Select branch");
    fill("college", options.colleges, "Select college");
    fill("skillSelect", skills, "Select a skill");
}

function populateProfileForm() {
    ["fullName","email","phone","degree","branch","college","graduationYear","experience","bio"].forEach(id => {
        const el = $(id);
        if (el) {
            const key = {fullName:"fullName", graduationYear:"graduationYear"}[id] || id;
            el.value = state.profile[key] ?? "";
        }
    });
    const edu = $("education");
    if (edu) edu.value = [state.profile.degree, state.profile.branch].filter(Boolean).join(" ");
    selectedSkills = state.profile.skills
        ? (Array.isArray(state.profile.skills) ? state.profile.skills : state.profile.skills.split(",")).map(s => String(s).trim()).filter(Boolean)
        : [];
    renderSelectedSkills();
}

function readProfileForm() {
    return {
        fullName: $("fullName").value.trim(),
        email: $("email").value.trim(),
        phone: $("phone").value.trim(),
        degree: $("degree").value,
        branch: $("branch").value,
        college: $("college").value,
        graduationYear: $("graduationYear").value,
        experience: $("experience").value.trim(),
        skills: [...selectedSkills],
        bio: $("bio").value.trim()
    };
}

async function loadProfile() {
    try {
        const profile = await apiRequest("/api/candidate/profile");
        state.profile = {
            fullName: profile.full_name || "",
            email: profile.email || "",
            phone: profile.phone || "",
            degree: profile.degree || "",
            branch: profile.branch || "",
            college: profile.college || "",
            graduationYear: profile.graduation_year || "",
            education: [profile.degree, profile.branch].filter(Boolean).join(" "),
            experience: profile.experience || "",
            skills: profile.skills || [],
            bio: profile.bio || ""
        };
        state.passportVerified = Boolean(profile.passport_verified);
        populateProfileForm();
        updateStats();
        await loadPassport();
    } catch(error) {
        showMessage("profileMessage", "Could not load profile. Check database setup and sign-in.", true);
    }
}

async function loadPassport() {
    try {
        const data = await apiRequest("/api/skill-passport");
        state.passportVerified = Boolean(data.issued);
        const code = $("passportCode");
        if (code) {
            code.textContent = data.issued
                ? `Passport ID: ${data.passport_code}`
                : `Assess all ${data.total_skills} selected skill(s) to issue your Skill Passport. Completed: ${data.completed_skills}/${data.total_skills}.`;
        }
        const holder = $("passportSkills");
        if (holder) {
            holder.innerHTML = (data.skills || [])
                .map(s => `<p>${escapeHTML(s.name)} — ${s.best_percentage === null ? "Not assessed" : `${Number(s.best_percentage).toFixed(1)}%`}</p>`)
                .join("") || "<p>No skills selected yet.</p>";
        }
        updateStats();
    } catch(error) {
        console.warn("Passport could not load", error);
    }
}

async function saveProfile(event) {
    event.preventDefault();
    const p = readProfileForm();
    if (!p.fullName || !p.email || !p.degree || !p.branch || !p.college) {
        showMessage("profileMessage", "Complete name, email, degree, branch and college.", true);
        return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p.email)) {
        showMessage("profileMessage", "Enter a valid email address.", true);
        return;
    }
    const button = $("saveProfileBtn");
    if (button) button.disabled = true;
    try {
        await apiRequest("/api/candidate/profile", {
            method: "PUT",
            body: JSON.stringify({
                full_name: p.fullName,
                email: p.email,
                phone: p.phone,
                degree: p.degree,
                branch: p.branch,
                college: p.college,
                graduation_year: p.graduationYear,
                experience: p.experience,
                skills: p.skills,
                bio: p.bio
            })
        });
        state.profile = { ...p, education: [p.degree, p.branch].join(" "), skills: p.skills };
        syncSkills();
        updateStats();
        showMessage("profileMessage", "Profile saved successfully. AI job matches refreshed!");
        loadMatches();
    } catch(error) {
        showMessage("profileMessage", error.message || "Unable to save profile.", true);
    } finally {
        if (button) button.disabled = false;
    }
}

// ── Projects CRUD Functions ──────────────────────────────────────────
async function loadProjects() {
    try {
        const projects = await apiRequest("/api/candidate/projects");
        state.projects = Array.isArray(projects) ? projects : [];
        renderProjects(state.projects);
    } catch (err) {
        console.warn("Projects load failed", err);
    }
}

async function saveProject() {
    const title = $("projectTitle").value.trim();
    const tech = $("projectTech").value.trim();
    const github = $("projectGithub").value.trim();
    const live = $("projectLive").value.trim();
    const desc = $("projectDesc").value.trim();

    if (!title || !tech) {
        alert("Please provide at least a project title and tech stack.");
        return;
    }

    const btn = $("saveProjectBtn");
    btn.disabled = true;
    try {
        await apiRequest("/api/candidate/projects", {
            method: "POST",
            body: JSON.stringify({
                title: title,
                tech_stack: tech,
                github_url: github,
                live_url: live,
                description: desc
            })
        });

        // Reset form
        $("projectTitle").value = "";
        $("projectTech").value = "";
        $("projectGithub").value = "";
        $("projectLive").value = "";
        $("projectDesc").value = "";
        $("newProjectForm").style.display = "none";

        await loadProjects();
        await loadMatches();
    } catch (err) {
        alert("Could not save project: " + err.message);
    } finally {
        btn.disabled = false;
    }
}

async function deleteProject(id) {
    if (!confirm("Are you sure you want to remove this project?")) return;
    try {
        await apiRequest(`/api/candidate/projects/${id}`, { method: "DELETE" });
        await loadProjects();
        await loadMatches();
    } catch (err) {
        alert("Could not remove project: " + err.message);
    }
}

// ── What-If Skill Simulator (Ultra-Intuitive Interactive Controls) ────
function updateSimStatusUI() {
    const badge = $("simStatusBadge");
    const resetBtn = $("clearSimSkillsBtn");
    const count = state.simulatedSkills.length;

    if (badge) {
        if (state.isSimulating) {
            badge.innerHTML = `<span class="status-dot active-sim"></span> ⚡ Live Preview Active (${count} Skill${count > 1 ? 's' : ''})`;
            badge.className = "what-if-status-badge is-active-mode";
        } else if (count > 0) {
            badge.innerHTML = `<span class="status-dot pulsing"></span> ${count} Skill${count > 1 ? 's' : ''} Selected`;
            badge.className = "what-if-status-badge is-pending-mode";
        } else {
            badge.innerHTML = `<span class="status-dot"></span> Baseline View`;
            badge.className = "what-if-status-badge";
        }
    }

    if (resetBtn) {
        resetBtn.style.display = (count > 0 || state.isSimulating) ? "inline-flex" : "none";
    }
}

function toggleSimSkill(skill, buttonElement) {
    const s = skill.trim();
    if (!s) return;

    const index = state.simulatedSkills.findIndex(x => x.toLowerCase() === s.toLowerCase());
    if (index >= 0) {
        // Deselect
        state.simulatedSkills.splice(index, 1);
        if (buttonElement) {
            buttonElement.classList.remove("is-active");
            const sym = buttonElement.querySelector(".pill-sym");
            if (sym) sym.textContent = "+";
        }
    } else {
        // Select
        state.simulatedSkills.push(s);
        if (buttonElement) {
            buttonElement.classList.add("is-active");
            const sym = buttonElement.querySelector(".pill-sym");
            if (sym) sym.textContent = "✓";
        }
    }

    updateSimStatusUI();
}

function addCustomSimSkill(skill) {
    const s = skill.trim();
    if (!s) return;

    if (state.simulatedSkills.map(x => x.toLowerCase()).includes(s.toLowerCase())) {
        return;
    }

    state.simulatedSkills.push(s);

    // Add button dynamically to presets container
    const presetHolder = $("whatIfPresets");
    if (presetHolder) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "sim-toggle-pill is-active";
        btn.dataset.skill = s;
        btn.innerHTML = `<span class="pill-sym">✓</span> ${escapeHTML(s)}`;
        presetHolder.appendChild(btn);
    }

    updateSimStatusUI();
}

async function runWhatIfSimulation() {
    if (!state.simulatedSkills.length) {
        alert("Please select or add at least one skill to simulate (e.g. React, Docker, SQL).");
        return;
    }

    const runBtn = $("runSimulationBtn");
    runBtn.disabled = true;
    runBtn.textContent = "⚡ Calculating...";

    try {
        const result = await apiRequest("/api/matching/what-if", {
            method: "POST",
            body: JSON.stringify({ simulated_skills: state.simulatedSkills })
        });

        state.isSimulating = true;
        const banner = $("simulationBanner");
        if (banner) {
            banner.style.display = "flex";
            $("simUnlockedCount").textContent = result.unlocked_count ?? 0;
            $("simAvgBoost").textContent = `+${result.average_boost ?? 0}%`;
        }

        updateSimStatusUI();
        renderMatches(result.comparisons || [], true);
    } catch (err) {
        alert("Simulation failed: " + err.message);
    } finally {
        runBtn.disabled = false;
        runBtn.textContent = "⚡ Simulate Boost";
    }
}

function exitWhatIfSimulation() {
    state.isSimulating = false;
    const banner = $("simulationBanner");
    if (banner) banner.style.display = "none";
    updateSimStatusUI();
    renderMatches(state.matches, false);
}

function resetWhatIfSimulation() {
    state.simulatedSkills = [];
    document.querySelectorAll(".sim-toggle-pill").forEach(btn => {
        btn.classList.remove("is-active");
        const sym = btn.querySelector(".pill-sym");
        if (sym) sym.textContent = "+";
    });
    exitWhatIfSimulation();
}

// ── Standard Jobs & Matches Loaders ──────────────────────────────────
async function loadJobs(searchTerm = "", isSilent = false) {
    const container = $("jobsList");
    if (!container) return;
    if (!isSilent) {
        container.innerHTML = `<p class="empty-state">Loading jobs...</p>`;
    }

    try {
        const query = searchTerm ? `?search=${encodeURIComponent(searchTerm)}` : "";
        const result = await apiRequest(`/api/jobs${query}`);
        state.jobs = Array.isArray(result) ? result : result.jobs ?? [];
        renderJobs(state.jobs, "jobsList");
    } catch (error) {
        if (!isSilent) {
            container.innerHTML = `<p class="empty-state">Could not load jobs at this time.</p>`;
        }
    }
}

async function loadMatches(isSilent = false) {
    const container = $("matchesList");
    if (!container) return;
    if (!isSilent) {
        container.innerHTML = `<p class="empty-state">Calculating personalized AI job matches...</p>`;
    }

    try {
        const result = await apiRequest("/api/jobs/recommendations");
        state.matches = Array.isArray(result) ? result : result.jobs ?? [];
        if (!state.isSimulating) {
            renderMatches(state.matches, false);
        }
        updateStats();
    } catch (error) {
        if (!isSilent) {
            container.innerHTML = `<p class="empty-state">Could not load job matches. Try updating your profile.</p>`;
        }
    }
}

async function loadApplications(isSilent = false) {
    const container = $("applicationsList");
    if (!container) return;
    if (!isSilent) {
        container.innerHTML = `<tr><td colspan="4" class="empty-state">Loading applications...</td></tr>`;
    }

    try {
        const result = await apiRequest("/api/my-applications");
        state.applications = Array.isArray(result) ? result : [];
        renderApplications(state.applications);
        updateStats();
    } catch (error) {
        if (!isSilent) {
            container.innerHTML = `<tr><td colspan="4" class="empty-state">Could not load applications.</td></tr>`;
        }
    }
}

async function applyForJob(jobId, button) {
    if (!jobId) return;
    if (!confirm("Do you want to submit your application for this position?")) return;

    button.disabled = true;
    button.textContent = "Applying...";

    try {
        await apiRequest("/api/applications", {
            method: "POST",
            body: JSON.stringify({ job_id: jobId })
        });
        alert("Application submitted successfully!");
        await Promise.all([loadApplications(), loadMatches()]);
    } catch (error) {
        alert("Unable to submit application: " + error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Apply for Role";
    }
}

// ── Event Listeners Setup ────────────────────────────────────────────
function setupEventListeners() {
    if ($("profileForm")) $("profileForm").addEventListener("submit", saveProfile);

    if ($("addSkillBtn")) {
        $("addSkillBtn").addEventListener("click", () => {
            const skill = $("skillSelect").value;
            if (skill && !selectedSkills.includes(skill)) {
                selectedSkills.push(skill);
                syncSkills();
                renderSelectedSkills();
                updateStats();
            }
        });
    }

    if ($("editProfileBtn")) {
        $("editProfileBtn").addEventListener("click", () => {
            $("fullName").focus();
            $("profile").scrollIntoView({ behavior: "smooth" });
        });
    }

    if ($("searchJobsBtn")) {
        $("searchJobsBtn").addEventListener("click", () => loadJobs($("jobSearch").value.trim()));
    }
    if ($("jobSearch")) {
        $("jobSearch").addEventListener("keydown", (e) => {
            if (e.key === "Enter") loadJobs($("jobSearch").value.trim());
        });
    }
    if ($("refreshJobsBtn")) {
        $("refreshJobsBtn").addEventListener("click", () => loadJobs($("jobSearch").value.trim()));
    }

    if ($("refreshMatchesBtn")) {
        $("refreshMatchesBtn").addEventListener("click", () => {
            state.isSimulating = false;
            loadMatches();
        });
    }

    if ($("refreshApplicationsBtn")) {
        $("refreshApplicationsBtn").addEventListener("click", loadApplications);
    }

    // Projects events
    if ($("toggleAddProjectBtn")) {
        $("toggleAddProjectBtn").addEventListener("click", () => {
            const f = $("newProjectForm");
            f.style.display = f.style.display === "none" ? "block" : "none";
        });
    }
    if ($("cancelProjectBtn")) {
        $("cancelProjectBtn").addEventListener("click", () => {
            $("newProjectForm").style.display = "none";
        });
    }
    if ($("saveProjectBtn")) {
        $("saveProjectBtn").addEventListener("click", saveProject);
    }

    // What-If Simulator events (Toggle Pills)
    const presetHolder = $("whatIfPresets");
    if (presetHolder) {
        presetHolder.addEventListener("click", (e) => {
            const pill = e.target.closest(".sim-toggle-pill");
            if (pill && pill.dataset.skill) {
                toggleSimSkill(pill.dataset.skill, pill);
            }
        });
    }

    if ($("addSimSkillBtn")) {
        $("addSimSkillBtn").addEventListener("click", () => {
            const val = $("customSimSkill").value.trim();
            if (val) {
                addCustomSimSkill(val);
                $("customSimSkill").value = "";
            }
        });
    }
    if ($("customSimSkill")) {
        $("customSimSkill").addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const val = $("customSimSkill").value.trim();
                if (val) {
                    addCustomSimSkill(val);
                    $("customSimSkill").value = "";
                }
            }
        });
    }

    if ($("clearSimSkillsBtn")) {
        $("clearSimSkillsBtn").addEventListener("click", resetWhatIfSimulation);
    }
    if ($("runSimulationBtn")) {
        $("runSimulationBtn").addEventListener("click", runWhatIfSimulation);
    }
    if ($("exitSimulationBtn")) {
        $("exitSimulationBtn").addEventListener("click", exitWhatIfSimulation);
    }

    // Global click delegate for apply buttons and project deletes
    document.addEventListener("click", (event) => {
        const applyBtn = event.target.closest(".apply-btn");
        if (applyBtn) {
            applyForJob(applyBtn.dataset.jobId, applyBtn);
            return;
        }

        const delProjBtn = event.target.closest(".delete-project-btn");
        if (delProjBtn) {
            deleteProject(delProjBtn.dataset.projectId);
            return;
        }
    });

    if ($("assessmentBtn")) {
        $("assessmentBtn").addEventListener("click", () => {
            window.location.href = "/assessments";
        });
    }

    // Nav tabs instant refresh when clicked
    document.querySelectorAll('a[href="#jobs"], a[href="#matches"], a[href="#applications"]').forEach(link => {
        link.addEventListener("click", () => {
            const query = $("jobSearch") ? $("jobSearch").value.trim() : "";
            loadJobs(query, true);
            if (!state.isSimulating) loadMatches(true);
            loadApplications(true);
        });
    });
}

// ── Initializer ──────────────────────────────────────────────────────
async function initializeDashboard() {
    setupEventListeners();
    populateProfileForm();
    updateStats();

    try { await loadProfileOptions(); } catch(e) { console.error("Profile options failed", e); }
    await Promise.all([
        loadProfile(),
        loadJobs(),
        loadMatches(),
        loadApplications(),
        loadProjects()
    ]);

    // Live Sync: Auto-refresh jobs, matches & applications every 3.5 seconds
    setInterval(async () => {
        if (!state.isSimulating) {
            const currentSearch = $("jobSearch") ? $("jobSearch").value.trim() : "";
            await Promise.all([
                loadJobs(currentSearch, true),
                loadMatches(true),
                loadApplications(true)
            ]);
        }
    }, 3500);

    // Refresh immediately when user switches back to this tab
    window.addEventListener("focus", () => {
        if (!state.isSimulating) {
            const currentSearch = $("jobSearch") ? $("jobSearch").value.trim() : "";
            loadJobs(currentSearch, true);
            loadMatches(true);
            loadApplications(true);
        }
    });
}

document.addEventListener("DOMContentLoaded", initializeDashboard);