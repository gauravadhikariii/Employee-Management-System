import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from database.db import get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-dev-only-change-before-deploy")
init_db()

DEPARTMENTS = ["Engineering", "Human Resources", "Sales", "Finance", "Marketing", "Operations", "Support"]

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def current_user():
    if "user_id" not in session:
        return None
    with get_db() as conn:
        return conn.execute(
            "SELECT id, username, full_name, email, theme FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

@app.context_processor
def inject_user():
    return {"current_user": current_user(), "departments": DEPARTMENTS}

@app.route("/")
def home():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            flash("Welcome back! You are signed in.", "success")
            return redirect(url_for("dashboard"))
        flash("Incorrect username or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM employees WHERE status='Active'").fetchone()[0]
        departments_count = conn.execute("SELECT COUNT(DISTINCT department) FROM employees").fetchone()[0]
        payroll = conn.execute("SELECT COALESCE(SUM(salary),0) FROM employees").fetchone()[0]
        recent = conn.execute("SELECT * FROM employees ORDER BY id DESC LIMIT 5").fetchall()
        dept_rows = conn.execute("SELECT department, COUNT(*) AS total FROM employees GROUP BY department ORDER BY total DESC").fetchall()
        status_rows = conn.execute("SELECT status, COUNT(*) AS total FROM employees GROUP BY status").fetchall()
    return render_template("dashboard.html", total=total, active=active, departments_count=departments_count,
                           payroll=payroll, recent=recent, dept_rows=dept_rows, status_rows=status_rows)

@app.route("/employees")
@login_required
def employees():
    q = request.args.get("q", "").strip()
    department = request.args.get("department", "").strip()
    status = request.args.get("status", "").strip()
    sql = "SELECT * FROM employees WHERE 1=1"
    params = []
    if q:
        sql += " AND (full_name LIKE ? OR employee_code LIKE ? OR email LIKE ? OR position LIKE ?)"
        params += [f"%{q}%"] * 4
    if department:
        sql += " AND department = ?"
        params.append(department)
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY id DESC"
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return render_template("employees.html", employees=rows, q=q, selected_department=department, selected_status=status)

def validate_employee(form):
    required = ["employee_code", "full_name", "email", "department", "position", "salary", "status", "joining_date"]
    for field in required:
        if not form.get(field, "").strip():
            return f"Please fill in {field.replace('_', ' ')}."
    try:
        salary = float(form.get("salary", "0"))
        if salary < 0:
            return "Salary cannot be negative."
    except ValueError:
        return "Salary must be a valid number."
    if "@" not in form.get("email", ""):
        return "Please enter a valid email address."
    return None

@app.route("/employees/add", methods=["GET", "POST"])
@login_required
def add_employee():
    if request.method == "POST":
        error = validate_employee(request.form)
        if error:
            flash(error, "error")
            return render_template("add_employee.html", employee=request.form)
        data = request.form
        try:
            with get_db() as conn:
                conn.execute("""INSERT INTO employees
                    (employee_code, full_name, email, phone, department, position, salary, status, joining_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (data["employee_code"].strip(), data["full_name"].strip(), data["email"].strip(),
                     data.get("phone", "").strip(), data["department"], data["position"].strip(),
                     float(data["salary"]), data["status"], data["joining_date"]))
                conn.commit()
            flash("Employee added successfully.", "success")
            return redirect(url_for("employees"))
        except Exception:
            flash("Could not add employee. Employee ID may already exist.", "error")
    return render_template("add_employee.html", employee={})

@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    with get_db() as conn:
        employee = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if not employee:
        flash("Employee not found.", "error")
        return redirect(url_for("employees"))
    if request.method == "POST":
        error = validate_employee(request.form)
        if error:
            flash(error, "error")
            return render_template("edit_employee.html", employee=request.form, employee_id=employee_id)
        data = request.form
        try:
            with get_db() as conn:
                conn.execute("""UPDATE employees SET employee_code=?, full_name=?, email=?, phone=?,
                    department=?, position=?, salary=?, status=?, joining_date=? WHERE id=?""",
                    (data["employee_code"].strip(), data["full_name"].strip(), data["email"].strip(),
                     data.get("phone", "").strip(), data["department"], data["position"].strip(),
                     float(data["salary"]), data["status"], data["joining_date"], employee_id))
                conn.commit()
            flash("Employee updated successfully.", "success")
            return redirect(url_for("employees"))
        except Exception:
            flash("Could not update employee. Check that the Employee ID is unique.", "error")
    return render_template("edit_employee.html", employee=employee, employee_id=employee_id)

@app.route("/employees/<int:employee_id>/delete", methods=["POST"])
@login_required
def delete_employee(employee_id):
    with get_db() as conn:
        conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        conn.commit()
    flash("Employee deleted.", "success")
    return redirect(url_for("employees"))

@app.route("/reports")
@login_required
def reports():
    with get_db() as conn:
        dept_rows = conn.execute("SELECT department, COUNT(*) AS total, COALESCE(AVG(salary),0) AS avg_salary FROM employees GROUP BY department ORDER BY total DESC").fetchall()
        status_rows = conn.execute("SELECT status, COUNT(*) AS total FROM employees GROUP BY status").fetchall()
        total_payroll = conn.execute("SELECT COALESCE(SUM(salary),0) FROM employees").fetchone()[0]
    return render_template("reports.html", dept_rows=dept_rows, status_rows=status_rows, total_payroll=total_payroll)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        if not full_name or "@" not in email:
            flash("Enter your name and a valid email.", "error")
        else:
            with get_db() as conn:
                conn.execute("UPDATE users SET full_name=?, email=? WHERE id=?", (full_name, email, session["user_id"]))
                conn.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("profile"))
    return render_template("profile.html", user=current_user())

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        theme = request.form.get("theme", "light")
        if theme not in ("light", "dark"):
            theme = "light"
        with get_db() as conn:
            conn.execute("UPDATE users SET theme=? WHERE id=?", (theme, session["user_id"]))
            conn.commit()
        flash("Theme preference saved.", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html", user=current_user())

@app.route("/change-password", methods=["POST"])
@login_required
def change_password():
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    if len(new_password) < 8:
        flash("New password must be at least 8 characters.", "error")
        return redirect(url_for("profile"))
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
        if not check_password_hash(user["password_hash"], old_password):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("profile"))
        conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                     (generate_password_hash(new_password), session["user_id"]))
        conn.commit()
    flash("Password changed successfully.", "success")
    return redirect(url_for("profile"))

if __name__ == "__main__":
    app.run(debug=False)
