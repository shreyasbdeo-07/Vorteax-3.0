from flask import Flask, render_template, jsonify, redirect, url_for, request, session
from pathlib import Path
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from pymysql.err import IntegrityError
from dotenv import load_dotenv
import os, re, secrets
from database import get_connection
from question_generator import generate_questions
from seed_assessments import seed as seed_assessment_bank

BACKEND_DIR = Path(__file__).resolve().parent
BASE_DIR = BACKEND_DIR.parent
FRONTEND_DIR = BASE_DIR / "frontend"
load_dotenv(BACKEND_DIR / ".env")
app = Flask(__name__, template_folder=str(FRONTEND_DIR / "templates"), static_folder=str(FRONTEND_DIR / "static"), static_url_path="/static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-only-change-this-secret")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

DEGREES = ["B.Tech / B.E.", "BCA", "B.Sc.", "BBA", "B.Com.", "B.A.", "M.Tech / M.E.", "MCA", "M.Sc.", "MBA", "Diploma", "Other"]
BRANCHES = ["Computer Engineering", "Artificial Intelligence & Data Science", "Artificial Intelligence", "Information Technology", "Electronics & Telecommunication", "Electrical Engineering", "Mechanical Engineering", "Civil Engineering", "Computer Science", "Data Science", "Cybersecurity", "Other"]
PUNE_COLLEGES = ["AISSMS College of Engineering", "Army Institute of Technology", "Bharati Vidyapeeth College of Engineering", "COEP Technological University", "Cummins College of Engineering for Women", "Fergusson College", "MIT Academy of Engineering", "MIT World Peace University", "Pimpri Chinchwad College of Engineering", "Pune Institute of Computer Technology (PICT)", "Sinhgad College of Engineering", "Symbiosis Institute of Technology", "Vishwakarma Institute of Information Technology (VIIT)", "Vishwakarma Institute of Technology", "Other Pune college"]

def json_error(message, code): return jsonify({"status":"error", "message":message}), code
def body():
    value=request.get_json(silent=True)
    return value if isinstance(value,dict) else None
def role_value(value):
    return {"candidate":"jobseeker","jobseeker":"jobseeker","company":"employer","employer":"employer"}.get(str(value or "").strip().lower())
def db(): return get_connection()
def require_role(role="jobseeker"):
    def deco(fn):
        from functools import wraps
        @wraps(fn)
        def wrapped(*args,**kwargs):
            if not session.get("user_id"): return json_error("Please log in.",401)
            if role and session.get("role") != role: return json_error("You are not authorized for this action.",403)
            return fn(*args,**kwargs)
        return wrapped
    return deco

def profile_complete(p):
    return bool(p and p.get("full_name") and p.get("phone") and p.get("degree") and p.get("branch") and p.get("college"))

@app.route("/")
def home(): return redirect(url_for("auth"))
@app.route("/auth")
def auth(): return render_template("auth.html")
@app.route("/api/health")
def health(): return jsonify({"status":"success","message":"Vorteax backend is running"})

@app.post("/api/auth/register")
def register():
    data=body()
    if data is None: return json_error("Invalid request data.",400)
    role=role_value(data.get("role")); email=str(data.get("email") or "").strip().lower(); password=str(data.get("password") or "")
    phone=str(data.get("phone") or "").strip(); name=str(data.get("name") or data.get("full_name") or data.get("contact_person") or "").strip()
    if role not in ("jobseeker","employer"): return json_error("Please select Candidate or Company.",400)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",email): return json_error("Please enter a valid email address.",400)
    if len(password)<8: return json_error("Password must contain at least 8 characters.",400)
    if role=="jobseeker" and not name: return json_error("Full name is required.",400)
    if role=="employer": name=str(data.get("company_name") or name or "").strip()
    conn=None
    try:
        conn=db()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email=%s LIMIT 1",(email,))
            if cur.fetchone(): return json_error("An account with this email already exists.",409)
            cur.execute("INSERT INTO users(full_name,email,password_hash,role) VALUES(%s,%s,%s,%s)",(name,email,generate_password_hash(password),role))
            uid=cur.lastrowid
            if role=="jobseeker":
                cur.execute("INSERT INTO candidate_profiles(user_id,phone) VALUES(%s,%s)",(uid,phone or None))
                cur.execute("INSERT INTO candidate_education(user_id) VALUES(%s)",(uid,))
        conn.commit()
        return jsonify({"status":"success","message":"Account created successfully. Please log in.","redirect_url":"/auth"}),201
    except IntegrityError:
        if conn: conn.rollback()
        return json_error("An account with these details already exists.",409)
    except Exception:
        if conn: conn.rollback()
        app.logger.exception("Registration failed")
        return json_error("Registration failed because of a server/database error. Check the Flask terminal.",500)
    finally:
        if conn: conn.close()

