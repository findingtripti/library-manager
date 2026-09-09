"""
app.py
Library Book Manager - Flask + SQLite mini project, with dashboard analytics charts.

Run with:  python app.py
Then open: http://127.0.0.1:5000
Login -> username: admin | password: admin123
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import date, timedelta
from flask_mail import Mail, Message
import calendar
from database import get_connection, init_db

app = Flask(__name__)
app.secret_key = "library-mini-project-secret-key"  

app.config["MAIL_SERVER"] = "smtp-relay.brevo.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
import os
app.config["MAIL_USERNAME"] =os.getenv("SMTP_EMAIL")

app.config["MAIL_PASSWORD"] = os.getenv("SMTP_PASSWORD")

mail = Mail(app)

LOAN_PERIOD_DAYS = 14
FINE_PER_DAY = 5  # rupees

# Helpers


def send_email(to_email, subject, body):
    msg = Message(
        subject,
        recipients=[to_email]
    )
    msg.body = body
    mail.send(msg)


def login_required(view):
    """Simple decorator to protect routes behind admin login."""
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def calculate_fine(due_date_str, return_date_str=None):
    """Calculate fine (in rupees) given a due date and an optional return date.
    If no return date is given, fine is computed against today's date (i.e. an
    'if returned today' preview for currently issued books).
    """
    due = date.fromisoformat(due_date_str)
    ref = date.fromisoformat(return_date_str) if return_date_str else date.today()
    overdue_days = (ref - due).days
    if overdue_days > 0:
        return overdue_days * FINE_PER_DAY
    return 0

# Auth routes

@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("dashboard")) if "user_id" in session else redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        conn = get_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login")) 

# Dashboard (with analytics charts)


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_connection()

    total_books = conn.execute("SELECT COALESCE(SUM(total_copies),0) AS c FROM books").fetchone()["c"]
    available_books = conn.execute("SELECT COALESCE(SUM(available_copies),0) AS c FROM books").fetchone()["c"]
    total_members = conn.execute("SELECT COUNT(*) AS c FROM members").fetchone()["c"]
    currently_issued = conn.execute(
        "SELECT COUNT(*) AS c FROM issue_records WHERE status = 'Issued'"
    ).fetchone()["c"]

    overdue_rows = conn.execute(
        """
        SELECT ir.issue_id, b.title, m.name AS member_name, ir.due_date
        FROM issue_records ir
        JOIN books b ON b.book_id = ir.book_id
        JOIN members m ON m.member_id = ir.member_id
        WHERE ir.status = 'Issued' AND ir.due_date < date('now')
        ORDER BY ir.due_date ASC
        """
    ).fetchall()

    overdue_list = []
    for row in overdue_rows:
        fine = calculate_fine(row["due_date"])
        overdue_list.append({**dict(row), "fine": fine})

    conn.close()

    stats = {
        "total_books": total_books,
        "available_books": available_books,
        "total_members": total_members,
        "currently_issued": currently_issued,
        "overdue_count": len(overdue_list),
    }

    return render_template("dashboard.html", stats=stats, overdue_list=overdue_list)


@app.route("/api/analytics/issues-per-month")
@login_required
def analytics_issues_per_month():
    """Returns issue counts for each of the last 6 months, for the dashboard chart."""
    conn = get_connection()

    # Build the last 6 (year, month) buckets ending with the current month.
    today = date.today()
    buckets = []
    y, m = today.year, today.month
    for _ in range(6):
        buckets.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    buckets.reverse()

    counts = []
    labels = []
    for (y, m) in buckets:
        month_str = f"{y:04d}-{m:02d}"
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM issue_records WHERE strftime('%Y-%m', issue_date) = ?",
            (month_str,),
        ).fetchone()
        counts.append(row["c"])
        labels.append(f"{calendar.month_abbr[m]} {y}")

    conn.close()
    return jsonify({"labels": labels, "counts": counts})


@app.route("/api/analytics/category-popularity")
@login_required
def analytics_category_popularity():
    """Returns the number of times each book category has been issued,
    for the dashboard's 'most borrowed categories' chart."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT COALESCE(b.category, 'Uncategorized') AS category, COUNT(ir.issue_id) AS times_issued
        FROM issue_records ir
        JOIN books b ON b.book_id = ir.book_id
        GROUP BY category
        ORDER BY times_issued DESC
        LIMIT 8
        """
    ).fetchall()
    conn.close()

    labels = [row["category"] for row in rows]
    counts = [row["times_issued"] for row in rows]
    return jsonify({"labels": labels, "counts": counts})

# Book management

@app.route("/books")
@login_required
def books():
    query = request.args.get("q", "").strip()
    conn = get_connection()
    if query:
        like = f"%{query}%"
        rows = conn.execute(
            """SELECT * FROM books
               WHERE title LIKE ? OR author LIKE ? OR category LIKE ? OR isbn LIKE ?
               ORDER BY title""",
            (like, like, like, like),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM books ORDER BY title").fetchall()
    conn.close()
    return render_template("books.html", books=rows, query=query)


@app.route("/books/add", methods=["POST"])
@login_required
def add_book():
    title = request.form["title"].strip()
    author = request.form["author"].strip()
    publisher = request.form.get("publisher", "").strip()
    isbn = request.form.get("isbn", "").strip()
    category = request.form.get("category", "").strip()
    total_copies = int(request.form.get("total_copies", 1))

    if not title or not author or total_copies < 1:
        flash("Title, author and a valid copy count are required.", "danger")
        return redirect(url_for("books"))

    conn = get_connection()
    conn.execute(
        """INSERT INTO books (title, author, publisher, isbn, category, total_copies, available_copies)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (title, author, publisher, isbn, category, total_copies, total_copies),
    )
    conn.commit()
    conn.close()
    flash(f'Book "{title}" added successfully.', "success")
    return redirect(url_for("books"))


