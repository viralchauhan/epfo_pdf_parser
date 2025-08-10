import json
from tabulate import tabulate
from collections import defaultdict
from datetime import datetime

def display_epfo_console(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    def fmt(val):
        try:
            return f"₹{int(val):,}"
        except Exception:
            return str(val)

    def unfmt(val):
        """Remove ₹ and commas for summation"""
        if val == "-" or val is None:
            return 0
        try:
            return int(str(val).replace("₹", "").replace(",", "").replace("-", "").strip())
        except:
            return 0

    # --- Header ---
    print("\n" + "🏛️ EPFO ACCOUNT STATEMENT 🏛️".center(100))
    print("=" * 100)

    # --- Member Info ---
    mi = data.get("member_info", {})
    print("\n" + "🧾 Member Information".center(100))
    print("=" * 100)
    member_info_table = [
        ["👤 Member Name", mi.get('member_name', '-')],
        ["🏢 Establishment", mi.get('establishment_name', '-')],
        ["🆔 Establishment ID", mi.get('establishment_id', '-')],
        ["🪪 Member ID", mi.get('member_id', '-')],
        ["🎂 Date of Birth", mi.get('date_of_birth', '-')],
        ["🧾 UAN", mi.get('uan', '-')]
    ]
    print(tabulate(
        member_info_table,
        tablefmt="fancy_grid",
        colalign=("left", "left")
    ))

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
            fmt(y["withdrawals_total"]),
            fmt(y["interest_total"]),
            fmt(y["closing_total"])
        ])
    
    print(tabulate(
        summary_rows,
        headers=[
            "📅 Year",
            "🔢 Txns",
            "🔓 Opening",
            "💸 Contributions",
            "🏧 Withdrawals", 
            "💰 Interest",
            "🔒 Closing"
        ],
        tablefmt="fancy_grid",
        colalign=("center", "right", "right", "right", "right", "right", "right")
    ))

    # --- Total Withdrawals Summary (NEW SECTION) ---
    total_withdrawals = data.get("total_withdrawals", {})
    if total_withdrawals and total_withdrawals.get("total", 0) > 0:
        print("\n" + "🏧 Total Withdrawals Summary".center(100))
        print("=" * 100)
        withdrawal_rows = [
            ["👤 Employee Withdrawals", fmt(total_withdrawals.get("employee", 0))],
            ["🏢 Employer Withdrawals", fmt(total_withdrawals.get("employer", 0))],
            ["🧓 Pension Withdrawals", fmt(total_withdrawals.get("pension", 0))],
            ["💰 Total Withdrawals", fmt(total_withdrawals.get("total", 0))]
        ]
        print(tabulate(
            withdrawal_rows,
            headers=["Category", "Amount"],
            tablefmt="fancy_grid",
            colalign=("left", "right")
        ))

    # --- Final Balance ---
    fb = data.get("final_balances", {})
    print("\n" + f"💰 Final Balance Summary (As of {fb.get('year', 'Latest')})".center(100))
    print("=" * 100)
    balance_rows = [
        ["👤 Employee Balance", fmt(fb.get('employee', 0))],
        ["🏢 Employer Balance", fmt(fb.get('employer', 0))],
        ["🧓 Pension Balance", fmt(fb.get('pension', 0))],
        ["💰 Total Balance", fmt(fb.get('total', 0))]
    ]
    print(tabulate(
        balance_rows,
        headers=["Account Type", "Balance"],
        tablefmt="fancy_grid",
        colalign=("left", "right")
    ))

    # --- Account Summary Statistics (NEW SECTION) ---
    print("\n" + "📊 Account Statistics".center(100))
    print("=" * 100)
    
    # Calculate total contributions
    total_employee_contrib = sum(y.get("contributions_employee", 0) for y in data.get("yearly_summaries", []))
    total_employer_contrib = sum(y.get("contributions_employer", 0) for y in data.get("yearly_summaries", []))
    total_pension_contrib = sum(y.get("contributions_pension", 0) for y in data.get("yearly_summaries", []))
    total_interest = sum(y.get("interest_total", 0) for y in data.get("yearly_summaries", []))
    
    stats_rows = [
        ["💸 Total Employee Contributions", fmt(total_employee_contrib)],
        ["🏢 Total Employer Contributions", fmt(total_employer_contrib)],
        ["🧓 Total Pension Contributions", fmt(total_pension_contrib)],
        ["💰 Total Interest Earned", fmt(total_interest)],
        ["🏧 Total Withdrawals", fmt(total_withdrawals.get("total", 0))],
        ["📊 Net Balance", fmt(fb.get('total', 0))]
    ]
    print(tabulate(
        stats_rows,
        headers=["Statistic", "Amount"],
        tablefmt="fancy_grid",
        colalign=("left", "right")
    ))

    # --- Monthly Transactions (Enhanced) ---
    print("\n" + "🧾 Monthly Transaction Details".center(100))
    print("=" * 100)
    transactions_by_year = defaultdict(list)
    
    for tx in data.get("all_transactions", []):
        # Handle different transaction types
        if tx.get("type") == "CR":  # Credit transactions
            row = [
                tx.get("month", "-"),
                tx.get("date", "-"),
                tx.get("description", "-")[:40] + "..." if len(tx.get("description", "")) > 40 else tx.get("description", "-"),
                fmt(tx.get("wages", 0)),
                fmt(tx.get("basic_wages", 0)),
                fmt(tx.get("employee_contribution", 0)),
                fmt(tx.get("employer_contribution", 0)),
                fmt(tx.get("pension_contribution", 0)),
            ]
        elif tx.get("type") == "DR":  # Debit/Withdrawal transactions
            row = [
                tx.get("month", "-"),
                tx.get("date", "-"),
                tx.get("description", "-")[:40] + "..." if len(tx.get("description", "")) > 40 else tx.get("description", "-"),
                "-",  # No wages for withdrawals
                "-",  # No basic wages for withdrawals
                fmt(-tx.get("employee_withdrawal", 0)) if tx.get("employee_withdrawal") else "₹0",
                fmt(-tx.get("employer_withdrawal", 0)) if tx.get("employer_withdrawal") else "₹0",
                fmt(-tx.get("pension_withdrawal", 0)) if tx.get("pension_withdrawal") else "₹0",
            ]
        else:  # Unknown transaction type - handle gracefully
            row = [
                tx.get("month", "-"),
                tx.get("date", "-"),
                tx.get("description", "-")[:40] + "..." if len(tx.get("description", "")) > 40 else tx.get("description", "-"),
                fmt(tx.get("wages", 0)),
                fmt(tx.get("basic_wages", 0)),
                fmt(tx.get("employee_contribution", tx.get("employee_withdrawal", 0))),
                fmt(tx.get("employer_contribution", tx.get("employer_withdrawal", 0))),
                fmt(tx.get("pension_contribution", tx.get("pension_withdrawal", 0))),
            ]
        
        transactions_by_year[tx["year"]].append(row)

    for year in sorted(transactions_by_year.keys()):
        rows = transactions_by_year[year]
        
        # Compute totals (skip wages, basic_wages columns for totals)
        totals = [0, 0, 0]  # For: Employee, Employer, Pension
        for row in rows:
            # Only sum the last 3 columns (employee, employer, pension)
            for i in range(3):
                val = unfmt(row[5 + i])  # columns 5, 6, 7
                totals[i] += val

        # Append a TOTAL row
        rows.append([
            "💰 TOTAL", "", "", 
            "", "",  # Empty for wages, basic
            fmt(totals[0]), fmt(totals[1]), fmt(totals[2])
        ])
        
        print("\n" + f"📅 Year: {year}".center(100))
        print(tabulate(
            rows,
            headers = [
                "🗓️ Month",
                "📅 Date",
                "📝 Description",
                "💵 Wages",
                "📊 Basic Wages",
                "👤 Employee",
                "🏢 Employer",
                "🏦 Pension"
            ],
            tablefmt="fancy_grid",
            colalign=("center", "center", "left", "right", "right", "right", "right", "right")
        ))

    # --- Metadata ---
    meta = data.get("extraction_metadata", {})
    print("\n" + "📦 Extraction Metadata".center(100))
    print("=" * 100)
    metadata_rows = [
        ["⏱️ Extracted At", meta.get('extracted_at', '-')],
        ["📂 Files Processed", str(meta.get('total_files_processed', 0))],
        ["📆 Years Covered", ', '.join(meta.get('years_covered', []))],
        ["🔢 Total Transactions", str(meta.get('total_transactions', 0))],
        ["🏧 Withdrawal Transactions", str(meta.get('total_withdrawal_transactions', 0))]
    ]
    print(tabulate(
        metadata_rows,
        headers=["Metadata", "Value"],
        tablefmt="fancy_grid",
        colalign=("left", "left")
    ))
    
    print("\n" + "=" * 100)
    print("📄 Report Generated Successfully! 📄".center(100))
    print("=" * 100)

# Usage example:
# if __name__ == "__main__":
#     # display_epfo_console("your_file.json")
#     pass