@app.post("/api/auth/login")
def login():
    data=body()
    if data is None: return json_error("Invalid request data.",400)
    email=str(data.get("email") or "").strip().lower(); password=str(data.get("password") or ""); wanted=role_value(data.get("role"))
    if not email or not password: return json_error("Email and password are required.",400)
    if wanted not in ("jobseeker","employer"): return json_error("Please select a valid account type.",400)
    conn=None
    try:
        conn=db()
        with conn.cursor() as cur:
            cur.execute("SELECT id,full_name,email,password_hash,role FROM users WHERE email=%s LIMIT 1",(email,)); user=cur.fetchone()
        if not user or not check_password_hash(user["password_hash"],password): return json_error("Invalid email or password.",401)
        if user["role"]!=wanted: return json_error("This account does not match the selected account type.",403)
        session.clear(); session["user_id"]=user["id"]; session["role"]=user["role"]; session["full_name"]=user["full_name"]; session["email"]=user["email"]
        session["candidate_id" if user["role"]=="jobseeker" else "company_id"]=user["id"]
        return jsonify({"status":"success","message":"Login successful.","redirect_url":"/candidate/dashboard" if wanted=="jobseeker" else "/company/dashboard"}),200
    except Exception:
        app.logger.exception("Login failed"); return json_error("Login failed because of a server/database error.",500)
    finally:
        if conn: conn.close()

@app.post("/api/auth/logout")
def api_logout(): session.clear(); return jsonify({"status":"success","redirect_url":"/auth"})
@app.route("/logout",methods=["GET","POST"])
def logout(): session.clear(); return redirect(url_for("auth"))

@app.route("/candidate/dashboard")
def candidate_dashboard():
    if not session.get("user_id") or session.get("role")!="jobseeker": return redirect(url_for("auth"))
    return render_template("candidate_dashboard.html")
@app.route("/company/dashboard")
def company_dashboard():
    if not session.get("user_id") or session.get("role")!="employer": return redirect(url_for("auth"))
    return render_template("company_dashboard.html")

@app.get("/api/profile-options")
@require_role()
def profile_options(): return jsonify({"degrees":DEGREES,"branches":BRANCHES,"colleges":PUNE_COLLEGES})

@app.get("/api/candidate/profile")
@require_role()
def get_profile():
    conn=None
    try:
        conn=db()
        with conn.cursor() as cur:
            cur.execute("""SELECT u.id,u.full_name,u.email,p.phone,p.experience,p.bio,e.degree,e.branch,e.college,e.graduation_year
                           FROM users u LEFT JOIN candidate_profiles p ON p.user_id=u.id
                           LEFT JOIN candidate_education e ON e.user_id=u.id WHERE u.id=%s""",(session["user_id"],)); row=cur.fetchone()
            cur.execute("SELECT s.name FROM candidate_skills cs JOIN skills s ON s.id=cs.skill_id WHERE cs.user_id=%s ORDER BY s.name",(session["user_id"],)); skills=[r["name"] for r in cur.fetchall()]
            cur.execute("SELECT COUNT(DISTINCT skill_id) total, SUM(CASE WHEN status='COMPLETED' THEN 1 ELSE 0 END) completed FROM assessment_attempts WHERE user_id=%s",(session["user_id"],)); a=cur.fetchone()
            cur.execute("SELECT COUNT(*) n FROM candidate_skills WHERE user_id=%s",(session["user_id"],)); selected=cur.fetchone()["n"]
            cur.execute("SELECT COUNT(DISTINCT skill_id) n FROM assessment_attempts WHERE user_id=%s AND status='COMPLETED'",(session["user_id"],)); completed=cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) n FROM candidate_skills WHERE user_id=%s",(session["user_id"],)); skill_count=cur.fetchone()["n"]
            cur.execute("SELECT COUNT(DISTINCT cs.skill_id) n FROM candidate_skills cs WHERE cs.user_id=%s AND EXISTS (SELECT 1 FROM assessment_attempts aa WHERE aa.user_id=cs.user_id AND aa.skill_id=cs.skill_id AND aa.status='COMPLETED')",(session["user_id"],)); verified=cur.fetchone()["n"]
        row=row or {}; row["skills"]=skills; row["profile_complete"]=profile_complete(row); row["passport_verified"]=bool(skill_count and verified==skill_count)
        return jsonify(row)
    except Exception:
        app.logger.exception("Profile load failed"); return json_error("Could not load profile. Check database schema.",500)
    finally:
        if conn: conn.close()

