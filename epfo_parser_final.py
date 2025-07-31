#python epfo_parser_final.py "C:\Users\virch\CascadeProjects\epfo_pdf_parser\PF\MHBAN01266700000011961"  "C:\Users\virch\CascadeProjects\epfo_pdf_parser\output"
#epfoparser "C:\Users\virch\CascadeProjects\epfo_pdf_parser\PF\MHBAN01266700000011961"  "C:\Users\virch\CascadeProjects\epfo_pdf_parser\output"
import pdfplumber
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EPFOMultiYearParser:
    """Enhanced EPFO PDF parser for processing multiple years and generating consolidated reports."""
    
    def __init__(self):
        self.member_info = {}
        self.yearly_data = {}
        self.consolidated_data = {
            "member_info": {},
            "yearly_summaries": [],
            "all_transactions": [],
            "final_balances": {},
            "extraction_metadata": {
                "extracted_at": "",
                "total_files_processed": 0,
                "years_covered": [],
                "total_transactions": 0
            }
        }
    
    def parse_amount(self, value: Any) -> int:
        """Parse amount from various formats and return integer."""
        if not value:
            return 0
        try:
            # Convert to string and clean
            clean_val = str(value).replace(",", "").replace("₹", "").strip()
            # Handle negative values
            if clean_val.startswith("-"):
                return -int(clean_val[1:])
            return int(clean_val) if clean_val.isdigit() else 0
        except (ValueError, TypeError):
            return 0
    
    def clean_text(self, text: str) -> str:
        """Remove Hindi characters and clean up text."""
        if not text:
            return ""
        # Remove Hindi unicode characters
        cleaned = re.sub(r'[\u0900-\u097F]', '', text)
        # Remove extra spaces and special characters
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def extract_year_from_filename(self, filename: str) -> Optional[str]:
        """Extract year from filename like MHBAN20138650000010289_2021.pdf"""
        match = re.search(r'_(\d{4})\.pdf$', filename)
        return match.group(1) if match else None
    
    def extract_member_info_from_text(self, text: str) -> Dict[str, Any]:
        """Extract member information from EPFO PDF plain text."""
        info = {}

        # Establishment ID and Name (stop at newline or "Member ID")
        est_match = re.search(
            r'Establishment ID/Name\s+([A-Z]{5}\d{10})\s*/\s*(.*?)(?=\s+lnL; vkbZMh@uke|Member ID/Name|$)',
        text,
        re.DOTALL
    )
        if est_match:
            info["establishment_id"] = est_match.group(1).strip()
            info["establishment_name"] = est_match.group(2).strip()

    # Member ID and Name
        member_match = re.search(
            r'Member ID/Name\s+([A-Z]{5}\d{17})\s*/\s*([A-Z\s]+)', text
        )
        if member_match:
            info["member_id"] = member_match.group(1).strip()
            info["member_name"] = member_match.group(2).strip()

        # Date of Birth
        dob_match = re.search(r'Date of Birth\s+(\d{2}-\d{2}-\d{4})', text)
        if dob_match:
            info["date_of_birth"] = dob_match.group(1).strip()

        # UAN
        uan_match = re.search(r'UAN\s+(\d{12})', text)
        if uan_match:
            info["uan"] = uan_match.group(1).strip()

        return info

    
    def extract_balances_from_text(self, text: str, year: str) -> Dict[str, Any]:
        """Extract opening and closing balances from text."""
        balances = {
            "year": year,
            "opening_balance": {"employee": 0, "employer": 0, "pension": 0},
            "closing_balance": {"employee": 0, "employer": 0, "pension": 0},
            "contributions": {"employee": 0, "employer": 0, "pension": 0},
            "withdrawals": {"employee": 0, "employer": 0, "pension": 0},
            "interest": {"employee": 0, "employer": 0, "pension": 0}
        }
        
        # Extract Opening Balance
        ob_match = re.search(r'OB Int\. Updated upto\s+\d{2}/\d{2}/\d{4}\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)', text, re.DOTALL | re.IGNORECASE)
       
        
        if ob_match:
            balances["opening_balance"]["employee"] = self.parse_amount(ob_match.group(1))
            balances["opening_balance"]["employer"] = self.parse_amount(ob_match.group(2))
            balances["opening_balance"]["pension"] = self.parse_amount(ob_match.group(3))
        
        # Extract Closing Balance
        #cb_match = re.search(r'Closing Balance as on.*?(\d{1,3}(?:,\d{3})*|\d+)\s+(\d{1,3}(?:,\d{3})*|\d+)\s+(\d{1,3}(?:,\d{3})*|\d+)', text, re.DOTALL)
        cb_match = re.search( r'Closing Balance as on\s+\d{2}/\d{2}/\d{4}\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)', text, re.DOTALL | re.IGNORECASE)
        if cb_match:
            balances["closing_balance"]["employee"] = self.parse_amount(cb_match.group(1))
            balances["closing_balance"]["employer"] = self.parse_amount(cb_match.group(2))
            balances["closing_balance"]["pension"] = self.parse_amount(cb_match.group(3))
        
        # Extract Total Contributions
        contrib_match = re.search(r'Total Contributions for the year.*?(\d{1,3}(?:,\d{3})*|\d+)\s+(\d{1,3}(?:,\d{3})*|\d+)\s+(\d{1,3}(?:,\d{3})*|\d+)', text, re.DOTALL)
        if contrib_match:
            balances["contributions"]["employee"] = self.parse_amount(contrib_match.group(1))
            balances["contributions"]["employer"] = self.parse_amount(contrib_match.group(2))
            balances["contributions"]["pension"] = self.parse_amount(contrib_match.group(3))
        
        # Extract Interest
        int_match = re.search(
            r'(?<!OB\s)Int\. Updated upto\s+\d{2}/\d{2}/\d{4}\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)',
            text,
            re.DOTALL
        )
        if int_match:
            balances["interest"]["employee"] = self.parse_amount(int_match.group(1))
            balances["interest"]["employer"] = self.parse_amount(int_match.group(2))
            balances["interest"]["pension"] = self.parse_amount(int_match.group(3))
        
        return balances
    
    def extract_transactions_from_text(self, text: str, year: str) -> List[Dict[str, Any]]:
        """Extract individual transactions from text."""
        transactions = []
        #print(text)
        # Pattern to match transaction lines
        # Fixed regex: capturing 9 groups total
        transaction_pattern = re.compile(r'''
            ([A-Z][a-z]{2}-\d{4})              # Month-Year
            \s+(\d{2}-\d{2}-\d{4})             # Date
            \s+CR\s+
            (.*?)                              # Description (non-greedy)
            \s+
            (\d{6})                            # Due-Month code like 052022
            \s+
            ([\d,]+)                           # Wages
            \s+
            ([\d,]+)                           # Employee Contribution
            \s+
            ([\d,]+)                           # Pension Contribution
            \s+
            ([\d,]+)                           # Admin Charges
            \s+
            ([\d,]+)                           # EDLI
        ''', re.VERBOSE)

        matches = transaction_pattern.findall(text)
        #print(matches)
        for match in matches:
            transaction = {
                "year": year,
                "month": match[0],
                "date": match[1],
                "type": "CR",
                "description": match[2].strip(),
                "wages": self.parse_amount(match[3]),
                "basic_wages": self.parse_amount(match[4]),
                "eps": self.parse_amount(match[5]),
                "employee_contribution": self.parse_amount(match[6]),
                "employer_contribution": self.parse_amount(match[7]),
                "pension_contribution": self.parse_amount(match[8])
            }
            transactions.append(transaction)
        
        return transactions
    
    def process_single_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process a single PDF file and extract data."""
        #logger.info(f"Processing: {pdf_path}")
        
        year = self.extract_year_from_filename(os.path.basename(pdf_path))
        if not year:
            logger.warning(f"Could not extract year from filename: {pdf_path}")
            return {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract all text
                all_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        all_text += page_text + "\n"
                
                clean_text = self.clean_text(all_text)
                
                # Extract member info (only if not already extracted)
                if not self.member_info:
                    self.member_info = self.extract_member_info_from_text(clean_text)
                
                # Extract year-specific data
                year_data = {
                    "year": year,
                    "balances": self.extract_balances_from_text(clean_text, year),
                    "transactions": self.extract_transactions_from_text(clean_text, year),
                    "pdf_path": pdf_path
                }
                
                return year_data
                
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            return {}
    
    def process_member_folder(self, folder_path: str) -> Dict[str, Any]:
        """Process all PDF files in a member's folder."""
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            logger.error(f"Folder not found: {folder_path}")
            return {}
        
        # Find all PDF files
        pdf_files = list(folder_path.glob("*.pdf"))
        pdf_files.sort()  # Sort by filename (which includes year)
        
        if not pdf_files:
            logger.error(f"No PDF files found in: {folder_path}")
            return {}
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each PDF
        for pdf_file in pdf_files:
            year_data = self.process_single_pdf(str(pdf_file))
            if year_data and year_data.get("year"):
                self.yearly_data[year_data["year"]] = year_data
        
        # Consolidate data
        self.consolidate_data()
        
        return self.consolidated_data
    
    def consolidate_data(self):
        """Consolidate data from all years."""
        self.consolidated_data["member_info"] = self.member_info.copy()  # Create a copy to modify
        
        # Initialize is_active flag as False
        self.consolidated_data["member_info"]["is_active"] = False
        self.consolidated_data["member_info"]["last_transaction_date"] = None
        
        self.consolidated_data["extraction_metadata"]["extracted_at"] = datetime.now().isoformat()
        self.consolidated_data["extraction_metadata"]["total_files_processed"] = len(self.yearly_data)
        self.consolidated_data["extraction_metadata"]["years_covered"] = sorted(self.yearly_data.keys())
        
        # Create yearly summaries
        for year in sorted(self.yearly_data.keys()):
            year_data = self.yearly_data[year]
            balances = year_data["balances"]
            
            summary = {
                "year": year,
                "opening_employee": balances["opening_balance"]["employee"],
                "opening_employer": balances["opening_balance"]["employer"],
                "opening_pension": balances["opening_balance"]["pension"],
                "opening_total": sum(balances["opening_balance"].values()),
                "contributions_employee": balances["contributions"]["employee"],
                "contributions_employer": balances["contributions"]["employer"],
                "contributions_pension": balances["contributions"]["pension"],
                "contributions_total": sum(balances["contributions"].values()),
                "interest_employee": balances["interest"]["employee"],
                "interest_employer": balances["interest"]["employer"],
                "interest_pension": balances["interest"]["pension"],
                "interest_total": sum(balances["interest"].values()),
                "closing_employee": balances["closing_balance"]["employee"],
                "closing_employer": balances["closing_balance"]["employer"],
                "closing_pension": balances["closing_balance"]["pension"],
                "closing_total": sum(balances["closing_balance"].values()),
                "transactions_count": len(year_data["transactions"])
            }
            
            self.consolidated_data["yearly_summaries"].append(summary)
            self.consolidated_data["all_transactions"].extend(year_data["transactions"])
        
        # Check for active status based on recent transactions
        if self.consolidated_data["all_transactions"]:
            # Sort transactions by date
            all_transactions = sorted(
                self.consolidated_data["all_transactions"],
                key=lambda x: datetime.strptime(x["date"], "%d-%m-%Y"),
                reverse=True
            )
            
            # Get the most recent transaction date
            latest_transaction = all_transactions[0]
            latest_date = datetime.strptime(latest_transaction["date"], "%d-%m-%Y")
            
            # Calculate the date 3 months ago from today
            today = datetime.now()
            three_months_ago = today.replace(day=1)  # First day of current month
            three_months_ago = (three_months_ago.replace(month=three_months_ago.month - 2) 
                              if three_months_ago.month > 2 
                              else three_months_ago.replace(year=three_months_ago.year - 1, 
                                                         month=three_months_ago.month + 10))
            
            # Update member info with active status and last transaction date
            self.consolidated_data["member_info"]["last_transaction_date"] = latest_transaction["date"]
            self.consolidated_data["member_info"]["is_active"] = latest_date >= three_months_ago
            
        # Set final balances (from the latest year)
        if self.consolidated_data["yearly_summaries"]:
            latest_year = self.consolidated_data["yearly_summaries"][-1]
            self.consolidated_data["final_balances"] = {
                "employee": latest_year["closing_employee"],
                "employer": latest_year["closing_employer"],
                "pension": latest_year["closing_pension"],
                "total": latest_year["closing_total"],
                "as_of_year": latest_year["year"]
            }
        
        self.consolidated_data["extraction_metadata"]["total_transactions"] = len(self.consolidated_data["all_transactions"])
    
    def generate_excel_report(self, output_path: str):
        """Generate Excel report with multiple sheets (requires pandas and openpyxl)."""
        try:
            import pandas as pd
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Member Info Sheet
                member_df = pd.DataFrame([self.consolidated_data["member_info"]])
                member_df.to_excel(writer, sheet_name='Member Info', index=False)
                
                # Yearly Summary Sheet
                summary_df = pd.DataFrame(self.consolidated_data["yearly_summaries"])
                summary_df.to_excel(writer, sheet_name='Yearly Summary', index=False)
                
                # All Transactions Sheet
                if self.consolidated_data["all_transactions"]:
                    transactions_df = pd.DataFrame(self.consolidated_data["all_transactions"])
                    transactions_df.to_excel(writer, sheet_name='All Transactions', index=False)
                
                # Final Balances Sheet
                final_df = pd.DataFrame([self.consolidated_data["final_balances"]])
                final_df.to_excel(writer, sheet_name='Final Balances', index=False)
            
            #logger.info(f"Excel report generated: {output_path}")
            
        except ImportError:
            logger.warning("pandas/openpyxl not installed. Skipping Excel report generation.")
        except Exception as e:
            logger.error(f"Error generating Excel report: {e}")
    
    def generate_csv_reports(self, output_dir: str, member_id: str):
        """Generate CSV reports as alternative to Excel."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Member Info CSV
            member_csv = os.path.join(output_dir, f"{member_id}_member_info_{timestamp}.csv")
            with open(member_csv, 'w', newline='', encoding='utf-8') as f:
                if self.consolidated_data["member_info"]:
                    headers = list(self.consolidated_data["member_info"].keys())
                    values = list(self.consolidated_data["member_info"].values())
                    f.write(','.join(headers) + '\n')
                    f.write(','.join(str(v) for v in values) + '\n')
            
            # Yearly Summary CSV
            summary_csv = os.path.join(output_dir, f"{member_id}_yearly_summary_{timestamp}.csv")
            with open(summary_csv, 'w', newline='', encoding='utf-8') as f:
                if self.consolidated_data["yearly_summaries"]:
                    headers = list(self.consolidated_data["yearly_summaries"][0].keys())
                    f.write(','.join(headers) + '\n')
                    for summary in self.consolidated_data["yearly_summaries"]:
                        values = [str(summary.get(h, '')) for h in headers]
                        f.write(','.join(values) + '\n')
            
            # Transactions CSV
            if self.consolidated_data["all_transactions"]:
                trans_csv = os.path.join(output_dir, f"{member_id}_transactions_{timestamp}.csv")
                with open(trans_csv, 'w', newline='', encoding='utf-8') as f:
                    headers = list(self.consolidated_data["all_transactions"][0].keys())
                    f.write(','.join(headers) + '\n')
                    for trans in self.consolidated_data["all_transactions"]:
                        values = [str(trans.get(h, '')) for h in headers]
                        f.write(','.join(values) + '\n')
            
            logger.info(f"CSV reports generated in: {output_dir}")
            return [member_csv, summary_csv, trans_csv if self.consolidated_data["all_transactions"] else None]
            
        except Exception as e:
            logger.error(f"Error generating CSV reports: {e}")
            return []
    
    def print_summary_table(self):
        """Print a formatted summary table to console."""
        print("\n" + "="*120)
        print(f"{'EPFO CONSOLIDATED SUMMARY':^120}")
        print("="*120)
        
        # Member Info
        member = self.consolidated_data["member_info"]
        print(f"Member: {member.get('member_name', 'N/A')} | ID: {member.get('member_id', 'N/A')}")
        print(f"Establishment: {member.get('establishment_name', 'N/A')}")
        print(f"UAN: {member.get('uan', 'N/A')} | DOB: {member.get('date_of_birth', 'N/A')}")
        print("-"*120)
        
        # Yearly Summary Table
        print(f"{'Year':<6} {'Op.Emp':<10} {'Op.Empr':<10} {'Op.Pen':<8} {'Contrib':<10} {'Interest':<10} {'Cl.Emp':<10} {'Cl.Empr':<10} {'Cl.Pen':<8} {'Total':<12}")
        print("-"*120)
        
        for summary in self.consolidated_data["yearly_summaries"]:
            print(f"{summary['year']:<6} "
                  f"₹{summary['opening_employee']:>8,} "
                  f"₹{summary['opening_employer']:>8,} "
                  f"₹{summary['opening_pension']:>6,} "
                  f"₹{summary['contributions_total']:>8,} "
                  f"₹{summary['interest_total']:>8,} "
                  f"₹{summary['closing_employee']:>8,} "
                  f"₹{summary['closing_employer']:>8,} "
                  f"₹{summary['closing_pension']:>6,} "
                  f"₹{summary['closing_total']:>10,}")
        
        print("-"*120)
        final = self.consolidated_data["final_balances"]
        print(f"FINAL BALANCE (as of {final['as_of_year']}): ₹{final['total']:,}")
        print("="*120)
    
    def validate_balance_continuity(self) -> List[str]:
        """Validate that closing balance of one year matches opening balance of next year."""
        issues = []
        
        summaries = sorted(self.consolidated_data["yearly_summaries"], key=lambda x: x["year"])
        
        for i in range(len(summaries) - 1):
            current_year = summaries[i]
            next_year = summaries[i + 1]
            
            # Check Employee balance continuity
            if current_year["closing_employee"] != next_year["opening_employee"]:
                issues.append(f"Employee balance mismatch between {current_year['year']} and {next_year['year']}: "
                            f"Closing: ₹{current_year['closing_employee']:,}, Opening: ₹{next_year['opening_employee']:,}")
            
            # Check Employer balance continuity
            if current_year["closing_employer"] != next_year["opening_employer"]:
                issues.append(f"Employer balance mismatch between {current_year['year']} and {next_year['year']}: "
                            f"Closing: ₹{current_year['closing_employer']:,}, Opening: ₹{next_year['opening_employer']:,}")
            
            # Check Pension balance continuity
            if current_year["closing_pension"] != next_year["opening_pension"]:
                issues.append(f"Pension balance mismatch between {current_year['year']} and {next_year['year']}: "
                            f"Closing: ₹{current_year['closing_pension']:,}, Opening: ₹{next_year['opening_pension']:,}")
        
        return issues


def main_entry():
    """Main function to run the multi-year parser."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python epfo_multi_year_parser.py <member_folder_path> [output_directory]")
        print("Example: python epfo_multi_year_parser.py ./PF/MHBAN20138650000010289/ ./output/")
        sys.exit(1)
    
    member_folder = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(member_folder))
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(member_folder):
        print(f"Error: Member folder not found: {member_folder}")
        sys.exit(1)
    
    try:
        parser = EPFOMultiYearParser()
        result = parser.process_member_folder(member_folder)
        
        if not result:
            print("No data extracted. Please check the PDF files.")
            sys.exit(1)
        
        # Generate output filename based on member ID
        member_id = result["member_info"].get("member_id", "unknown")
        
        # Save JSON
        json_path = os.path.join(output_dir, f"{member_id}_consolidated.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Generate Excel report (if pandas is available)
        excel_path = os.path.join(output_dir, f"{member_id}_report.xlsx")
        parser.generate_excel_report(excel_path)
        
        # Generate CSV reports as fallback
        #csv_files = parser.generate_csv_reports(output_dir, member_id)
        
        # Print summary to console
        #parser.print_summary_table()
        
        # Validate balance continuity
        balance_issues = parser.validate_balance_continuity()
        
        print(f"\n✅ Processing completed successfully!")
        print(f"📁 JSON Output: {json_path}")
        if os.path.exists(excel_path):
            print(f"📊 Excel Report: {excel_path}")
        # if csv_files:
        #     print(f"📄 CSV Reports: {len([f for f in csv_files if f])} files generated")
        print(f"📈 Years Processed: {', '.join(result['extraction_metadata']['years_covered'])}")
        #print(f"💰 Final Total Balance: ₹{result['final_balances']['total']:,}")
        
        if balance_issues:
            print(f"\n⚠️  Balance Continuity Issues Found:")
            for issue in balance_issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ All balance continuity checks passed!")
        
        try:
            from display_epfo import display_epfo_console
            display_epfo_console(json_path)
        except Exception as e:
            print(f"[WARN] Could not display table: {e}")

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_entry()