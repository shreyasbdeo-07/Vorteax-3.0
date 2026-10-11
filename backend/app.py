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

def passport_is_issued(user_id):
    """Authoritative server-side gate: passport exists and every selected skill's latest attempt completed."""
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""SELECT u.full_name,p.phone,e.degree,e.branch,e.college
                           FROM users u LEFT JOIN candidate_profiles p ON p.user_id=u.id
                           LEFT JOIN candidate_education e ON e.user_id=u.id WHERE u.id=%s""", (user_id,))
            profile = cur.fetchone()
            if not profile_complete(profile):
                return False
            cur.execute("SELECT COUNT(*) AS n FROM candidate_skills WHERE user_id=%s", (user_id,))
            total = int(cur.fetchone()["n"])
            if total < 1:
                return False
            cur.execute("""SELECT COUNT(*) AS n FROM candidate_skills cs
                           WHERE cs.user_id=%s AND EXISTS (
                             SELECT 1 FROM assessment_attempts a
                             WHERE a.user_id=cs.user_id AND a.skill_id=cs.skill_id
                               AND a.id=(SELECT MAX(a2.id) FROM assessment_attempts a2
                                         WHERE a2.user_id=cs.user_id AND a2.skill_id=cs.skill_id)
                               AND a.status='COMPLETED')""", (user_id,))
            completed = int(cur.fetchone()["n"])
            cur.execute("SELECT COUNT(*) AS n FROM skill_passports WHERE user_id=%s", (user_id,))
            issued = int(cur.fetchone()["n"]) > 0
            return issued and completed == total
    except Exception:
        app.logger.exception("Passport access check failed")
        return False
    finally:
        if conn:
            conn.close()

def require_verified_passport(fn):
    @wraps(fn)
    @require_role()
    def wrapped(*args, **kwargs):
        if not passport_is_issued(session["user_id"]):
            return json_error("Complete your profile and all selected skill assessments to unlock this feature.", 423)
        return fn(*args, **kwargs)
    return wrapped

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
    if not phone: return json_error("Phone number is required to verify your Skill Passport.",400)
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
            cur.execute("INSERT INTO candidate_profiles(user_id,phone,experience,bio) VALUES(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE phone=VALUES(phone),experience=VALUES(experience),bio=VALUES(bio)",(session["user_id"],phone,experience,bio))
            cur.execute("INSERT INTO candidate_education(user_id,degree,branch,college,graduation_year) VALUES(%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE degree=VALUES(degree),branch=VALUES(branch),college=VALUES(college),graduation_year=VALUES(graduation_year)",(session["user_id"],degree,branch,college,year))
            cur.execute("SELECT s.name FROM candidate_skills cs JOIN skills s ON s.id=cs.skill_id WHERE cs.user_id=%s ORDER BY s.name", (session["user_id"],))
            old_skills = [r["name"] for r in cur.fetchall()]
            if sorted(old_skills, key=str.lower) != sorted(skills, key=str.lower):
                cur.execute("DELETE FROM skill_passports WHERE user_id=%s", (session["user_id"],))
            cur.execute("DELETE FROM candidate_skills WHERE user_id=%s",(session["user_id"],))
            for skill in skills:
                cur.execute("INSERT INTO skills(name) VALUES(%s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)",(skill,)); sid=cur.lastrowid
                cur.execute("INSERT INTO candidate_skills(user_id,skill_id) VALUES(%s,%s)",(session["user_id"],sid))
        conn.commit(); session["full_name"]=name; session["email"]=email
        return jsonify({"status":"success","message":"Profile saved.","profile_complete":True,"redirect_url":"/assessments"})
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
        # Ensure the local static question bank exists before opening the attempt transaction.
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
            if len(questions)!=10: return json_error("This skill does not have a complete 30-question bank. Run `python seed_assessments.py` after database migration.",409)
            for q in questions:
                # MySQL ENUM values may be returned in the table's stored case (e.g. 'easy').
                # Normalize before assigning the assessment's fixed marks.
                difficulty = str(q['difficulty']).strip().upper()
                q['marks'] = {'EASY': 3, 'MEDIUM': 5, 'HARD': 7}[difficulty]
            cur.execute("INSERT INTO assessment_attempts(user_id,skill_id,status,started_at,time_limit_seconds,total_marks) VALUES(%s,%s,'IN_PROGRESS',NOW(),900,50)",(session["user_id"],skill_id))
            attempt_id=cur.lastrowid
            for i,q in enumerate(questions,1): cur.execute("INSERT INTO assessment_attempt_questions(attempt_id,question_id,question_number,marks) VALUES(%s,%s,%s,%s)",(attempt_id,q['id'],i,q['marks']))
        conn.commit()
        return jsonify({"attempt_id":attempt_id,"skill":skill["name"],"time_limit_seconds":900,"total_marks":50,"questions":[{"id":q['id'],"number":i+1,"difficulty":q['difficulty'].lower(),"marks":q['marks'],"text":q['question_text'],"options":{"A":q['option_a'],"B":q['option_b'],"C":q['option_c'],"D":q['option_d']}} for i,q in enumerate(questions)]}),201
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
            cur.execute("SELECT * FROM assessment_attempts WHERE id=%s AND user_id=%s FOR UPDATE",(attempt_id,session["user_id"])); attempt=cur.fetchone()
            if not attempt: return json_error("Assessment attempt not found.",404)
            if attempt["status"]!="IN_PROGRESS": return json_error("This assessment has already been submitted or closed.",409)
            cur.execute("SELECT aq.question_id,aq.marks,q.correct_option FROM assessment_attempt_questions aq JOIN assessment_questions q ON q.id=aq.question_id WHERE aq.attempt_id=%s",(attempt_id,)); qs=cur.fetchall()
            total=sum(int(q["marks"]) for q in qs); score=0; correct=0
            for q in qs:
                chosen=str(answers.get(str(q["question_id"]),"")).upper()
                if chosen not in ("A","B","C","D"): chosen=""
                ok=chosen==q["correct_option"]
                if ok: score+=int(q["marks"]); correct+=1
                cur.execute("INSERT INTO assessment_answers(attempt_id,question_id,selected_answer,is_correct,marks_awarded) VALUES(%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE selected_answer=VALUES(selected_answer),is_correct=VALUES(is_correct),marks_awarded=VALUES(marks_awarded)",(attempt_id,q["question_id"],chosen or None,int(ok),int(q["marks"]) if ok else 0))
            expired=(attempt["started_at"].timestamp()+int(attempt["time_limit_seconds"])) < __import__('time').time()
            requested_reason=str(data.get("reason") or "MANUAL").upper()
            proctor_violations=False
            if requested_reason == "PROCTOR_VIOLATION":
                cur.execute("SELECT COUNT(*) AS n FROM assessment_proctor_events WHERE attempt_id=%s AND event_type IN ('TAB_SWITCH','FULLSCREEN_EXIT','MULTIPLE_FACES','MOBILE_DETECTED')",(attempt_id,))
                proctor_violations=int(cur.fetchone()["n"]) >= 3
            pct=round(score*100/total,2) if total else 0
            terminated=expired or proctor_violations
            status="TERMINATED" if terminated else "COMPLETED"
            finish_reason="TIME_EXPIRED" if expired else ("PROCTOR_VIOLATION" if proctor_violations else "MANUAL")
            cur.execute("UPDATE assessment_attempts SET status=%s,score=%s,percentage=%s,submitted_at=NOW(),finish_reason=%s WHERE id=%s",(status,score,pct,finish_reason,attempt_id))
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
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""SELECT u.full_name,p.phone,e.degree,e.branch,e.college
                           FROM users u LEFT JOIN candidate_profiles p ON p.user_id=u.id
                           LEFT JOIN candidate_education e ON e.user_id=u.id WHERE u.id=%s""", (session["user_id"],))
            profile = cur.fetchone()
            profile_ok = profile_complete(profile)
            cur.execute("""SELECT s.id skill_id,s.name,
                           (SELECT MAX(r.percentage) FROM assessment_results r WHERE r.user_id=cs.user_id AND r.skill_id=cs.skill_id AND r.status='COMPLETED') best_percentage,
                           (SELECT COUNT(*) FROM assessment_results r WHERE r.user_id=cs.user_id AND r.skill_id=cs.skill_id) attempts,
                           (SELECT a.status FROM assessment_attempts a WHERE a.user_id=cs.user_id AND a.skill_id=cs.skill_id ORDER BY a.id DESC LIMIT 1) latest_status
                           FROM candidate_skills cs JOIN skills s ON s.id=cs.skill_id
                           WHERE cs.user_id=%s ORDER BY s.name""", (session["user_id"],))
            rows = cur.fetchall()
            total = len(rows)
            done = sum(1 for row in rows if row.get("latest_status") == "COMPLETED")
            ready = profile_ok and total > 0 and done == total
            code = None
            generated_at = None
            if ready:
                cur.execute("SELECT passport_code,generated_at FROM skill_passports WHERE user_id=%s", (session["user_id"],))
                existing = cur.fetchone()
                if not existing:
                    code = "VX-" + secrets.token_hex(6).upper()
                    cur.execute("INSERT INTO skill_passports(user_id,passport_code) VALUES(%s,%s)", (session["user_id"], code))
                    conn.commit()
                    cur.execute("SELECT passport_code,generated_at FROM skill_passports WHERE user_id=%s", (session["user_id"],))
                    existing = cur.fetchone()
                code = existing["passport_code"]
                generated_at = str(existing["generated_at"]) if existing.get("generated_at") else None
            else:
                # A stale passport must never grant access after skills/profile requirements change.
                cur.execute("DELETE FROM skill_passports WHERE user_id=%s", (session["user_id"],))
                conn.commit()
        return jsonify({"skills": rows, "total_skills": total, "completed_skills": done,
                        "profile_complete": bool(profile_ok), "issued": bool(ready and code),
                        "locked": not bool(ready and code), "passport_code": code,
                        "generated_at": generated_at,
                        "lock_reason": ("Complete and save all required profile details." if not profile_ok else
                                        ("Complete every selected skill assessment." if done < total else None))})
    except Exception:
        app.logger.exception("Passport failed")
        return json_error("Could not load Skill Passport.", 500)
    finally:
        if conn:
            conn.close()