@app.route("/books/delete/<int:book_id>", methods=["POST"])
@login_required
def delete_book(book_id):
    conn = get_connection()
    active = conn.execute(
        "SELECT COUNT(*) AS c FROM issue_records WHERE book_id = ? AND status = 'Issued'",
        (book_id,),
    ).fetchone()["c"]
    if active > 0:
        flash("Cannot delete: this book has copies currently issued.", "danger")
    else:
        conn.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
        conn.commit()
        flash("Book deleted.", "info")
    conn.close()
    return redirect(url_for("books"))

# Member management

@app.route("/members")
@login_required
def members():
    query = request.args.get("q", "").strip()
    conn = get_connection()
    if query:
        like = f"%{query}%"
        rows = conn.execute(
            "SELECT * FROM members WHERE name LIKE ? OR email LIKE ? OR phone LIKE ? ORDER BY name",
            (like, like, like),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM members ORDER BY name").fetchall()
    conn.close()
    return render_template("members.html", members=rows, query=query)


@app.route("/members/add", methods=["POST"])
@login_required
def add_member():
    name = request.form["name"].strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()

    if not name:
        flash("Member name is required.", "danger")
        return redirect(url_for("members"))

    conn = get_connection()
    conn.execute(
        "INSERT INTO members (name, email, phone, address, join_date) VALUES (?, ?, ?, ?, date('now'))",
        (name, email, phone, address),
    )
    conn.commit()
    conn.close()
    flash(f'Member "{name}" added successfully.', "success")
    return redirect(url_for("members"))


@app.route("/members/delete/<int:member_id>", methods=["POST"])
@login_required
def delete_member(member_id):
    conn = get_connection()
    active = conn.execute(
        "SELECT COUNT(*) AS c FROM issue_records WHERE member_id = ? AND status = 'Issued'",
        (member_id,),
    ).fetchone()["c"]
    if active > 0:
        flash("Cannot delete: this member has books currently issued.", "danger")
    else:
        conn.execute("DELETE FROM members WHERE member_id = ?", (member_id,))
        conn.commit()
        flash("Member deleted.", "info")
    conn.close()
    return redirect(url_for("members"))

# Issue / Return

@app.route("/issue-return")
@login_required
def issue_return():
    conn = get_connection()
    available_books = conn.execute(
        "SELECT * FROM books WHERE available_copies > 0 ORDER BY title"
    ).fetchall()
    all_members = conn.execute("SELECT * FROM members ORDER BY name").fetchall()

    active_issues = conn.execute(
        """
        SELECT ir.issue_id, b.title, m.name AS member_name, ir.issue_date, ir.due_date
        FROM issue_records ir
        JOIN books b ON b.book_id = ir.book_id
        JOIN members m ON m.member_id = ir.member_id
        WHERE ir.status = 'Issued'
        ORDER BY ir.due_date ASC
        """
    ).fetchall()
    conn.close()

    active_list = []
    for row in active_issues:
        fine_preview = calculate_fine(row["due_date"])
        is_overdue = fine_preview > 0
        active_list.append({**dict(row), "fine_preview": fine_preview, "is_overdue": is_overdue})

    return render_template(
        "issue_return.html",
        available_books=available_books,
        members=all_members,
        active_issues=active_list,
        loan_period=LOAN_PERIOD_DAYS,
        fine_per_day=FINE_PER_DAY,
    )


@app.route("/issue", methods=["POST"])
@login_required
def issue_book():
    book_id = int(request.form["book_id"])
    member_id = int(request.form["member_id"])

    conn = get_connection()
    book = conn.execute("SELECT * FROM books WHERE book_id = ?", (book_id,)).fetchone()

    if not book or book["available_copies"] < 1:
        flash("Selected book is not available.", "danger")
        conn.close()
        return redirect(url_for("issue_return"))

    issue_date = date.today()
    due_date = issue_date + timedelta(days=LOAN_PERIOD_DAYS)

    conn.execute(
        """INSERT INTO issue_records (book_id, member_id, issue_date, due_date, status)
           VALUES (?, ?, ?, ?, 'Issued')""",
        (book_id, member_id, issue_date.isoformat(), due_date.isoformat()),
    )
    conn.execute(
        "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?",
        (book_id,),
    )
    conn.commit()

    member = conn.execute(
        "SELECT * FROM members WHERE member_id = ?",
        (member_id,)
    ).fetchone()

    if member and member["email"]:
        subject = "Library Book Issued"
        body = (
            f"Hello {member['name']}\n\n"
            f"Your book has been issued successfully.\n\n"
            f"Book: {book['title']}\n"
            f"Issue Date: {issue_date}\n"
            f"Due Date: {due_date}\n\n"
            f"Please return it before the due date to avoid a fine.\n\n"
            f"Thank you.\n"
            f"Library Management System"
        )

        send_email(member["email"], subject, body)

        conn.close()
        flash(f'"{book["title"]}" issued. Due back on {due_date.isoformat()}.', "success")
        return redirect(url_for("issue_return"))
@app.route("/return/<int:issue_id>", methods=["POST"])
@login_required
def return_book(issue_id):
    conn = get_connection()
    record = conn.execute(
        "SELECT * FROM issue_records WHERE issue_id = ?", (issue_id,)
    ).fetchone()

    if not record or record["status"] != "Issued":
        flash("Invalid or already-returned issue record.", "danger")
        conn.close()
        return redirect(url_for("issue_return"))

    return_date = date.today().isoformat()
    fine = calculate_fine(record["due_date"], return_date)

    conn.execute(
        """UPDATE issue_records
           SET return_date = ?, fine_amount = ?, status = 'Returned'
           WHERE issue_id = ?""",
        (return_date, fine, issue_id),
    )
    conn.execute(
        "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = ?",
        (record["book_id"],),
    )
    conn.commit()
    conn.close()

    if fine > 0:
        flash(f"Book returned. Overdue fine: Rs. {fine}", "warning")
    else:
        flash("Book returned on time. No fine.", "success")
    return redirect(url_for("issue_return"))

# Reports

@app.route("/reports")
@login_required
def reports():
    conn = get_connection()

    overdue_rows = conn.execute(
        """
        SELECT ir.issue_id, b.title, m.name AS member_name, m.phone, ir.issue_date, ir.due_date
        FROM issue_records ir
        JOIN books b ON b.book_id = ir.book_id
        JOIN members m ON m.member_id = ir.member_id
        WHERE ir.status = 'Issued' AND ir.due_date < date('now')
        ORDER BY ir.due_date ASC
        """
    ).fetchall()
    overdue_list = [{**dict(r), "fine": calculate_fine(r["due_date"])} for r in overdue_rows]

    most_borrowed = conn.execute(
        """
        SELECT b.title, b.author, COUNT(ir.issue_id) AS times_issued
        FROM issue_records ir
        JOIN books b ON b.book_id = ir.book_id
        GROUP BY ir.book_id
        ORDER BY times_issued DESC
        LIMIT 5
        """
    ).fetchall()

    issued_today = conn.execute(
        """
        SELECT b.title, m.name AS member_name, ir.due_date
        FROM issue_records ir
        JOIN books b ON b.book_id = ir.book_id
        JOIN members m ON m.member_id = ir.member_id
        WHERE ir.issue_date = date('now')
        """
    ).fetchall()

    history = conn.execute(
        """
        SELECT b.title, m.name AS member_name, ir.issue_date, ir.due_date, ir.return_date,
               ir.fine_amount, ir.status
        FROM issue_records ir
        JOIN books b ON b.book_id = ir.book_id
        JOIN members m ON m.member_id = ir.member_id
        ORDER BY ir.issue_date DESC
        """
    ).fetchall()

    conn.close()
    return render_template(
        "reports.html",
        overdue_list=overdue_list,
        most_borrowed=most_borrowed,
        issued_today=issued_today,
        history=history,
    )

# Entry point

if __name__ == "__main__":
    init_db()  # creates + seeds library.db on first run only
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))