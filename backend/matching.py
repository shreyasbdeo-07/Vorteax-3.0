"""
backend/matching.py — VORTEXA 3.0 / RozgarLink Matching Engine
=============================================================
Core Features:
1. Rule-based mandatory eligibility checks
2. AI-powered semantic skill matching (sentence-transformers/all-MiniLM-L6-v2)
3. Skill gap analysis (matched vs missing competencies)
4. Match explanations & personalized learning recommendations
5. Candidate & Job ranking utilities
"""

import os
from typing import Any

# Global cached model reference
_MODEL = None


def get_model():
    """Lazy loader for SentenceTransformer to optimize memory and startup time."""
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _MODEL


# ── Curated Learning Resources Map ────────────────────────────────────
LEARNING_RESOURCES = {
    "python": {
        "topic": "Python Programming",
        "resource": "Official Python Tutorial & Real Python",
        "type": "Documentation & Hands-on",
        "url": "https://docs.python.org/3/tutorial/"
    },
    "flask": {
        "topic": "Flask Web Development",
        "resource": "Flask Mega-Tutorial (Miguel Grinberg)",
        "type": "Full Project Guide",
        "url": "https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world"
    },
    "react": {
        "topic": "React.js Modern Frontend",
        "resource": "React.dev Interactive Docs",
        "type": "Interactive Tutorial",
        "url": "https://react.dev/learn"
    },
    "sql": {
        "topic": "Relational Databases & SQL",
        "resource": "SQLZoo & Mode SQL Tutorial",
        "type": "Interactive Practice",
        "url": "https://sqlzoo.net/"
    },
    "machine learning": {
        "topic": "Machine Learning Fundamentals",
        "resource": "Scikit-Learn Tutorials & Fast.ai",
        "type": "Comprehensive Course",
        "url": "https://scikit-learn.org/stable/tutorial/index.html"
    },
    "docker": {
        "topic": "Docker & Containerization",
        "resource": "Docker Getting Started Guide",
        "type": "Hands-on Labs",
        "url": "https://docs.docker.com/get-started/"
    },
    "javascript": {
        "topic": "JavaScript & DOM Manipulation",
        "resource": "MDN Web Docs JavaScript Guide",
        "type": "Reference & Exercises",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"
    },
    "data analysis": {
        "topic": "Pandas & Data Analysis",
        "resource": "10 Minutes to Pandas",
        "type": "Practical Guide",
        "url": "https://pandas.pydata.org/docs/user_guide/10min.html"
    }
}


def _normalize_skill_list(skills: Any) -> list[str]:
    """Parse comma-separated strings or lists into clean lowercase skill names."""
    if not skills:
        return []
    if isinstance(skills, str):
        raw_items = skills.split(",")
    elif isinstance(skills, (list, tuple, set)):
        raw_items = list(skills)
    else:
        raw_items = [str(skills)]

    cleaned = []
    for item in raw_items:
        s = str(item).strip()
        if s:
            cleaned.append(s)
    return cleaned


# ── 1. Rule-Based Mandatory Eligibility Checks ────────────────────────

def check_eligibility(candidate: dict, job: dict) -> tuple[bool, list[str]]:
    """
    Evaluates mandatory qualification rules before semantic matching.
    Returns: (is_eligible: bool, failed_criteria: list[str])
    """
    failed = []

    # Check minimum graduation year (if job specifies a required batch)
    min_grad_year = job.get("min_graduation_year")
    cand_grad_year = candidate.get("graduation_year")
    if min_grad_year and cand_grad_year:
        try:
            if int(cand_grad_year) < int(min_grad_year):
                failed.append(
                    f"Graduation year {cand_grad_year} is below requirement ({min_grad_year}+)."
                )
        except (ValueError, TypeError):
            pass

    # Check required education degree keyword (e.g. B.Tech / BE / BCA / MCA / Diploma)
    req_degree = job.get("required_degree")
    cand_education = candidate.get("education", "") or candidate.get("degree", "")
    if req_degree and cand_education:
        req_norm = req_degree.strip().lower()
        cand_norm = cand_education.strip().lower()
        if req_norm not in cand_norm and cand_norm not in req_norm:
            failed.append(
                f"Candidate degree '{cand_education}' does not fulfill required '{req_degree}'."
            )

    # Check location constraints (e.g., if strictly On-site in a city)
    job_loc = str(job.get("location", "")).lower()
    cand_loc = str(candidate.get("location", "")).lower()
    if job.get("strict_location") and job_loc and "remote" not in job_loc:
        if cand_loc and job_loc not in cand_loc and cand_loc not in job_loc:
            failed.append(f"Candidate location '{cand_loc}' does not match '{job_loc}'.")

    return (len(failed) == 0, failed)


