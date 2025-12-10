from flask import Flask, render_template, redirect, url_for, request, flash, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime, timedelta
from uuid import uuid4

from database import init_db, migrate_from_json, get_db
from models import User, Application, Document, Comment, Announcement

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-in-production"
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)

if not os.path.isdir(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

init_db()
migrate_from_json()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            flash("Najprv sa prihláste.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = session.get("user")
            if not user:
                flash("Najprv sa prihláste.", "warning")
                return redirect(url_for("login"))
            if user.get("role") not in allowed_roles:
                flash("Nemáte oprávnenie na prístup k tejto stránke.", "danger")
                if user.get("role") == "student":
                    return redirect(url_for("student_dashboard"))
                else:
                    return redirect(url_for("admin_panel"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def guest_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user"):
            role = session["user"]["role"]
            if role == "student":
                return redirect(url_for("student_dashboard"))
            else:
                return redirect(url_for("admin_panel"))
        return f(*args, **kwargs)
    return decorated_function


DOCUMENT_REQUIREMENTS = [
    {"key": "cv", "label": "Životopis (v angličtine)"},
    {"key": "motivation", "label": "Motivačný list (v angličtine)"},
    {"key": "grades", "label": "Výpis známok potvrdený fakultou"},
    {"key": "plan", "label": "Predpokladaný študijný plán"},
    {"key": "language", "label": "Osvedčenie o jazykových znalostiach"},
    {"key": "passport", "label": "Kópia pasu (zahraniční študenti)"},
    {"key": "other", "label": "Iné – doplňujúce dokumenty"},
]


@app.context_processor
def inject_current_user():
    return {"current_user": session.get("user")}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
@guest_required
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role")

        user = User.get_by_email(email)
        if user and User.verify_password(user, password) and user["role"] == role:
            session["user"] = {
                "name": user["name"],
                "role": user["role"],
                "email": user["email"],
            }
            session.permanent = True
            flash(f"Vitajte, {user['name']}!", "success")
            return redirect(url_for("student_dashboard" if role == "student" else "admin_panel"))

        flash("Nesprávne prihlasovacie údaje.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
@guest_required
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        role = request.form.get("role", "student")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        faculty = request.form.get("faculty", "").strip()

        if not email or not password:
            flash("Vyplňte e‑mail a heslo.", "danger")
            return render_template("register.html")

        if password != password2:
            flash("Heslá sa nezhodujú.", "danger")
            return render_template("register.html")

        if len(password) < 4:
            flash("Heslo musí mať aspoň 4 znaky.", "danger")
            return render_template("register.html")

        if User.get_by_email(email):
            flash("Používateľ s týmto e‑mailom už existuje.", "danger")
            return render_template("register.html")

        if User.create(email, password, role, full_name, faculty):
            session["user"] = {
                "name": full_name,
                "role": role,
                "email": email,
            }
            session.permanent = True
            flash(f"Registrácia používateľa {full_name} bola úspešná.", "success")
            return redirect(url_for("student_dashboard" if role == "student" else "admin_panel"))
        else:
            flash("Chyba pri vytváraní účtu.", "danger")
    
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Boli ste odhlásený.", "info")
    return redirect(url_for("index"))


@app.route("/student")
@role_required("student")
def student_dashboard():
    user = session.get("user")
    user_apps = Application.get_by_student(user["email"])
    tab = request.args.get("tab", "home")

    for app in user_apps:
        app["documents"] = Document.get_by_application(app["id"])

    total_documents = sum(len(app.get("documents", [])) for app in user_apps)
    total_required = len(DOCUMENT_REQUIREMENTS) * len(user_apps) if user_apps else len(DOCUMENT_REQUIREMENTS)
    unread_messages = 0
    
    pending_apps = len([a for a in user_apps if a["status"] == "Podaná"])
    approved_apps = len([a for a in user_apps if a["status"] == "Schválená"])
    
    latest_docs_by_key: dict[str, dict] = {}
    if user_apps:
        latest = user_apps[0]
        for d in latest.get("documents", []):
            latest_docs_by_key[d["document_key"]] = d
    
    all_announcements = Announcement.get_all()
    latest_announcements = all_announcements[:5]

    return render_template(
        "student_dashboard.html",
        applications=user_apps,
        required_documents=DOCUMENT_REQUIREMENTS,
        docs_by_key=latest_docs_by_key,
        active_tab=tab,
        total_documents=total_documents,
        total_required=total_required,
        unread_messages=0,
        pending_apps=pending_apps,
        approved_apps=approved_apps,
        latest_announcements=latest_announcements,
        all_announcements=all_announcements,
    )


@app.route("/student/application/<app_id>")
@role_required("student")
def student_view_application(app_id):
    user = session.get("user")
    application = Application.get_by_id(app_id)
    
    if not application or application["student_email"] != user["email"]:
        flash("Prihláška nebola nájdená.", "danger")
        return redirect(url_for("student_dashboard"))
    
    application["documents"] = Document.get_by_application(app_id)
    application["comments"] = Comment.get_by_application(app_id)
    
    return render_template("student_view_application.html", application=application, required_documents=DOCUMENT_REQUIREMENTS)


@app.route("/student/announcements")
@role_required("student")
def student_announcements():
    announcements = Announcement.get_all()
    return render_template("student_announcements.html", announcements=announcements, active_tab="announcements")


@app.route("/student/profile", methods=["GET", "POST"])
@role_required("student")
def student_profile():
    user = session.get("user")
    user_data = User.get_by_email(user["email"])
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        faculty = request.form.get("faculty", "").strip()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if name:
            User.update(user["email"], name=name, faculty=faculty)
            session["user"]["name"] = name
            flash("Profil bol aktualizovaný.", "success")
        
        if new_password:
            if not current_password or not User.verify_password(user_data, current_password):
                flash("Nesprávne aktuálne heslo.", "danger")
            elif new_password != confirm_password:
                flash("Nové heslá sa nezhodujú.", "danger")
            elif len(new_password) < 4:
                flash("Heslo musí mať aspoň 4 znaky.", "danger")
            else:
                User.update_password(user["email"], new_password)
                flash("Heslo bolo zmenené.", "success")
        
        return redirect(url_for("student_profile"))
    
    return render_template("student_profile.html", user_data=user_data, active_tab="profile")


@app.route("/student/application/<app_id>/update-documents", methods=["GET", "POST"])
@role_required("student")
def update_application_documents(app_id):
    user = session.get("user")
    application = Application.get_by_id(app_id)
    
    if not application or application["student_email"] != user["email"]:
        flash("Prihláška nebola nájdená.", "danger")
        return redirect(url_for("student_dashboard"))
    
    if application["status"] != "Podaná":
        flash("Dokumenty možno aktualizovať len pri prihláškach so stavom 'Podaná'.", "warning")
        return redirect(url_for("student_view_application", app_id=app_id))
    
    if request.method == "POST":
        uploaded_count = 0
        for req in DOCUMENT_REQUIREMENTS:
            field_name = f"doc_{req['key']}"
            f = request.files.get(field_name)
            if f and f.filename:
                filename = secure_filename(f.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}_{filename}"
                path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
                f.save(path)
                
                existing_docs = Document.get_by_application(app_id)
                existing_doc = next((d for d in existing_docs if d["document_key"] == req["key"]), None)
                
                if existing_doc:
                    old_file_path = os.path.join(app.config["UPLOAD_FOLDER"], existing_doc["filename"])
                    if os.path.exists(old_file_path):
                        try:
                            os.remove(old_file_path)
                        except:
                            pass
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE documents 
                        SET filename = ?, status = 'Odoslaný', uploaded_at = ?
                        WHERE id = ?
                    """, (unique_filename, datetime.now(), existing_doc["id"]))
                    conn.commit()
                    conn.close()
                else:
                    Document.add_to_application(app_id, req["key"], req["label"], unique_filename)
                
                uploaded_count += 1
        
        all_docs = Document.get_by_application(app_id)
        progress = int((len(all_docs) / len(DOCUMENT_REQUIREMENTS)) * 100)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE applications SET progress = ? WHERE id = ?", (progress, app_id))
        conn.commit()
        conn.close()
        
        flash(f"Dokumenty boli aktualizované ({uploaded_count} súborov).", "success")
        return redirect(url_for("student_view_application", app_id=app_id))
    
    application["documents"] = Document.get_by_application(app_id)
    return render_template("update_documents.html", application=application, required_documents=DOCUMENT_REQUIREMENTS)


@app.route("/download/<filename>")
@login_required
def download_file(filename):
    user = session.get("user")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE filename = ?", (filename,))
    doc = cursor.fetchone()
    conn.close()
    
    if doc:
        doc = dict(doc)
        application = Application.get_by_id(doc["application_id"])
        if user["role"] == "admin" or (user["role"] == "student" and application["student_email"] == user["email"]):
            return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)
    
    flash("Nemáte oprávnenie na prístup k tomuto súboru.", "danger")
    return redirect(url_for("student_dashboard" if user["role"] == "student" else "admin_panel"))




@app.route("/admin")
@role_required("admin")
def admin_panel():
    tab = request.args.get("tab", "home")
    status_filter = request.args.get("status", "all")
    search_query = request.args.get("search", "").strip()
    student_email = request.args.get("student", "").strip()
    
    all_students = User.get_all_students()
    
    if student_email:
        all_applications = Application.get_by_student(student_email)
        if tab == "students":
            tab = "applications"
    else:
        all_applications = Application.get_all()
    
    if search_query:
        all_applications = [app for app in all_applications 
                          if search_query.lower() in app.get("university", "").lower() 
                          or search_query.lower() in app.get("student_name", "").lower()]
    
    if status_filter != "all":
        all_applications = [app for app in all_applications if app.get("status") == status_filter]
    
    all_announcements = Announcement.get_all()
    
    for app in all_applications:
        app["documents"] = Document.get_by_application(app["id"])
    
    all_apps_for_stats = Application.get_all()
    total_students = len(all_students)
    applications_pending = len([a for a in all_apps_for_stats if a["status"] == "Podaná"])
    applications_approved = len([a for a in all_apps_for_stats if a["status"] == "Schválená"])
    applications_rejected = len([a for a in all_apps_for_stats if a["status"] == "Zamietnutá"])
    documents_waiting = sum(len(Document.get_by_application(app["id"])) for app in all_apps_for_stats)
    unread_messages = 0
    total_announcements = len(all_announcements)

    stats = {
        "students_total": total_students,
        "applications_pending": applications_pending,
        "applications_approved": applications_approved,
        "applications_rejected": applications_rejected,
        "documents_waiting": documents_waiting,
        "unread_messages": unread_messages,
        "total_announcements": total_announcements,
    }
    
    latest_apps = all_applications[:10]
    
    latest_announcements = all_announcements[:5]
    
    return render_template(
        "admin_panel.html",
        stats=stats,
        latest_apps=latest_apps,
        latest_announcements=latest_announcements,
        active_tab=tab,
        required_documents=DOCUMENT_REQUIREMENTS,
        all_applications=all_applications,
        all_students=all_students,
        all_announcements=all_announcements,
        status_filter=status_filter,
        search_query=search_query,
        selected_student=student_email,
    )


@app.route("/admin/applications/<app_id>")
@role_required("admin")
def view_application(app_id):
    application = Application.get_by_id(app_id)
    if not application:
        flash("Prihláška nebola nájdená.", "danger")
        return redirect(url_for("admin_panel", tab="applications"))
    
    application["documents"] = Document.get_by_application(app_id)
    application["comments"] = Comment.get_by_application(app_id)
    
    return render_template("admin_view_application.html", application=application, required_documents=DOCUMENT_REQUIREMENTS)


@app.route("/admin/applications/<app_id>/approve", methods=["POST"])
@role_required("admin")
def approve_application(app_id):
    application = Application.get_by_id(app_id)
    if not application:
        flash("Prihláška nebola nájdená.", "danger")
        return redirect(url_for("admin_panel", tab="applications"))
    
    Application.approve(app_id, session["user"]["email"])
    flash(f"Prihláška od {application['student_name']} bola schválená.", "success")
    return redirect(url_for("admin_panel", tab="applications"))


@app.route("/admin/applications/<app_id>/reject", methods=["POST"])
@role_required("admin")
def reject_application(app_id):
    application = Application.get_by_id(app_id)
    if not application:
        flash("Prihláška nebola nájdená.", "danger")
        return redirect(url_for("admin_panel", tab="applications"))
    
    reason = request.form.get("reason", "").strip()
    if not reason:
        flash("Zadajte dôvod zamietnutia.", "warning")
        return redirect(url_for("admin_panel", tab="applications"))
    
    Application.reject(app_id, session["user"]["email"], reason)
    flash(f"Prihláška od {application['student_name']} bola zamietnutá.", "info")
    return redirect(url_for("admin_panel", tab="applications"))


@app.route("/admin/applications/<app_id>/comment", methods=["POST"])
@role_required("admin")
def comment_application(app_id):
    application = Application.get_by_id(app_id)
    if not application:
        flash("Prihláška nebola nájdená.", "danger")
        return redirect(url_for("admin_panel", tab="applications"))
    
    comment_text = request.form.get("comment", "").strip()
    if not comment_text:
        flash("Komentár nemôže byť prázdny.", "warning")
        return redirect(url_for("admin_panel", tab="applications"))
    
    Comment.create(
        app_id,
        session["user"]["email"],
        session["user"]["name"],
        comment_text
    )
    
    flash("Komentár bol pridaný.", "success")
    return redirect(url_for("admin_panel", tab="applications"))


@app.route("/admin/announcements/new", methods=["GET", "POST"])
@role_required("admin")
def new_announcement():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        priority = request.form.get("priority", "normal")
        
        if not title or not content:
            flash("Vyplňte názov a obsah oznámenia.", "danger")
            return render_template("admin_announcement_form.html", active_tab="announcements")
        
        Announcement.create(
            title,
            content,
            priority,
            session["user"]["email"],
            session["user"]["name"]
        )
        
        flash("Oznámenie bolo vytvorené.", "success")
        return redirect(url_for("admin_panel", tab="announcements"))
    
    return render_template("admin_announcement_form.html", active_tab="announcements")


@app.route("/admin/announcements/<ann_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_announcement(ann_id):
    announcement = Announcement.get_by_id(ann_id)
    if not announcement:
        flash("Oznámenie nebolo nájdené.", "danger")
        return redirect(url_for("admin_panel", tab="announcements"))
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        priority = request.form.get("priority", "normal")
        
        if not title or not content:
            flash("Vyplňte názov a obsah oznámenia.", "danger")
            return render_template("admin_announcement_form.html", announcement=announcement, active_tab="announcements")
        
        Announcement.update(ann_id, title, content, priority)
        
        flash("Oznámenie bolo aktualizované.", "success")
        return redirect(url_for("admin_panel", tab="announcements"))
    
    return render_template("admin_announcement_form.html", announcement=announcement, active_tab="announcements")


@app.route("/admin/announcements/<ann_id>/delete", methods=["POST"])
@role_required("admin")
def delete_announcement(ann_id):
    announcement = Announcement.get_by_id(ann_id)
    if announcement:
        Announcement.delete(ann_id)
        flash("Oznámenie bolo zmazané.", "success")
    else:
        flash("Oznámenie nebolo nájdené.", "warning")
    
    return redirect(url_for("admin_panel", tab="announcements"))




@app.route("/admin/users")
@role_required("admin")
def admin_users():
    users = User.get_all()
    return render_template("admin_users.html", users=users)


@app.route("/admin/users/<user_email>/delete", methods=["POST"])
@role_required("admin")
def delete_user(user_email):
    if user_email == session["user"]["email"]:
        flash("Nemôžete zmazať svoj vlastný účet.", "danger")
    else:
        User.delete(user_email)
        flash("Používateľ bol zmazaný.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/documents/<doc_id>/update-status", methods=["POST"])
@role_required("admin")
def update_document_status(doc_id):
    status = request.form.get("status", "").strip()
    if status in ["Odoslaný", "V preverovaní", "Schválený", "Zamietnutý"]:
        Document.update_status(doc_id, status)
        flash("Stav dokumentu bol aktualizovaný.", "success")
    else:
        flash("Neplatný stav dokumentu.", "danger")
    
    return redirect(url_for("admin_panel", tab="applications"))


@app.route("/admin/statistics")
@role_required("admin")
def admin_statistics():
    all_applications = Application.get_all()
    all_students = User.get_all_students()
    
    applications_approved = len([a for a in all_applications if a["status"] == "Schválená"])
    applications_rejected = len([a for a in all_applications if a["status"] == "Zamietnutá"])
    
    monthly_stats = {}
    for app in all_applications:
        if app.get("created_at"):
            try:
                if isinstance(app["created_at"], str):
                    try:
                        date_obj = datetime.fromisoformat(app["created_at"].replace(" ", "T"))
                    except:
                        date_obj = datetime.strptime(app["created_at"], "%Y-%m-%d %H:%M:%S")
                else:
                    date_obj = app["created_at"]
                month_key = date_obj.strftime("%Y-%m")
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = {"total": 0, "approved": 0, "rejected": 0}
                monthly_stats[month_key]["total"] += 1
                if app["status"] == "Schválená":
                    monthly_stats[month_key]["approved"] += 1
                elif app["status"] == "Zamietnutá":
                    monthly_stats[month_key]["rejected"] += 1
            except Exception as e:
                pass
    
    mobility_stats = {}
    for app in all_applications:
        mob_type = app.get("mobility_type", "Nezadané")
        mobility_stats[mob_type] = mobility_stats.get(mob_type, 0) + 1
    
    doc_stats = {}
    for req in DOCUMENT_REQUIREMENTS:
        count = 0
        for app in all_applications:
            docs = Document.get_by_application(app["id"])
            if any(d["document_key"] == req["key"] for d in docs):
                count += 1
        doc_stats[req["label"]] = count
    
    return render_template(
        "admin_statistics.html",
        monthly_stats=monthly_stats,
        mobility_stats=mobility_stats,
        doc_stats=doc_stats,
        total_applications=len(all_applications),
        total_students=len(all_students),
        applications_approved=applications_approved,
        applications_rejected=applications_rejected,
        active_tab="statistics",
    )


@app.route("/application", methods=["GET", "POST"])
@role_required("student")
def application_form():
    if request.method == "POST":
        user = session.get("user")
        destination = request.form.get("destination", "").strip()
        mobility_type = request.form.get("mobility_type") or "Štúdium"

        documents = []
        uploaded_count = 0
        for req in DOCUMENT_REQUIREMENTS:
            field_name = f"doc_{req['key']}"
            f = request.files.get(field_name)
            if f and f.filename:
                filename = secure_filename(f.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}_{filename}"
                path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
                f.save(path)
                uploaded_count += 1
                documents.append(
                    {
                        "key": req["key"],
                        "label": req["label"],
                        "filename": unique_filename,
                    }
                )

        app_id = Application.create(
            user["email"],
            user["name"],
            destination or "Nešpecifikovaná univerzita",
            mobility_type,
            documents
        )

        flash(
            f"Prihláška bola vytvorená a dokumenty boli nahrané ({uploaded_count} z {len(DOCUMENT_REQUIREMENTS)}).",
            "success",
        )
        return redirect(url_for("student_dashboard"))

    return render_template(
        "application_form.html", required_documents=DOCUMENT_REQUIREMENTS
    )


@app.route("/applications/<app_id>/delete", methods=["POST"])
@role_required("student", "admin")
def delete_application(app_id):
    user = session.get("user")
    application = Application.get_by_id(app_id)
    
    if not application:
        flash("Prihláška nebola nájdená.", "warning")
    elif user["role"] == "student" and application["student_email"] != user["email"]:
        flash("Nemáte oprávnenie na zmazanie tejto prihlášky.", "danger")
    else:
        Application.delete(app_id)
        flash("Prihláška bola zmazaná.", "info")
    
    return redirect(url_for("student_dashboard" if user["role"] == "student" else "admin_panel"))



@app.errorhandler(404)
def not_found(error):
    flash("Stránka nebola nájdená.", "warning")
    return redirect(url_for("index")), 404

@app.errorhandler(500)
def internal_error(error):
    flash("Vyskytla sa chyba. Skúste to znova.", "danger")
    return redirect(url_for("index")), 500


if __name__ == "__main__":
    app.run(debug=True)



