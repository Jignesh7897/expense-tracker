from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import get_db, init_db
from datetime import date, datetime
import calendar, os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "expense_tracker_secret")

init_db()

# ── helpers ──────────────────────────────────────────────────────────────────

def _totals():
    conn = get_db()
    c = conn.cursor()
    inc  = c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='income'").fetchone()[0]
    exp  = c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='expense'").fetchone()[0]
    cnt  = c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    conn.close()
    return inc, exp, cnt

# ── dashboard ─────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    conn = get_db()
    c = conn.cursor()
    inc, exp, cnt = _totals()

    # monthly income vs expense (last 6 months)
    monthly = []
    today = date.today()
    for i in range(5, -1, -1):
        mo = (today.month - i - 1) % 12 + 1
        yr = today.year - ((today.month - i - 1) // 12)
        label = f"{calendar.month_abbr[mo]} {yr}"
        mi = c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='income'  AND strftime('%m,%Y',date)=?", (f"{mo:02d},{yr}",)).fetchone()[0]
        me = c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='expense' AND strftime('%m,%Y',date)=?", (f"{mo:02d},{yr}",)).fetchone()[0]
        monthly.append({"label": label, "income": mi, "expense": me})

    # category pie
    cat_rows = c.execute("SELECT category, SUM(amount) FROM transactions WHERE transaction_type='expense' GROUP BY category").fetchall()
    cat_data = [{"category": r[0], "amount": r[1]} for r in cat_rows]

    # recent 5
    recent = c.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC LIMIT 5").fetchall()

    # monthly summary (current month)
    m, y = today.month, today.year
    m_inc = c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='income'  AND strftime('%m,%Y',date)=?", (f"{m:02d},{y}",)).fetchone()[0]
    m_exp = c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='expense' AND strftime('%m,%Y',date)=?", (f"{m:02d},{y}",)).fetchone()[0]
    conn.close()

    return render_template("dashboard.html",
        total_income=inc, total_expense=exp, balance=inc-exp, tx_count=cnt,
        monthly=monthly, cat_data=cat_data, recent=recent,
        m_inc=m_inc, m_exp=m_exp, m_save=m_inc-m_exp,
        current_month=calendar.month_name[m])

# ── income ────────────────────────────────────────────────────────────────────

@app.route("/income")
def income():
    conn = get_db()
    rows = conn.execute("SELECT * FROM transactions WHERE transaction_type='income' ORDER BY date DESC, id DESC").fetchall()
    conn.close()
    return render_template("add_income.html", transactions=rows)

@app.route("/income/add", methods=["POST"])
def add_income():
    amt  = request.form.get("amount", "").strip()
    cat  = request.form.get("category", "").strip()
    dt   = request.form.get("date", "").strip()
    desc = request.form.get("description", "").strip()
    try:
        amt = float(amt)
        if amt <= 0: raise ValueError
    except ValueError:
        flash("Please enter a valid positive amount.", "danger"); return redirect(url_for("income"))
    if not cat or not dt:
        flash("Category and date are required.", "danger"); return redirect(url_for("income"))
    conn = get_db()
    conn.execute("INSERT INTO transactions (transaction_type,category,amount,payment_method,date,description) VALUES ('income',?,?,NULL,?,?)", (cat, amt, dt, desc))
    conn.commit(); conn.close()
    flash("Income added successfully!", "success")
    return redirect(url_for("income"))

@app.route("/income/edit/<int:tid>", methods=["GET","POST"])
def edit_income(tid):
    conn = get_db()
    if request.method == "POST":
        amt  = request.form.get("amount","").strip()
        cat  = request.form.get("category","").strip()
        dt   = request.form.get("date","").strip()
        desc = request.form.get("description","").strip()
        try:
            amt = float(amt)
            if amt <= 0: raise ValueError
        except ValueError:
            flash("Please enter a valid positive amount.", "danger")
            return redirect(url_for("edit_income", tid=tid))
        conn.execute("UPDATE transactions SET category=?,amount=?,date=?,description=? WHERE id=? AND transaction_type='income'", (cat, amt, dt, desc, tid))
        conn.commit(); conn.close()
        flash("Income updated successfully!", "success")
        return redirect(url_for("income"))
    row = conn.execute("SELECT * FROM transactions WHERE id=? AND transaction_type='income'", (tid,)).fetchone()
    conn.close()
    if not row: flash("Record not found.", "danger"); return redirect(url_for("income"))
    return render_template("edit_income.html", tx=row)

@app.route("/income/delete/<int:tid>", methods=["POST"])
def delete_income(tid):
    conn = get_db()
    conn.execute("DELETE FROM transactions WHERE id=? AND transaction_type='income'", (tid,))
    conn.commit(); conn.close()
    flash("Income deleted.", "success")
    return redirect(url_for("income"))

# ── expense ───────────────────────────────────────────────────────────────────

@app.route("/expense")
def expense():
    conn = get_db()
    rows = conn.execute("SELECT * FROM transactions WHERE transaction_type='expense' ORDER BY date DESC, id DESC").fetchall()
    conn.close()
    return render_template("add_expense.html", transactions=rows)

@app.route("/expense/add", methods=["POST"])
def add_expense():
    amt  = request.form.get("amount","").strip()
    cat  = request.form.get("category","").strip()
    pm   = request.form.get("payment_method","").strip()
    dt   = request.form.get("date","").strip()
    desc = request.form.get("description","").strip()
    try:
        amt = float(amt)
        if amt <= 0: raise ValueError
    except ValueError:
        flash("Please enter a valid positive amount.", "danger"); return redirect(url_for("expense"))
    if not cat or not dt:
        flash("Category and date are required.", "danger"); return redirect(url_for("expense"))
    conn = get_db()
    conn.execute("INSERT INTO transactions (transaction_type,category,amount,payment_method,date,description) VALUES ('expense',?,?,?,?,?)", (cat, amt, pm, dt, desc))
    conn.commit(); conn.close()
    flash("Expense added successfully!", "success")
    return redirect(url_for("expense"))

@app.route("/expense/edit/<int:tid>", methods=["GET","POST"])
def edit_expense(tid):
    conn = get_db()
    if request.method == "POST":
        amt  = request.form.get("amount","").strip()
        cat  = request.form.get("category","").strip()
        pm   = request.form.get("payment_method","").strip()
        dt   = request.form.get("date","").strip()
        desc = request.form.get("description","").strip()
        try:
            amt = float(amt)
            if amt <= 0: raise ValueError
        except ValueError:
            flash("Please enter a valid positive amount.", "danger")
            return redirect(url_for("edit_expense", tid=tid))
        conn.execute("UPDATE transactions SET category=?,amount=?,payment_method=?,date=?,description=? WHERE id=? AND transaction_type='expense'", (cat, amt, pm, dt, desc, tid))
        conn.commit(); conn.close()
        flash("Expense updated successfully!", "success")
        return redirect(url_for("expense"))
    row = conn.execute("SELECT * FROM transactions WHERE id=? AND transaction_type='expense'", (tid,)).fetchone()
    conn.close()
    if not row: flash("Record not found.", "danger"); return redirect(url_for("expense"))
    return render_template("edit_expense.html", tx=row)

@app.route("/expense/delete/<int:tid>", methods=["POST"])
def delete_expense(tid):
    conn = get_db()
    conn.execute("DELETE FROM transactions WHERE id=? AND transaction_type='expense'", (tid,))
    conn.commit(); conn.close()
    flash("Expense deleted.", "success")
    return redirect(url_for("expense"))

# ── transactions ──────────────────────────────────────────────────────────────

@app.route("/transactions")
def transactions():
    conn = get_db()
    q    = request.args.get("q","").strip()
    ttype = request.args.get("type","")
    cat  = request.args.get("category","")
    dfrom = request.args.get("date_from","")
    dto   = request.args.get("date_to","")

    sql  = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if q:
        sql += " AND (description LIKE ? OR category LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if ttype:
        sql += " AND transaction_type=?"; params.append(ttype)
    if cat:
        sql += " AND category=?"; params.append(cat)
    if dfrom:
        sql += " AND date>=?"; params.append(dfrom)
    if dto:
        sql += " AND date<=?"; params.append(dto)
    sql += " ORDER BY date DESC, id DESC"

    rows = conn.execute(sql, params).fetchall()
    cats = conn.execute("SELECT DISTINCT category FROM transactions ORDER BY category").fetchall()
    conn.close()
    return render_template("transactions.html", transactions=rows, categories=cats,
                           q=q, ttype=ttype, cat=cat, dfrom=dfrom, dto=dto)

@app.route("/transactions/delete/<int:tid>", methods=["POST"])
def delete_transaction(tid):
    conn = get_db()
    row = conn.execute("SELECT transaction_type FROM transactions WHERE id=?", (tid,)).fetchone()
    conn.execute("DELETE FROM transactions WHERE id=?", (tid,))
    conn.commit(); conn.close()
    flash("Transaction deleted.", "success")
    ref = request.referrer or url_for("transactions")
    return redirect(ref)

# ── budgets ───────────────────────────────────────────────────────────────────

@app.route("/budgets")
def budgets():
    today = date.today()
    m, y = today.month, today.year
    conn = get_db()
    brows = conn.execute("SELECT * FROM budgets WHERE month=? AND year=? ORDER BY category", (m, y)).fetchall()
    result = []
    for b in brows:
        spent = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='expense' AND category=? AND strftime('%m,%Y',date)=?",
            (b["category"], f"{m:02d},{y}")
        ).fetchone()[0]
        pct = round((spent / b["monthly_limit"]) * 100, 1) if b["monthly_limit"] else 0
        result.append({"id": b["id"], "category": b["category"], "limit": b["monthly_limit"], "spent": spent, "pct": pct})
    conn.close()
    expense_cats = ["Food","Travel","Shopping","Education","Medical","Bills","Entertainment","Other"]
    return render_template("budgets.html", budgets=result, month=calendar.month_name[m], year=y,
                           expense_cats=expense_cats, current_month=m, current_year=y)