# ── 2. AI-Powered Semantic Skill Matching ─────────────────────────────

def compute_semantic_similarity(source_text: str, target_text: str) -> float:
    """
    Computes cosine similarity between two texts using all-MiniLM-L6-v2.
    Returns float score between 0.0 and 1.0.
    """
    if not source_text or not target_text:
        return 0.0

    model = get_model()
    embeddings = model.encode([source_text, target_text], normalize_embeddings=True)
    similarity = model.similarity(embeddings[0:1], embeddings[1:2]).item()
    return max(0.0, min(1.0, float(similarity)))


# ── 3. Skill Gap Analysis & Matching ──────────────────────────────────

def analyze_skill_gaps(
    candidate_skills: list[str],
    job_skills: list[str],
    match_threshold: float = 0.60
) -> dict[str, Any]:
    """
    Compares candidate skills against required skills using semantic similarity.
    Returns:
    - matched_skills: list of job skills candidate possesses
    - missing_skills: list of job skills candidate lacks
    - skill_breakdown: detailed scores per required skill
    """
    if not job_skills:
        return {"matched_skills": [], "missing_skills": [], "skill_breakdown": {}}

    if not candidate_skills:
        return {
            "matched_skills": [],
            "missing_skills": list(job_skills),
            "skill_breakdown": {s: 0.0 for s in job_skills}
        }

    model = get_model()
    cand_emb = model.encode(candidate_skills, normalize_embeddings=True)
    job_emb = model.encode(job_skills, normalize_embeddings=True)

    sim_matrix = model.similarity(job_emb, cand_emb)

    matched = []
    missing = []
    breakdown = {}

    for i, job_skill in enumerate(job_skills):
        best_score = sim_matrix[i].max().item()
        best_cand_idx = sim_matrix[i].argmax().item()
        best_cand_skill = candidate_skills[best_cand_idx]

        breakdown[job_skill] = {
            "score": round(best_score, 3),
            "closest_candidate_skill": best_cand_skill,
            "matched": best_score >= match_threshold
        }

        if best_score >= match_threshold:
            matched.append(job_skill)
        else:
            missing.append(job_skill)

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "skill_breakdown": breakdown
    }


# ── 4. Learning Recommendations ───────────────────────────────────────

def get_learning_recommendations(missing_skills: list[str]) -> list[dict[str, str]]:
    """Generates curated study materials and next steps for identified skill gaps."""
    recommendations = []
    for skill in missing_skills:
        skill_lower = skill.lower()
        # Find closest pre-defined resource or generate a structured recommendation
        found = None
        for key, info in LEARNING_RESOURCES.items():
            if key in skill_lower or skill_lower in key:
                found = info
                break

        if found:
            recommendations.append({
                "skill": skill,
                "topic": found["topic"],
                "resource": found["resource"],
                "type": found["type"],
                "url": found["url"]
            })
        else:
            recommendations.append({
                "skill": skill,
                "topic": f"Mastering {skill}",
                "resource": f"Explore documentation and projects for {skill}",
                "type": "Self-paced Guided Practice",
                "url": f"https://www.google.com/search?q={skill}+beginner+tutorial+project"
            })
    return recommendations


# ── 5. End-to-End Match Evaluator ─────────────────────────────────────