@app.put("/api/candidate/profile")
@require_role()
def save_profile():
    data=body()
    if data is None: return json_error("Invalid request data.",400)
    name=str(data.get("full_name") or "").strip(); phone=str(data.get("phone") or "").strip(); email=str(data.get("email") or "").strip().lower()
    degree=str(data.get("degree") or "").strip(); branch=str(data.get("branch") or "").strip(); college=str(data.get("college") or "").strip()
    experience=str(data.get("experience") or "").strip(); bio=str(data.get("bio") or "").strip(); year=data.get("graduation_year")
    skills=data.get("skills",[])
    if not name: return json_error("Full name is required.",400)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",email): return json_error("Enter a valid email address.",400)
    if phone and not re.fullmatch(r"[0-9+()\-\s]{7,20}",phone): return json_error("Enter a valid phone number.",400)
    if degree not in DEGREES: return json_error("Choose a degree from the list.",400)
    if branch not in BRANCHES: return json_error("Choose a branch from the list.",400)
    if college not in PUNE_COLLEGES: return json_error("Choose a college from the list.",400)
    if not isinstance(skills,list) or len(skills)>50: return json_error("Skills must be a list of up to 50 items.",400)
    try: year=int(year) if year not in (None,"") else None
    except (TypeError,ValueError): return json_error("Graduation year must be a number.",400)
    if year and not 2020<=year<=2100: return json_error("Graduation year is outside the allowed range.",400)
    skills=list(dict.fromkeys(str(s).strip() for s in skills if str(s).strip()))
    conn=None
    try:
        conn=db()
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET full_name=%s,email=%s WHERE id=%s",(name,email,session["user_id"]))
            
            # Upsert candidate_profiles
            cur.execute("SELECT user_id FROM candidate_profiles WHERE user_id=%s",(session["user_id"],))
            if cur.fetchone():
                cur.execute("UPDATE candidate_profiles SET phone=%s,experience=%s,bio=%s WHERE user_id=%s",(phone,experience,bio,session["user_id"]))
            else:
                cur.execute("INSERT INTO candidate_profiles(user_id,phone,experience,bio) VALUES(%s,%s,%s,%s)",(session["user_id"],phone,experience,bio))

            # Upsert candidate_education
            cur.execute("SELECT user_id FROM candidate_education WHERE user_id=%s",(session["user_id"],))
            if cur.fetchone():
                cur.execute("UPDATE candidate_education SET degree=%s,branch=%s,college=%s,graduation_year=%s WHERE user_id=%s",(degree,branch,college,year,session["user_id"]))
            else:
                cur.execute("INSERT INTO candidate_education(user_id,degree,branch,college,graduation_year) VALUES(%s,%s,%s,%s,%s)",(session["user_id"],degree,branch,college,year))

            # Update candidate_skills
            cur.execute("DELETE FROM candidate_skills WHERE user_id=%s",(session["user_id"],))
            for skill in skills:
                cur.execute("SELECT id FROM skills WHERE name=%s",(skill,))
                srow=cur.fetchone()
                if srow:
                    sid=srow["id"]
                else:
                    cur.execute("INSERT INTO skills(name) VALUES(%s)",(skill,))
                    sid=cur.lastrowid
                cur.execute("INSERT INTO candidate_skills(user_id,skill_id) VALUES(%s,%s)",(session["user_id"],sid))
        conn.commit(); session["full_name"]=name; session["email"]=email
        return jsonify({"status":"success","message":"Profile saved.","profile_complete":True})
    except IntegrityError:
        if conn: conn.rollback()
        return json_error("That email address is already registered to another account.",409)
    except Exception:
        if conn: conn.rollback()
        app.logger.exception("Profile save failed"); return json_error("Could not save profile. Check database schema.",500)
    finally:
        if conn: conn.close()

@app.get("/api/skills")
@require_role()
def list_skills():
    conn=None
    try:
        conn=db()
        with conn.cursor() as cur: cur.execute("SELECT id,name FROM skills ORDER BY name"); rows=cur.fetchall()
        return jsonify(rows)
    except Exception: app.logger.exception("Skills load failed"); return json_error("Could not load skills.",500)
    finally:
        if conn: conn.close()

@app.get("/assessments")
@require_role()
def assessments_page(): return render_template("assessments.html")

@app.get("/api/assessments/available")
@require_role()
def available_assessments():
    conn=None
    try:
        conn=db()
        with conn.cursor() as cur:
            cur.execute("""SELECT s.id skill_id,s.name, COUNT(q.id) question_count,
              (SELECT a.status FROM assessment_attempts a WHERE a.user_id=%s AND a.skill_id=s.id ORDER BY a.id DESC LIMIT 1) last_status,
              (SELECT a.percentage FROM assessment_attempts a WHERE a.user_id=%s AND a.skill_id=s.id AND a.status='COMPLETED' ORDER BY a.id DESC LIMIT 1) best_percentage
              FROM candidate_skills cs JOIN skills s ON s.id=cs.skill_id LEFT JOIN assessment_questions q ON q.skill_id=s.id AND q.active=1
              WHERE cs.user_id=%s GROUP BY s.id,s.name ORDER BY s.name""",(session["user_id"],session["user_id"],session["user_id"])); rows=cur.fetchall()
        return jsonify(rows)
    except Exception: app.logger.exception("Assessment list failed"); return json_error("Could not load assessments.",500)
    finally:
        if conn: conn.close()

