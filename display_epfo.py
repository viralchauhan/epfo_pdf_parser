import json
from tabulate import tabulate
from collections import defaultdict

def display_epfo_console(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    def fmt(val):
        try:
            return f"₹{int(val):,}"
        except Exception:
            return str(val)

    # --- Member Info ---
    mi = data.get("member_info", {})
    print("\n" + "🧾 Member Information".center(100))
    print("=" * 100)
    print(f"👤 Member Name:         {mi.get('member_name', '-')}")
    print(f"🏢 Establishment:       {mi.get('establishment_name', '-')}")
    print(f"🆔 Establishment ID:    {mi.get('establishment_id', '-')}")
    print(f"🪪 Member ID:           {mi.get('member_id', '-')}")
    print(f"🎂 Date of Birth:       {mi.get('date_of_birth', '-')}")
    print(f"🧾 UAN:                 {mi.get('uan', '-')}")
    print("=" * 100)

    # --- Yearly Summary ---
    print("\n" + "📆 Yearly Contribution Summary".center(100))
    print("=" * 100)
    summary_rows = []
    for y in data.get("yearly_summaries", []):
        summary_rows.append([
            y["year"],
            y["transactions_count"],
            fmt(y["opening_total"]),
            fmt(y["contributions_total"]),
            fmt(y["interest_total"]),
            fmt(y["closing_total"])
        ])
    print(tabulate(
        summary_rows,
        headers=[
            "📅 Year",
            "🔢 Txns",
            "🔓 Opening",
            "💸 Contribution",
            "💰 Interest",
            "🔒 Closing"
        ],
        tablefmt="fancy_grid",
        colalign=("center", "right", "right", "right", "right", "right")
    ))

    # --- Final Balance ---
    fb = data.get("final_balances", {})
    print("\n" + f"💰 Final Balance Summary (As of {fb.get('as_of_year', 'Latest')})".center(100))
    print("=" * 100)
    print(f"👤 Employee Balance:   {fmt(fb.get('employee'))}")
    print(f"🏢 Employer Balance:   {fmt(fb.get('employer'))}")
    print(f"🧓 Pension Balance:    {fmt(fb.get('pension'))}")
    print(f"💰 Total Balance:      {fmt(fb.get('total'))}")
    print("=" * 100)

    # --- Metadata ---
    meta = data.get("extraction_metadata", {})
    print("\n" + "📦 Extraction Metadata".center(100))
    print("=" * 100)
    print(f"⏱️ Extracted At:           {meta.get('extracted_at')}")
    print(f"📂 Files Processed:        {meta.get('total_files_processed')}")
    print(f"📆 Years Covered:          {', '.join(meta.get('years_covered', []))}")
    print(f"🔢 Total Transactions:     {meta.get('total_transactions')}")
    print("=" * 100)

    # --- Monthly Transactions (Fancy Grid Per Year) ---
    print("\n" + "🧾 Monthly Transaction Details".center(100))
    print("=" * 100)
    transactions_by_year = defaultdict(list)
    for tx in data.get("all_transactions", []):
        transactions_by_year[tx["year"]].append([
            tx["month"],
            tx["date"],
            tx["description"],
            fmt(tx["wages"]),
            fmt(tx["basic_wages"]),
            fmt(tx["eps"]),
            fmt(tx["employee_contribution"]),
            fmt(tx["employer_contribution"]),
            fmt(tx["pension_contribution"]),
        ])

    for year in sorted(transactions_by_year):
        rows = transactions_by_year[year]
        
        # Function to remove ₹ and commas for summation
        def unfmt(val):
            return int(str(val).replace("₹", "").replace(",", "").strip())
        
        # Compute totals
        totals = [0] * 6  # For: Wages, Basic, EPS, Employee, Employer, Pension
        for row in rows:
            for i in range(6, 9):
                totals[i - 6] += unfmt(row[i])

        # Append a TOTAL row
        rows.append([
            "💰 TOTAL", "", "", 
            "","","",
            fmt(totals[0]), fmt(totals[1]), fmt(totals[2])
        ])
        print("\n" + f"📅 Year: {year}".center(100))
        print(tabulate(
            rows,
            headers = [
                "🗓️ Month",
                "📅 Txn Date",
                "📝 Description",
                "💵 Wages",
                "📊 Basic",
                "📈 EPS Wages",
                "👤 Employee",
                "🏢 Employer",
                "🏦 Pension"
            ],
            tablefmt="fancy_grid",
            colalign=("center",)*9
        ))
