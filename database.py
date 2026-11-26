import sqlite3, os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expense.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT,
            date TEXT NOT NULL,
            description TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            UNIQUE(category, month, year)
        )
    """)
    # Insert sample data only once
    c.execute("SELECT COUNT(*) FROM transactions")
    if c.fetchone()[0] == 0:
        today = date.today()
        m = today.month
        y = today.year
        samples = [
            ("income",  "Salary",        25000, None,            f"{y}-{m:02d}-01", "Monthly salary"),
            ("income",  "Freelancing",    5000, None,            f"{y}-{m:02d}-05", "Web design project"),
            ("income",  "Business",       8000, None,            f"{y}-{m:02d}-10", "Consulting fees"),
            ("expense", "Food",           2000, "UPI",           f"{y}-{m:02d}-03", "Groceries & dining"),
            ("expense", "Travel",         1000, "Cash",          f"{y}-{m:02d}-07", "Commute & travel"),
            ("expense", "Shopping",       3000, "Card",          f"{y}-{m:02d}-08", "Clothes & accessories"),
            ("expense", "Education",      1500, "Bank Transfer", f"{y}-{m:02d}-12", "Online course"),
            ("expense", "Bills",          1200, "UPI",           f"{y}-{m:02d}-02", "Electricity & internet"),
            ("expense", "Entertainment",   800, "Card",          f"{y}-{m:02d}-14", "Movies & streaming"),
            ("expense", "Medical",         500, "Cash",          f"{y}-{m:02d}-09", "Pharmacy"),
        ]
        c.executemany(
            "INSERT INTO transactions (transaction_type,category,amount,payment_method,date,description) VALUES (?,?,?,?,?,?)",
            samples
        )
        # Sample budgets
        budgets = [
            ("Food",          3000, m, y),
            ("Shopping",      4000, m, y),
            ("Travel",        2000, m, y),
            ("Entertainment", 1500, m, y),
            ("Bills",         2000, m, y),
            ("Education",     2000, m, y),
            ("Medical",       1000, m, y),
        ]
        c.executemany(
            "INSERT OR IGNORE INTO budgets (category,monthly_limit,month,year) VALUES (?,?,?,?)",
            budgets
        )
    conn.commit()
    conn.close()