def match_candidate_to_job(candidate: dict, job: dict) -> dict[str, Any]:
    """
    Evaluates candidate eligibility, skill match percentage, explanations,
    gaps, and learning recommendations.
    """
    is_eligible, eligibility_reasons = check_eligibility(candidate, job)

    cand_skills = _normalize_skill_list(
        candidate.get("skills") or candidate.get("skills_required") or []
    )
    job_skills = _normalize_skill_list(
        job.get("skills_required") or job.get("skills") or []
    )

    # Contextual overview text
    cand_context = f"{' '.join(cand_skills)}. {candidate.get('bio', '')}".strip()
    job_context = f"{job.get('title', '')}. {' '.join(job_skills)}. {job.get('description', '')}".strip()

    # Calculate overall semantic similarity
    overall_sim = compute_semantic_similarity(cand_context, job_context)

    # Detailed skill gap analysis
    gap_analysis = analyze_skill_gaps(cand_skills, job_skills)
    matched_skills = gap_analysis["matched_skills"]
    missing_skills = gap_analysis["missing_skills"]

    # Calculate weighted percentage score
    if job_skills:
        coverage_ratio = len(matched_skills) / len(job_skills)
        # 60% weight on skill coverage, 40% on overall contextual similarity
        raw_score = (coverage_ratio * 0.60) + (overall_sim * 0.40)
    else:
        raw_score = overall_sim

    # Penalty if mandatory criteria fail
    if not is_eligible:
        raw_score = min(raw_score, 0.45)

    match_percentage = round(raw_score * 100, 1)

    # Match tier label
    if match_percentage >= 75:
        match_tier = "Strong Match"
    elif match_percentage >= 50:
        match_tier = "Moderate Match"
    else:
        match_tier = "Low Match"

    # Human-readable explanation
    explanation_parts = []
    if is_eligible:
        explanation_parts.append("Candidate meets all mandatory eligibility criteria.")
    else:
        explanation_parts.append(
            f"Eligibility Notice: {'; '.join(eligibility_reasons)}"
        )

    if matched_skills:
        explanation_parts.append(f"Strong overlap in: {', '.join(matched_skills)}.")
    if missing_skills:
        explanation_parts.append(f"Recommended areas to develop: {', '.join(missing_skills)}.")

    explanation = " ".join(explanation_parts)

    recommendations = get_learning_recommendations(missing_skills)

    return {
        "candidate_id": candidate.get("id"),
        "job_id": job.get("id"),
        "is_eligible": is_eligible,
        "eligibility_reasons": eligibility_reasons,
        "match_percentage": match_percentage,
        "match_tier": match_tier,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "explanation": explanation,
        "learning_recommendations": recommendations,
        "skill_breakdown": gap_analysis["skill_breakdown"]
    }


# ── 6. Candidate & Job Ranking Functions ──────────────────────────────

def rank_candidates_for_job(candidates: list[dict], job: dict) -> list[dict]:
    """Ranks all candidates for an employer's job posting (eligible first, highest score first)."""
    scored = []
    for cand in candidates:
        evaluation = match_candidate_to_job(cand, job)
        scored.append({
            **cand,
            "evaluation": evaluation,
            "match_score": evaluation["match_percentage"],
            "is_eligible": evaluation["is_eligible"]
        })

    # Sort primarily by eligibility, then by match_score descending
    scored.sort(key=lambda x: (x["is_eligible"], x["match_score"]), reverse=True)
    return scored


def rank_jobs_for_candidate(candidate: dict, jobs: list[dict]) -> list[dict]:
    """Ranks all available jobs for a candidate's profile."""
    scored = []
    for job in jobs:
        evaluation = match_candidate_to_job(candidate, job)
        scored.append({
            **job,
            "evaluation": evaluation,
            "match_score": evaluation["match_percentage"],
            "is_eligible": evaluation["is_eligible"]
        })

    scored.sort(key=lambda x: (x["is_eligible"], x["match_score"]), reverse=True)
    return scored


# ── Self-Test / Verification ──────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("RozgarLink / VORTEXA 3.0 — AI Matching Engine Self-Test")
    print("=" * 60)

    sample_job = {
        "id": 101,
        "title": "Python & React Full Stack Developer",
        "description": "Looking for a full stack engineer proficient in Python Flask backends and modern React user interfaces. Experience with SQL databases required.",
        "skills_required": "Python, Flask, React, SQL, Docker",
        "min_graduation_year": 2022
    }

    sample_candidate = {
        "id": 1,
        "full_name": "Aarav Sharma",
        "education": "B.Tech Computer Science",
        "graduation_year": 2024,
        "skills": "Python, Flask, JavaScript, SQLite, HTML, CSS",
        "bio": "Enthusiastic developer who has built backend REST APIs using Flask and worked on frontend web pages."
    }

    result = match_candidate_to_job(sample_candidate, sample_job)

    print(f"Candidate    : {sample_candidate['full_name']}")
    print(f"Job          : {sample_job['title']}")
    print(f"Eligible     : {result['is_eligible']}")
    print(f"Match Score  : {result['match_percentage']}% ({result['match_tier']})")
    print(f"Matched      : {result['matched_skills']}")
    print(f"Missing      : {result['missing_skills']}")
    print(f"\nExplanation  :\n{result['explanation']}")
    print(f"\nLearning Recommendations ({len(result['learning_recommendations'])}):")
    for rec in result["learning_recommendations"]:
        print(f"  * [{rec['skill']}] -> {rec['topic']} ({rec['resource']})")
    print("=" * 60)
    print("[OK] Matching module self-test completed successfully.")