@app.post("/api/assessments/start")
@require_role()
def start_assessment():
    data=body() or {}; skill_id=data.get("skill_id")
    try: skill_id=int(skill_id)
    except (TypeError,ValueError): return json_error("Select a valid skill.",400)
    conn=None
    try:
        seed_assessment_bank()
        conn=db()
        with conn.cursor() as cur:
            cur.execute("SELECT s.id,s.name FROM candidate_skills cs JOIN skills s ON s.id=cs.skill_id WHERE cs.user_id=%s AND s.id=%s",(session["user_id"],skill_id))
            skill=cur.fetchone()
            if not skill: return json_error("You can only assess a skill selected in your profile.",403)
            questions=[]
            for level,need in [('EASY',3),('MEDIUM',4),('HARD',3)]:
                cur.execute("SELECT id,question_text,option_a,option_b,option_c,option_d,marks,difficulty FROM assessment_questions WHERE skill_id=%s AND active=1 AND difficulty=%s ORDER BY RAND() LIMIT %s",(skill_id,level,need))
                questions.extend(cur.fetchall())
            if len(questions)!=10:
                cur.execute("SELECT id,question_text,option_a,option_b,option_c,option_d,marks,difficulty FROM assessment_questions WHERE skill_id=%s AND active=1 ORDER BY RAND() LIMIT 10",(skill_id,))
                questions=cur.fetchall()
            if len(questions)<10:
                return json_error("This skill does not have a complete 30-question bank. Run `python seed_assessments.py`.",409)
            for q in questions:
                diff = str(q.get('difficulty') or 'MEDIUM').strip().upper()
                q['marks'] = {'EASY': 3, 'MEDIUM': 5, 'HARD': 7}.get(diff, 5)
            cur.execute("INSERT INTO assessment_attempts(user_id,skill_id,status,started_at,time_limit_seconds,total_marks) VALUES(%s,%s,'IN_PROGRESS',NOW(),900,50)",(session["user_id"],skill_id))
            attempt_id=cur.lastrowid
            for i,q in enumerate(questions,1):
                cur.execute("INSERT INTO assessment_attempt_questions(attempt_id,question_id,question_number,marks) VALUES(%s,%s,%s,%s)",(attempt_id,q['id'],i,q['marks']))
        conn.commit()
        return jsonify({
            "attempt_id": attempt_id,
            "skill": skill["name"],
            "time_limit_seconds": 900,
            "total_marks": 50,
            "questions": [{
                "id": q['id'],
                "number": i+1,
                "difficulty": str(q.get('difficulty') or 'medium').lower(),
                "marks": q['marks'],
                "text": q['question_text'],
                "options": {"A": q['option_a'], "B": q['option_b'], "C": q['option_c'], "D": q['option_d']}
            } for i,q in enumerate(questions)]
        }), 201
    except Exception:
        if conn: conn.rollback()
        app.logger.exception("Assessment start failed"); return json_error("Could not start assessment.",500)
    finally:
        if conn: conn.close()

@app.post("/api/assessments/<int:attempt_id>/proctor-event")
@require_role()
def assessment_proctor_event(attempt_id):
    data=body() or {}; event=str(data.get('event_type') or '').strip().upper(); details=str(data.get('details') or '')[:255]
    allowed={'TAB_SWITCH','FULLSCREEN_EXIT','MULTIPLE_FACES','MOBILE_DETECTED','CAMERA_UNAVAILABLE','CAMERA_PERMISSION_DENIED'}
    if event not in allowed: return json_error('Invalid proctor event.',400)
    conn=None
    try:
        conn=db()
        with conn.cursor() as cur:
            cur.execute('SELECT id,status FROM assessment_attempts WHERE id=%s AND user_id=%s',(attempt_id,session['user_id']))
            attempt=cur.fetchone()
            if not attempt: return json_error('Assessment attempt not found.',404)
            if attempt['status']!='IN_PROGRESS': return json_error('Attempt is not active.',409)
            cur.execute('INSERT INTO assessment_proctor_events(attempt_id,user_id,event_type,details) VALUES(%s,%s,%s,%s)',(attempt_id,session['user_id'],event,details))
            cur.execute("SELECT COUNT(*) AS n FROM assessment_proctor_events WHERE attempt_id=%s AND event_type IN ('TAB_SWITCH','FULLSCREEN_EXIT','MULTIPLE_FACES','MOBILE_DETECTED')",(attempt_id,))
            violations=int(cur.fetchone()['n'])
        conn.commit()
        return jsonify({'recorded':True,'violations':violations,'terminate':violations>=3})
    except Exception:
        if conn: conn.rollback()
        app.logger.exception('Proctor event logging failed'); return json_error('Could not record proctor event.',500)
    finally:
        if conn: conn.close()