@app.route("/budgets/add", methods=["POST"])
def add_budget():
    cat   = request.form.get("category","").strip()
    limit = request.form.get("monthly_limit","").strip()
    m     = request.form.get("month", date.today().month)
    y     = request.form.get("year",  date.today().year)
    try:
        limit = float(limit)
        if limit <= 0: raise ValueError
    except ValueError:
        flash("Enter a valid budget amount.", "danger"); return redirect(url_for("budgets"))
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO budgets (category,monthly_limit,month,year) VALUES (?,?,?,?)", (cat, limit, m, y))
    conn.commit(); conn.close()
    flash("Budget saved!", "success")
    return redirect(url_for("budgets"))

@app.route("/budgets/delete/<int:bid>", methods=["POST"])
def delete_budget(bid):
    conn = get_db()
    conn.execute("DELETE FROM budgets WHERE id=?", (bid,))
    conn.commit(); conn.close()
    flash("Budget removed.", "success")
    return redirect(url_for("budgets"))

# ── reports ───────────────────────────────────────────────────────────────────

@app.route("/reports")
def reports():
    today = date.today()
    sel_m = int(request.args.get("month", today.month))
    sel_y = int(request.args.get("year",  today.year))
    conn  = get_db()

    key = f"{sel_m:02d},{sel_y}"
    m_inc = conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='income'  AND strftime('%m,%Y',date)=?", (key,)).fetchone()[0]
    m_exp = conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='expense' AND strftime('%m,%Y',date)=?", (key,)).fetchone()[0]

    inc_by_cat = conn.execute("SELECT category,SUM(amount) FROM transactions WHERE transaction_type='income'  AND strftime('%m,%Y',date)=? GROUP BY category", (key,)).fetchall()
    exp_by_cat = conn.execute("SELECT category,SUM(amount) FROM transactions WHERE transaction_type='expense' AND strftime('%m,%Y',date)=? GROUP BY category", (key,)).fetchall()

    # 6-month trend
    trend = []
    for i in range(5, -1, -1):
        mo = (today.month - i - 1) % 12 + 1
        yr = today.year - ((today.month - i - 1) // 12)
        k  = f"{mo:02d},{yr}"
        ti = conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='income'  AND strftime('%m,%Y',date)=?", (k,)).fetchone()[0]
        te = conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE transaction_type='expense' AND strftime('%m,%Y',date)=?", (k,)).fetchone()[0]
        trend.append({"label": f"{calendar.month_abbr[mo]} {yr}", "income": ti, "expense": te})

    conn.close()
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years  = list(range(today.year - 2, today.year + 1))
    return render_template("reports.html",
        m_inc=m_inc, m_exp=m_exp, m_save=m_inc-m_exp,
        inc_by_cat=[{"category": r[0], "amount": r[1]} for r in inc_by_cat],
        exp_by_cat=[{"category": r[0], "amount": r[1]} for r in exp_by_cat],
        trend=trend, months=months, years=years,
        sel_m=sel_m, sel_y=sel_y,
        sel_month_name=calendar.month_name[sel_m])

# ── run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=False)
