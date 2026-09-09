# Library Book Manager 

web-based **Library Management System** developed using **Python (Flask)** and **SQLite**. The system helps librarians efficiently manage books, members, book issue/return operations, and automatically sends email notifications to members when a book is issued using **Brevo SMTP**.
## Features

- 📖 Add, Update and Delete Books
- 👤 Add, Update and Delete Members
- 📚 Issue Books
- 🔄 Return Books
- 📧 Automatic Email Notification using Brevo SMTP
- 📊 Dashboard with Library Statistics
- 🔍 Search Books and Members
- 🔐 Login Authentication
- 💾 SQLite Database Integration
- 📱 Responsive User Interface using Bootstrap

## Tech Stack

- **Backend:** Python + Flask
- **Database:** SQLite (a single file — no server/installation needed)
- **Frontend:** HTML + Jinja2 templates + Bootstrap 5 (via CDN) + a small amount of custom CSS
- **Charts:** Chart.js (via CDN) — fetches live data from two small JSON API endpoints in `app.py`
- **Brevo SMTP**

## Project Structure

```
library_manager/
├── app.py              # Flask routes + business logic + chart data API endpoints
├── database.py          # SQLite connection + DB initialization
├── schema.sql            # Table definitions + sample seed data (spread across recent months)
├── requirements.txt
├── templates/
│   ├── base.html          # Shared layout, navbar, Bootstrap + Chart.js CDN
│   ├── login.html
│   ├── dashboard.html      # Stat cards + the two charts
│   ├── books.html
│   ├── members.html
│   ├── issue_return.html
│   └── reports.html
└── static/
    └── style.css           # Small custom styling on top of Bootstrap
```

## How to Run

1. **Install Python 3** (3.9+) if you don't already have it.

2. **Create a virtual environment (recommended) and install Flask:**
   ```bash
   cd library_manager
   python3 -m venv venv
   source venv/bin/activate      # on Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   python app.py
   ```

4. **Open your browser** at: `http://127.0.0.1:5000`

5. **Login with the default admin account:**
   - Username: `username`
   - Password: `password`

The database (`library.db`) is created automatically on first run, pre-loaded with sample books, members, and issue records **spread across the last several months** — specifically so the two dashboard charts have real data to plot right away instead of showing up empty.

To reset the database back to the original sample data at any time:
```bash
python database.py
```
(This deletes and recreates `library.db` from `schema.sql`.)

## How the Charts Work

Two small JSON API endpoints in `app.py` compute the chart data server-side using SQL, and the dashboard page fetches them with plain JavaScript when it loads:

- **`GET /api/analytics/issues-per-month`** — runs a `strftime('%Y-%m', issue_date)` grouped count for each of the last 6 calendar months and returns `{labels: [...], counts: [...]}`
- **`GET /api/analytics/category-popularity`** — joins `issue_records` to `books` and groups by category to find the most-borrowed subjects, returns the top 8

`templates/dashboard.html` has a `<canvas>` element for each chart and a small `<script>` block (in the `scripts` block, loaded after Chart.js) that fetches each endpoint and renders a Chart.js bar/doughnut chart from the JSON response.

This is a good pattern to explain in your viva: the **backend only returns data** (via a lightweight JSON API), and the **frontend is responsible for rendering** — a basic but real example of separating a data layer from a presentation layer, which is exactly how larger production apps are structured.

## Database Design (ER Overview)

- **books** (book_id PK, title, author, publisher, isbn, category, total_copies, available_copies)
- **members** (member_id PK, name, email, phone, address, join_date)
- **issue_records** (issue_id PK, book_id FK, member_id FK, issue_date, due_date, return_date, fine_amount, status)
- **users** (user_id PK, username, password, role) — for admin login

Relationships: a member can have many issue records; a book can appear in many issue records over time (but only one active "Issued" record per copy at a time, tracked via `available_copies`).

## Business Logic Notes

- **Loan period:** 14 days from issue date (`LOAN_PERIOD_DAYS` in `app.py`)
- **Fine:** Rs. 5/day for every day past the due date (`FINE_PER_DAY` in `app.py`) — calculated at return time, or previewed live on the Issue/Return page for books still out
- **Deletion guards:** a book or member can't be deleted while they have an active ("Issued") record, to keep the data consistent
  
## Developed By

**Tripti Singh**
B.Tech Computer Science Engineering