@app.post("/api/assessments/<int:attempt_id>/submit")
@require_role()
def submit_assessment(attempt_id):
    data=body() or {}; answers=data.get("answers",{})
    if not isinstance(answers,dict): return json_error("Answers must be an object.",400)
    conn=None
    try:
        conn=db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM assessment_attempts WHERE id=%s AND user_id=%s",(attempt_id,session["user_id"]))
            attempt=cur.fetchone()
            if not attempt: return json_error("Assessment attempt not found.",404)
            if attempt["status"]!="IN_PROGRESS": return json_error("This assessment has already been submitted or closed.",409)
            cur.execute("SELECT aq.question_id,aq.marks,q.correct_option FROM assessment_attempt_questions aq JOIN assessment_questions q ON q.id=aq.question_id WHERE aq.attempt_id=%s",(attempt_id,)); qs=cur.fetchall()
            total=sum(int(q["marks"]) for q in qs); score=0; correct=0
            for q in qs:
                chosen=str(answers.get(str(q["question_id"]),"")).upper()
                if chosen not in ("A","B","C","D"): chosen=""
                ok=chosen==q["correct_option"]
                if ok: score+=int(q["marks"]); correct+=1
                cur.execute("DELETE FROM assessment_answers WHERE attempt_id=%s AND question_id=%s",(attempt_id,q["question_id"]))
                cur.execute("INSERT INTO assessment_answers(attempt_id,question_id,selected_answer,is_correct,marks_awarded) VALUES(%s,%s,%s,%s,%s)",(attempt_id,q["question_id"],chosen or None,int(ok),int(q["marks"]) if ok else 0))
            
            started = attempt.get("started_at")
            started_ts = 0
            if isinstance(started, str):
                from datetime import datetime, timezone
                try:
                    dt = datetime.fromisoformat(started.replace(" ", "T"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    started_ts = dt.timestamp()
                except Exception:
                    started_ts = 0
            elif hasattr(started, "timestamp"):
                started_ts = started.timestamp()

            import time
            expired = bool(started_ts and (started_ts + int(attempt.get("time_limit_seconds") or 900)) < time.time())
            requested_reason=str(data.get("reason") or "MANUAL").upper()
            proctor_violations=False
            if requested_reason == "PROCTOR_VIOLATION":
                cur.execute("SELECT COUNT(*) AS n FROM assessment_proctor_events WHERE attempt_id=%s AND event_type IN ('TAB_SWITCH','FULLSCREEN_EXIT','MULTIPLE_FACES','MOBILE_DETECTED')",(attempt_id,))
                proctor_violations=int(cur.fetchone()["n"]) >= 3
            pct=round(score*100/total,2) if total else 0
            terminated=expired or proctor_violations
            status="TERMINATED" if terminated else "COMPLETED"
            finish_reason="TIME_EXPIRED" if expired else ("PROCTOR_VIOLATION" if proctor_violations else "MANUAL")
            cur.execute("UPDATE assessment_attempts SET status=%s,score=%s,percentage=%s,submitted_at=DATETIME('now'),finish_reason=%s WHERE id=%s",(status,score,pct,finish_reason,attempt_id))
            cur.execute("INSERT INTO assessment_results(attempt_id,user_id,skill_id,score,total_marks,percentage,correct_count,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(attempt_id,session["user_id"],attempt["skill_id"],score,total,pct,correct,status))
        conn.commit()
        return jsonify({"status":status,"score":score,"total_marks":total,"percentage":pct,"correct_count":correct,"message":("Assessment terminated after repeated proctoring violations." if status=="TERMINATED" and finish_reason=="PROCTOR_VIOLATION" else ("Time limit exceeded; attempt terminated." if expired else "Assessment submitted. Results are calculated on the server."))})
    except Exception:
        if conn: conn.rollback()
        app.logger.exception("Assessment submission failed"); return json_error("Could not submit assessment.",500)
    finally:
        if conn: conn.close()

@app.get("/api/skill-passport")
@require_role()
def skill_passport():
    conn=None
    try:
        conn=db()
        with conn.cursor() as cur:
            cur.execute("""SELECT s.id skill_id,s.name,
                           (SELECT MAX(r.percentage) FROM assessment_results r WHERE r.user_id=cs.user_id AND r.skill_id=cs.skill_id AND r.status='COMPLETED') best_percentage,
                           (SELECT COUNT(*) FROM assessment_results r WHERE r.user_id=cs.user_id AND r.skill_id=cs.skill_id) attempts,
                           (SELECT a.status FROM assessment_attempts a WHERE a.user_id=cs.user_id AND a.skill_id=cs.skill_id ORDER BY a.id DESC LIMIT 1) latest_status
                           FROM candidate_skills cs JOIN skills s ON s.id=cs.skill_id
                           WHERE cs.user_id=%s ORDER BY s.name""", (session["user_id"],))
            rows=cur.fetchall()
            total=len(rows)
            done=sum(1 for row in rows if row.get("latest_status")=="COMPLETED")
            code=None
            if total>0 and done>=total:
                cur.execute("SELECT passport_code,generated_at FROM skill_passports WHERE user_id=%s",(session["user_id"],))
                existing=cur.fetchone()
                if not existing:
                    code="VX-"+secrets.token_hex(6).upper()
                    cur.execute("INSERT INTO skill_passports(user_id,passport_code) VALUES(%s,%s)",(session["user_id"],code))
                    conn.commit()
                else:
                    code=existing["passport_code"]
        return jsonify({"skills":rows,"total_skills":total,"completed_skills":done,"issued":bool(total>0 and done>=total),"passport_code":code})
    except Exception:
        app.logger.exception("Passport failed"); return json_error("Could not load Skill Passport.",500)
    finally:
        if conn: conn.close()

# ── Jobs & Applications Endpoints ─────────────────────────────────────

@app.get("/api/jobs")
def get_jobs():
    search = str(request.args.get("search") or "").strip()
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            query = """
                SELECT j.id, j.title, j.description, j.skills_required, j.location, j.salary_range,
                       u.full_name AS company_name
                FROM jobs j
                JOIN users u ON j.employer_id = u.id
                WHERE j.is_active = 1
            """
            params = []
            if search:
                pattern = f"%{search}%"
                query += " AND (j.title LIKE %s OR j.skills_required LIKE %s OR u.full_name LIKE %s)"
                params = [pattern, pattern, pattern]
            query += " ORDER BY j.created_at DESC"
            cur.execute(query, params)
            jobs = cur.fetchall()
            return jsonify(jobs or [])
    except Exception:
        app.logger.exception("Jobs load failed")
        return jsonify([])
    finally:
        if conn: conn.close()


@app.get("/api/jobs/recommendations")
def get_recommendations():
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT j.id, j.title, j.description, j.skills_required, j.location, j.salary_range,
                       u.full_name AS company_name
                FROM jobs j
                JOIN users u ON j.employer_id = u.id
                WHERE j.is_active = 1
            """)
            jobs = cur.fetchall() or []

            # Retrieve candidate profile with education and practical projects
            user_id = session.get("user_id")
            cand_profile = {"id": user_id, "skills": [], "bio": "", "projects": []}
            if user_id:
                cur.execute("""
                    SELECT u.full_name, p.bio, p.experience, e.degree, e.graduation_year,
                           GROUP_CONCAT(s.name) AS skills_str
                    FROM users u
                    LEFT JOIN candidate_profiles p ON p.user_id = u.id
                    LEFT JOIN candidate_education e ON e.user_id = u.id
                    LEFT JOIN candidate_skills cs ON cs.user_id = u.id
                    LEFT JOIN skills s ON s.id = cs.skill_id
                    WHERE u.id = %s
                    GROUP BY u.id
                """, (user_id,))
                row = cur.fetchone()
                if row:
                    cand_profile["full_name"] = row.get("full_name") or ""
                    cand_profile["bio"] = row.get("bio") or ""
                    cand_profile["experience"] = row.get("experience") or ""
                    cand_profile["degree"] = row.get("degree") or ""
                    cand_profile["graduation_year"] = row.get("graduation_year")
                    cand_profile["skills"] = [s.strip() for s in (row.get("skills_str") or "").split(",") if s.strip()]

                # Fetch candidate projects for practical experience evaluation
                cur.execute("""
                    SELECT id, title, description, tech_stack, live_url, github_url
                    FROM candidate_projects
                    WHERE user_id = %s
                    ORDER BY id DESC
                """, (user_id,))
                cand_profile["projects"] = cur.fetchall() or []

        # Run AI matching if matching.py is present
        try:
            from matching import rank_jobs_for_candidate
            ranked = rank_jobs_for_candidate(cand_profile, jobs)
            return jsonify(ranked)
        except Exception as e:
            app.logger.warning(f"AI matching fallback: {e}")
            for j in jobs:
                j["match_score"] = 75
            return jsonify(jobs)
    except Exception:
        app.logger.exception("Recommendations failed")
        return jsonify([])
    finally:
        if conn: conn.close()


@app.post("/api/matching/what-if")
def what_if_simulation():
    data = body() or {}
    simulated_skills = data.get("simulated_skills") or []
    if not isinstance(simulated_skills, list):
        return json_error("simulated_skills must be a list of skill names.", 400)

    user_id = session.get("user_id")
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT j.id, j.title, j.description, j.skills_required, j.location, j.salary_range,
                       u.full_name AS company_name
                FROM jobs j
                JOIN users u ON j.employer_id = u.id
                WHERE j.is_active = 1
            """)
            jobs = cur.fetchall() or []

            cand_profile = {"id": user_id, "skills": [], "bio": "", "projects": []}
            if user_id:
                cur.execute("""
                    SELECT u.full_name, p.bio, p.experience, e.degree, e.graduation_year,
                           GROUP_CONCAT(s.name) AS skills_str
                    FROM users u
                    LEFT JOIN candidate_profiles p ON p.user_id = u.id
                    LEFT JOIN candidate_education e ON e.user_id = u.id
                    LEFT JOIN candidate_skills cs ON cs.user_id = u.id
                    LEFT JOIN skills s ON s.id = cs.skill_id
                    WHERE u.id = %s
                    GROUP BY u.id
                """, (user_id,))
                row = cur.fetchone()
                if row:
                    cand_profile["full_name"] = row.get("full_name") or ""
                    cand_profile["bio"] = row.get("bio") or ""
                    cand_profile["experience"] = row.get("experience") or ""
                    cand_profile["degree"] = row.get("degree") or ""
                    cand_profile["graduation_year"] = row.get("graduation_year")
                    cand_profile["skills"] = [s.strip() for s in (row.get("skills_str") or "").split(",") if s.strip()]

                cur.execute("""
                    SELECT id, title, description, tech_stack, live_url, github_url
                    FROM candidate_projects
                    WHERE user_id = %s
                """, (user_id,))
                cand_profile["projects"] = cur.fetchall() or []

        from matching import simulate_what_if_match
        simulation = simulate_what_if_match(cand_profile, jobs, simulated_skills)
        return jsonify(simulation)
    except Exception:
        app.logger.exception("What-if simulation failed")
        return json_error("Failed to run what-if simulation.", 500)
    finally:
        if conn: conn.close()


@app.get("/api/candidate/projects")
@require_role()
def get_candidate_projects():
    user_id = session.get("user_id")
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, description, tech_stack, live_url, github_url, created_at
                FROM candidate_projects
                WHERE user_id = %s
                ORDER BY id DESC
            """, (user_id,))
            return jsonify(cur.fetchall() or [])
    except Exception:
        app.logger.exception("Failed to load candidate projects")
        return jsonify([])
    finally:
        if conn: conn.close()


@app.post("/api/candidate/projects")
@require_role()
def add_candidate_project():
    data = body() or {}
    title = str(data.get("title") or "").strip()
    description = str(data.get("description") or "").strip()
    tech_stack = str(data.get("tech_stack") or "").strip()
    live_url = str(data.get("live_url") or "").strip()
    github_url = str(data.get("github_url") or "").strip()

    if not title:
        return json_error("Project title is required.", 400)

    user_id = session.get("user_id")
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO candidate_projects (user_id, title, description, tech_stack, live_url, github_url)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, title, description, tech_stack, live_url, github_url))
        conn.commit()
        return jsonify({"status": "success", "message": "Project added successfully!"}), 201
    except Exception:
        if conn: conn.rollback()
        app.logger.exception("Failed to add candidate project")
        return json_error("Failed to save project.", 500)
    finally:
        if conn: conn.close()


@app.delete("/api/candidate/projects/<int:project_id>")
@require_role()
def delete_candidate_project(project_id):
    user_id = session.get("user_id")
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM candidate_projects WHERE id = %s AND user_id = %s", (project_id, user_id))
        conn.commit()
        return jsonify({"status": "success", "message": "Project removed."})
    except Exception:
        if conn: conn.rollback()
        app.logger.exception("Failed to delete candidate project")
        return json_error("Failed to delete project.", 500)
    finally:
        if conn: conn.close()


@app.get("/api/my-applications")
def get_my_applications():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify([])
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id, a.job_id, a.status, a.applied_at,
                       j.title AS job_title, u.full_name AS company_name
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                JOIN users u ON j.employer_id = u.id
                WHERE a.applicant_id = %s
                ORDER BY a.applied_at DESC
            """, (user_id,))
            apps = cur.fetchall() or []
            return jsonify(apps)
    except Exception:
        app.logger.exception("Applications load failed")
        return jsonify([])
    finally:
        if conn: conn.close()


@app.post("/api/applications")
def apply_to_job():
    user_id = session.get("user_id")
    if not user_id:
        return json_error("Please log in to apply.", 401)
    data = body() or {}
    job_id = data.get("job_id")
    if not job_id:
        return json_error("job_id is required.", 400)
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO applications (job_id, applicant_id, status)
                VALUES (%s, %s, 'pending')
            """, (job_id, user_id))
        conn.commit()
        return jsonify({"status": "success", "message": "Application submitted successfully!"})
    except Exception as e:
        if conn: conn.rollback()
        # If already applied (unique constraint)
        return jsonify({"status": "success", "message": "Already applied for this job."})
    finally:
        if conn: conn.close()


# ── Employer / Company Job Management & Applicant Endpoints ──────────

@app.post("/api/jobs")
def create_job():
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id or role != "employer":
        return json_error("Only logged in companies can post jobs.", 403)
    data = body() or {}
    title = str(data.get("title") or "").strip()
    if not title:
        return json_error("Job title is required.", 400)
    description = str(data.get("description") or "").strip()
    skills = str(data.get("skills_required") or data.get("skills") or "").strip()
    location = str(data.get("location") or "Remote").strip()
    salary = str(data.get("salary_range") or data.get("salary") or "Competitive").strip()
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jobs (employer_id, title, description, skills_required, location, salary_range, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """, (user_id, title, description, skills, location, salary))
            job_id = cur.lastrowid
        conn.commit()
        return jsonify({
            "status": "success",
            "message": "Job posted successfully!",
            "job": {
                "id": job_id,
                "title": title,
                "description": description,
                "skills_required": skills,
                "location": location,
                "salary_range": salary
            }
        }), 201
    except Exception:
        if conn: conn.rollback()
        app.logger.exception("Job creation failed")
        return json_error("Could not post job.", 500)
    finally:
        if conn: conn.close()