@app.get("/api/jobs")
@require_role()
def list_jobs():
    search = str(request.args.get("search") or "").strip()[:120]
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            pattern = f"%{search}%"
            cur.execute("""SELECT j.id,j.title,j.description,j.skills_required AS skills,j.location,
                           j.salary_range, u.full_name AS company_name
                           FROM jobs j JOIN users u ON u.id=j.employer_id
                           WHERE j.is_active=1 AND (%s='' OR j.title LIKE %s OR j.description LIKE %s OR j.skills_required LIKE %s OR u.full_name LIKE %s)
                           ORDER BY j.created_at DESC LIMIT 100""", (search, pattern, pattern, pattern, pattern))
            rows = cur.fetchall()
        for row in rows:
            row["job_type"] = "Not specified"
            row["skills"] = [v.strip() for v in str(row.get("skills") or "").split(",") if v.strip()]
        return jsonify(rows)
    except Exception:
        app.logger.exception("Jobs list failed")
        return json_error("Could not load jobs.", 500)
    finally:
        if conn: conn.close()

@app.get("/api/jobs/recommendations")
@app.get("/api/jobs/matches")
@require_verified_passport
def job_recommendations():
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""SELECT s.name FROM candidate_skills cs JOIN skills s ON s.id=cs.skill_id
                           WHERE cs.user_id=%s ORDER BY s.name""", (session["user_id"],))
            skills = [r["name"] for r in cur.fetchall()]
            cur.execute("""SELECT j.id,j.title,j.description,j.skills_required AS skills,j.location,j.salary_range,
                           u.full_name AS company_name FROM jobs j JOIN users u ON u.id=j.employer_id
                           WHERE j.is_active=1 ORDER BY j.created_at DESC LIMIT 100""")
            jobs = cur.fetchall()
        result = []
        for job in jobs:
            required = [x.strip() for x in str(job.get("skills") or "").split(",") if x.strip()]
            matched = [x for x in required if any(x.lower() in skill.lower() or skill.lower() in x.lower() for skill in skills)]
            score = round(100 * len(matched) / max(1, len(required)), 1) if required else 0
            job["skills"] = required
            job["job_type"] = "Not specified"
            job["match_score"] = score
            job["matched_skills"] = matched
            result.append(job)
        result.sort(key=lambda x: x["match_score"], reverse=True)
        return jsonify(result)
    except Exception:
        app.logger.exception("Job recommendations failed")
        return json_error("Could not load job recommendations.", 500)
    finally:
        if conn: conn.close()

@app.get("/api/my-applications")
@require_role()
def my_applications():
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("""SELECT a.id,a.status,a.applied_at,j.title AS job_title,u.full_name AS company_name
                           FROM applications a JOIN jobs j ON j.id=a.job_id JOIN users u ON u.id=j.employer_id
                           WHERE a.applicant_id=%s ORDER BY a.applied_at DESC""", (session["user_id"],))
            rows = cur.fetchall()
        return jsonify(rows)
    except Exception:
        app.logger.exception("Applications list failed")
        return json_error("Could not load applications.", 500)
    finally:
        if conn: conn.close()

@app.post("/api/applications")
@require_role()
def apply_for_job():
    data = body() or {}
    try: job_id = int(data.get("job_id"))
    except (TypeError, ValueError): return json_error("Choose a valid job.", 400)
    conn = None
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM jobs WHERE id=%s AND is_active=1", (job_id,))
            if not cur.fetchone(): return json_error("This job is no longer available.", 404)
            cur.execute("INSERT INTO applications(job_id,applicant_id) VALUES(%s,%s)", (job_id, session["user_id"]))
        conn.commit()
        return jsonify({"status":"success", "message":"Application submitted."}), 201
    except IntegrityError:
        if conn: conn.rollback()
        return json_error("You have already applied for this job.", 409)
    except Exception:
        if conn: conn.rollback()
        app.logger.exception("Job application failed")
        return json_error("Could not submit your application.", 500)
    finally:
        if conn: conn.close()

if __name__=="__main__": app.run(host="127.0.0.1",port=5000,debug=os.getenv("FLASK_DEBUG","0")=="1")
