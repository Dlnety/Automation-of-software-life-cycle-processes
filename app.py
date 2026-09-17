import os
from functools import wraps

import oracledb
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for

import db

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")


def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "username" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Недостаточно прав для открытия этой страницы.", "error")
                return redirect(url_for("home"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def flash_exception(exc):
    if isinstance(exc, ValueError):
        flash(str(exc), "error")
    elif isinstance(exc, oracledb.DatabaseError):
        flash(db.friendly_db_error(exc), "error")
    else:
        app.logger.exception("Unexpected error")
        flash("Произошла ошибка. Повторите операцию или обратитесь к администратору.", "error")


@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("academic_dashboard" if session.get("role") == "academic" else "teacher_dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        try:
            user = db.authenticate(username, password)
        except Exception as exc:
            flash_exception(exc)
            return render_template("login.html")
        if user:
            session.clear()
            session.update(username=user["username"], role=user["role"], role_title=user["title"])
            return redirect(url_for("home"))
        flash("Неверный логин или пароль.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/academic", methods=["GET", "POST"])
@login_required("academic")
def academic_dashboard():
    selected_form = request.form.get("study_form", "очная")
    discipline_name = request.form.get("discipline_name", "").strip()
    try:
        count = db.count_students_by_form(selected_form)
        discipline = db.get_discipline_info(discipline_name) if discipline_name else None
        if discipline_name and not discipline:
            flash("Дисциплина не найдена.", "error")
    except Exception as exc:
        flash_exception(exc)
        count, discipline = 0, None
    return render_template("academic.html", selected_form=selected_form, count=count,
                           discipline_name=discipline_name, discipline=discipline)


@app.route("/academic/students", methods=["GET", "POST"])
@login_required("academic")
def students():
    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in ["last_name", "first_name", "middle_name", "year", "form", "group_id"]}
        try:
            db.add_student(data, session["username"])
            flash("Студент добавлен.", "success")
            return redirect(url_for("students"))
        except Exception as exc:
            flash_exception(exc)
    return render_template("students.html", students=db.list_students(), groups=db.list_groups(), study_forms=db.STUDY_FORMS)


@app.route("/academic/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required("academic")
def edit_student(student_id):
    student = db.get_student(student_id)
    if not student:
        flash("Студент не найден.", "error")
        return redirect(url_for("students"))
    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in ["last_name", "first_name", "middle_name", "year", "form", "group_id"]}
        try:
            db.update_student(student_id, data, session["username"])
            flash("Данные студента изменены.", "success")
            return redirect(url_for("students"))
        except Exception as exc:
            flash_exception(exc)
    return render_template("edit_student.html", student=student, groups=db.list_groups(), study_forms=db.STUDY_FORMS)


@app.route("/academic/curriculum", methods=["GET", "POST"])
@login_required("academic")
def curriculum():
    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in ["specialty_id", "discipline_id", "semester", "hours", "report_type"]}
        try:
            db.add_curriculum(data, session["username"])
            flash("Элемент учебного плана добавлен.", "success")
            return redirect(url_for("curriculum"))
        except Exception as exc:
            flash_exception(exc)
    return render_template("curriculum.html", curriculum=db.list_curriculum(), specialties=db.list_specialties(),
                           disciplines=db.list_disciplines(), report_types=db.REPORT_TYPES)


@app.route("/academic/curriculum/<int:curriculum_id>/edit", methods=["GET", "POST"])
@login_required("academic")
def edit_curriculum(curriculum_id):
    item = db.get_curriculum(curriculum_id)
    if not item:
        flash("Элемент учебного плана не найден.", "error")
        return redirect(url_for("curriculum"))
    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in ["specialty_id", "discipline_id", "semester", "hours", "report_type"]}
        try:
            db.update_curriculum(curriculum_id, data, session["username"])
            flash("Учебный план изменён.", "success")
            return redirect(url_for("curriculum"))
        except Exception as exc:
            flash_exception(exc)
    return render_template("edit_curriculum.html", item=item, specialties=db.list_specialties(),
                           disciplines=db.list_disciplines(), report_types=db.REPORT_TYPES)


@app.route("/teacher")
@login_required("teacher")
def teacher_dashboard():
    return render_template("teacher.html", students=db.list_students(), disciplines=db.list_disciplines())


@app.route("/teacher/grades", methods=["GET", "POST"])
@login_required("teacher")
def grades():
    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in ["student_id", "discipline_id", "period", "grade"]}
        try:
            db.add_grade(data, session["username"])
            flash("Оценка добавлена.", "success")
            return redirect(url_for("grades"))
        except Exception as exc:
            flash_exception(exc)
    return render_template("grades.html", grades=db.list_grades(), students=db.list_students(), disciplines=db.list_disciplines())


@app.route("/teacher/grades/<int:grade_id>/edit", methods=["GET", "POST"])
@login_required("teacher")
def edit_grade(grade_id):
    item = db.get_grade(grade_id)
    if not item:
        flash("Запись журнала не найдена.", "error")
        return redirect(url_for("grades"))
    if request.method == "POST":
        try:
            db.update_grade(grade_id, {"grade": request.form.get("grade", "").strip()}, session["username"])
            flash("Оценка изменена.", "success")
            return redirect(url_for("grades"))
        except Exception as exc:
            flash_exception(exc)
    return render_template("edit_grade.html", item=item)


@app.errorhandler(oracledb.DatabaseError)
def handle_database_error(exc):
    app.logger.error("Database error: %s", type(exc).__name__)
    return render_template("error.html", message=db.friendly_db_error(exc)), 500


@app.errorhandler(500)
def handle_internal_error(exc):
    app.logger.error("Internal server error")
    return render_template("error.html", message="Внутренняя ошибка приложения. Повторите попытку позже."), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG", "0") == "1")