@app.get("/api/company/jobs")
def get_company_jobs():
    user_id = session.get("user_id")
    if not user_id or session.get("role") != "employer":
        return json_error("Unauthorized.", 401)
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT j.id, j.title, j.description, j.skills_required, j.location, j.salary_range,
                       j.is_active, j.created_at,
                       COUNT(a.id) AS applicants_count
                FROM jobs j
                LEFT JOIN applications a ON a.job_id = j.id
                WHERE j.employer_id = %s
                GROUP BY j.id
                ORDER BY j.created_at DESC
            """, (user_id,))
            jobs = cur.fetchall() or []
            return jsonify(jobs)
    except Exception:
        app.logger.exception("Company jobs load failed")
        return jsonify([])
    finally:
        if conn: conn.close()


@app.post("/api/company/jobs/<int:job_id>/toggle")
def toggle_company_job(job_id):
    user_id = session.get("user_id")
    if not user_id or session.get("role") != "employer":
        return json_error("Unauthorized.", 401)
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("SELECT id, is_active FROM jobs WHERE id = %s AND employer_id = %s", (job_id, user_id))
            job = cur.fetchone()
            if not job:
                return json_error("Job not found.", 404)
            new_state = 0 if job["is_active"] else 1
            cur.execute("UPDATE jobs SET is_active = %s WHERE id = %s", (new_state, job_id))
        conn.commit()
        return jsonify({"status": "success", "is_active": new_state})
    except Exception:
        if conn: conn.rollback()
        return json_error("Could not update job status.", 500)
    finally:
        if conn: conn.close()


@app.get("/api/company/applicants")
def get_company_applicants():
    user_id = session.get("user_id")
    if not user_id or session.get("role") != "employer":
        return json_error("Unauthorized.", 401)
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id AS application_id, a.job_id, a.applicant_id, a.status, a.applied_at,
                       j.title AS job_title,
                       u.full_name AS candidate_name, u.email AS candidate_email,
                       p.phone, p.experience, e.degree, e.branch, e.college,
                       GROUP_CONCAT(s.name) AS skills_str
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                JOIN users u ON a.applicant_id = u.id
                LEFT JOIN candidate_profiles p ON p.user_id = u.id
                LEFT JOIN candidate_education e ON e.user_id = u.id
                LEFT JOIN candidate_skills cs ON cs.user_id = u.id
                LEFT JOIN skills s ON s.id = cs.skill_id
                WHERE j.employer_id = %s
                GROUP BY a.id
                ORDER BY a.applied_at DESC
            """, (user_id,))
            applicants = cur.fetchall() or []
            try:
                from matching import calculate_hybrid_match
                for app_row in applicants:
                    cand_profile = {
                        "skills": [s.strip() for s in (app_row.get("skills_str") or "").split(",") if s.strip()],
                        "experience": app_row.get("experience") or "",
                        "degree": app_row.get("degree") or "",
                        "projects": []
                    }
                    cur.execute("SELECT skills_required FROM jobs WHERE id = %s", (app_row["job_id"],))
                    j_row = cur.fetchone()
                    job_dict = {
                        "title": app_row.get("job_title") or "",
                        "skills_required": j_row.get("skills_required") if j_row else ""
                    }
                    match_res = calculate_hybrid_match(cand_profile, job_dict)
                    app_row["match_score"] = match_res.get("match_score", 70)
            except Exception:
                for app_row in applicants:
                    app_row["match_score"] = 75
            return jsonify(applicants)
    except Exception:
        app.logger.exception("Company applicants load failed")
        return jsonify([])
    finally:
        if conn: conn.close()


@app.post("/api/company/applications/<int:app_id>/status")
def update_application_status(app_id):
    user_id = session.get("user_id")
    if not user_id or session.get("role") != "employer":
        return json_error("Unauthorized.", 401)
    data = body() or {}
    new_status = str(data.get("status") or "").strip().lower()
    status_map = {
        "applied": "pending",
        "pending": "pending",
        "review": "reviewed",
        "reviewed": "reviewed",
        "shortlisted": "accepted",
        "accepted": "accepted",
        "interview": "accepted",
        "rejected": "rejected"
    }
    mapped = status_map.get(new_status, "pending")
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id FROM applications a
                JOIN jobs j ON a.job_id = j.id
                WHERE a.id = %s AND j.employer_id = %s
            """, (app_id, user_id))
            if not cur.fetchone():
                return json_error("Application not found or unauthorized.", 404)
            cur.execute("UPDATE applications SET status = %s WHERE id = %s", (mapped, app_id))
        conn.commit()
        return jsonify({"status": "success", "message": f"Status updated to {mapped}."})
    except Exception:
        if conn: conn.rollback()
        return json_error("Could not update status.", 500)
    finally:
        if conn: conn.close()


if __name__=="__main__": app.run(host="127.0.0.1",port=5000,debug=os.getenv("FLASK_DEBUG","0")=="1")

