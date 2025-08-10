#python epfo_parser_final.py "C:\Users\virch\CascadeProjects\epfo_pdf_parser\PF\MHBAN01266700000011961"  "C:\Users\virch\CascadeProjects\epfo_pdf_parser\output"
#epfoparser "C:\Users\virch\CascadeProjects\epfo_pdf_parser\PF\MHBAN01266700000011961"  "C:\Users\virch\CascadeProjects\epfo_pdf_parser\output"
import pdfplumber
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)
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
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
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
            "total_withdrawals": {
                "employee": 0,
                "employer": 0,
                "pension": 0,
                "total": 0,
            },
            "extraction_metadata": {
                "extracted_at": "",
                "total_files_processed": 0,
                "years_covered": [],
                "total_transactions": 0,
                "total_withdrawal_transactions": 0,
            },
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
        cleaned = re.sub(r"[\u0900-\u097F]", "", text)
        # Remove extra spaces and special characters
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def extract_year_from_filename(self, filename: str) -> Optional[str]:
        """Extract year from filename like MHBAN20138650000010289_2021.pdf"""
        match = re.search(r"_(\d{4})\.pdf$", filename)
        return match.group(1) if match else None

    def extract_member_info_from_text(self, text: str) -> Dict[str, Any]:
        """Extract member information from EPFO PDF plain text."""
        info = {}

        # Establishment ID and Name (stop at newline or "Member ID")
        est_match = re.search(
            r"Establishment ID/Name\s+([A-Z]{5}\d{10})\s*/\s*(.*?)(?=\s+lnL; vkbZMh@uke|Member ID/Name|$)",
            text,
            re.DOTALL,
        )
        if est_match:
            info["establishment_id"] = est_match.group(1).strip()
            info["establishment_name"] = est_match.group(2).strip()

        # Member ID and Name
        member_match = re.search(
            r"Member ID/Name\s+([A-Z]{5}\d{17})\s*/\s*([A-Z\s]+)", text
        )
        if member_match:
            info["member_id"] = member_match.group(1).strip()
            info["member_name"] = member_match.group(2).strip()

        # Date of Birth
        dob_match = re.search(r"Date of Birth\s+(\d{2}-\d{2}-\d{4})", text)
        if dob_match:
            info["date_of_birth"] = dob_match.group(1).strip()

        # UAN
        uan_match = re.search(r"UAN\s+(\d{12})", text)
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
            "interest": {"employee": 0, "employer": 0, "pension": 0},
        }

        # Extract Opening Balance
        ob_match = re.search(
            r"OB Int\. Updated upto\s+\d{2}/\d{2}/\d{4}\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)",
            text,
            re.DOTALL | re.IGNORECASE,
        )

        if ob_match:
            balances["opening_balance"]["employee"] = self.parse_amount(
                ob_match.group(1)
            )
            balances["opening_balance"]["employer"] = self.parse_amount(
                ob_match.group(2)
            )
            balances["opening_balance"]["pension"] = self.parse_amount(
                ob_match.group(3)
            )

        # Extract Closing Balance
        cb_match = re.search(
            r"Closing Balance as on\s+\d{2}/\d{2}/\d{4}\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if cb_match:
            balances["closing_balance"]["employee"] = self.parse_amount(
                cb_match.group(1)
            )
            balances["closing_balance"]["employer"] = self.parse_amount(
                cb_match.group(2)
            )
            balances["closing_balance"]["pension"] = self.parse_amount(
                cb_match.group(3)
            )

        # Extract Total Contributions
        contrib_match = re.search(
            r"Total Contributions for the year.*?(\d{1,3}(?:,\d{3})*|\d+)\s+(\d{1,3}(?:,\d{3})*|\d+)\s+(\d{1,3}(?:,\d{3})*|\d+)",
            text,
            re.DOTALL,
        )
        if contrib_match:
            balances["contributions"]["employee"] = self.parse_amount(
                contrib_match.group(1)
            )
            balances["contributions"]["employer"] = self.parse_amount(
                contrib_match.group(2)
            )
            balances["contributions"]["pension"] = self.parse_amount(
                contrib_match.group(3)
            )

        # Extract Total Withdrawals for the year
        withdrawal_match = re.search(
            r"Total Withdrawals for the year.*?(\d{1,3}(?:,\d{3})*|\d+)\s+(\d{1,3}(?:,\d{3})*|\d+)\s+(\d{1,3}(?:,\d{3})*|\d+)",
            text,
            re.DOTALL,
        )
        if withdrawal_match:
            balances["withdrawals"]["employee"] = self.parse_amount(
                withdrawal_match.group(1)
            )
            balances["withdrawals"]["employer"] = self.parse_amount(
                withdrawal_match.group(2)
            )
            balances["withdrawals"]["pension"] = self.parse_amount(
                withdrawal_match.group(3)
            )

        # Extract Interest
        int_match = re.search(
            r"(?<!OB\s)Int\. Updated upto\s+\d{2}/\d{2}/\d{4}\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)",
            text,
            re.DOTALL,
        )
        if int_match:
            balances["interest"]["employee"] = self.parse_amount(int_match.group(1))
            balances["interest"]["employer"] = self.parse_amount(int_match.group(2))
            balances["interest"]["pension"] = self.parse_amount(int_match.group(3))

        return balances

    def extract_transactions_from_text(self, text: str, year: str) -> List[Dict[str, Any]]:
        """Extract transactions from EPFO passbook text with detailed debug logging."""
        transactions = []

        # print("\n--- DEBUG: Starting transaction extraction ---")
        # print(f"Input year: {year}")
        # print(f"Total raw characters: {len(text)}")
        # print(f"Total raw lines: {len(text.splitlines())}")

        # Normalize spaces to avoid broken patterns due to extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Step 1: Consolidate transactions line-by-line
        consolidated_lines = []
        current_transaction = ""
        lines = re.split(r'(?=[A-Za-z]{3}-\d{4}\s+\d{2}-\d{2}-\d{4})', text)

        # print("\n--- DEBUG: Consolidating lines ---")
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            if re.match(r'^[A-Za-z]{3}-\d{4}\s+\d{2}-\d{2}-\d{4}', line, re.IGNORECASE):
                if current_transaction:
                    consolidated_lines.append(current_transaction.strip())
                    #print(f"  >> Saved transaction [{len(consolidated_lines)-1}]: {current_transaction.strip()}")
                current_transaction = line
                #print(f"  New transaction start at split segment {idx}")
            else:
                if current_transaction:
                    current_transaction += " " + line
                    #print(f"    Continuation: {line}")

        if current_transaction:
            consolidated_lines.append(current_transaction.strip())
            #print(f"  >> Saved final transaction [{len(consolidated_lines)-1}]: {current_transaction.strip()}")

        #print(f"\n--- DEBUG: Total consolidated transactions: {len(consolidated_lines)} ---")

        # Step 3: Pattern matching
        for line_num, line in enumerate(consolidated_lines):
            self.extract_transfer_transactions(line, year, transactions)
            if not re.match(r'^[A-Za-z]{3}-\d{4}\s+\d{2}-\d{2}-\d{4}', line, re.IGNORECASE):
                continue

            # --- Transfer Pattern ---
            transfer_pattern = re.compile(r'''
                ([A-Za-z]{3}-\d{4})\s+               
                (\d{2}-\d{2}-\d{4})\s+               
                CR\s+                                  
                (TRANSFER\s+IN\s+-\s+.*?)\s+          
                (\d+(?:,\d{3})*|0)\s+                   
                (\d+(?:,\d{3})*|0)\s+                   
                (\d+(?:,\d{3})*|0)\s+                   
                (\d+(?:,\d{3})*|0)\s+                   
                (\d+(?:,\d{3})*|0)                      
            ''', re.IGNORECASE | re.VERBOSE)

            transfer_match = transfer_pattern.search(line)
            if transfer_match:
                desc = transfer_match.group(3).strip()
                old_member_id = None
                old_id_match = re.search(r'Old\s+Member\s+Id\s*[:-]?\s*([A-Z0-9]+)', desc, re.IGNORECASE)
                if old_id_match:
                    old_member_id = old_id_match.group(1)

                transactions.append({
                    "year": year,
                    "month": transfer_match.group(1),
                    "date": transfer_match.group(2),
                    "type": "CR",
                    "description": desc,
                    "old_member_id": old_member_id,
                    "wages": self.parse_amount(transfer_match.group(4)),
                    "basic_wages": self.parse_amount(transfer_match.group(5)),
                    "employee_contribution": self.parse_amount(transfer_match.group(6)),
                    "employer_contribution": self.parse_amount(transfer_match.group(7)),
                    "pension_contribution": self.parse_amount(transfer_match.group(8))
                })
                continue
            #else:
                #print("  ✗ TRANSFER pattern did not match.")

            # --- Regular CR Pattern ---
            cr_pattern = re.compile(r'''
                ([A-Za-z]{3}-\d{4})\s+               
                (\d{2}-\d{2}-\d{4})\s+               
                CR\s+                                  
                (?!TRANSFER)                           
                (.*?)\s+                               
                (\d{6})\s+                             
                ([\d,]+)\s+                            
                ([\d,]+)\s+                            
                ([\d,]+)\s+                            
                ([\d,]+)\s+                            
                ([\d,]+)                               
            ''', re.IGNORECASE | re.VERBOSE)

            cr_match = cr_pattern.search(line)
            if cr_match:
                transactions.append({
                    "year": year,
                    "month": cr_match.group(1),
                    "date": cr_match.group(2),
                    "type": "CR",
                    "description": cr_match.group(3).strip(),
                    "due_month_code": cr_match.group(4),
                    "wages": self.parse_amount(cr_match.group(5)),
                    "basic_wages": self.parse_amount(cr_match.group(6)),
                    "employee_contribution": self.parse_amount(cr_match.group(7)),
                    "employer_contribution": self.parse_amount(cr_match.group(8)),
                    "pension_contribution": self.parse_amount(cr_match.group(9))
                })
                continue
            #else:
                #print("  ✗ Regular CR pattern did not match.")

            # --- DR Pattern ---
            dr_pattern = re.compile(r'''
                ([A-Za-z]{3}-\d{4})\s+               
                (\d{2}-\d{2}-\d{4})\s+               
                DR\s+                                  
                (.*?)\s+                               
                (\d+(?:,\d{3})*)\s+                   
                (\d+(?:,\d{3})*)\s+                   
                ([\d,]+)\s+                            
                ([\d,]+)\s+                            
                ([\d,]+)                               
            ''', re.IGNORECASE | re.VERBOSE)

            dr_match = dr_pattern.search(line)
            if dr_match:
                transactions.append({
                    "year": year,
                    "month": dr_match.group(1),
                    "date": dr_match.group(2),
                    "type": "DR",
                    "description": dr_match.group(3).strip(),
                    "employee_withdrawal": self.parse_amount(dr_match.group(6)),
                    "employer_withdrawal": self.parse_amount(dr_match.group(7)),
                    "pension_withdrawal": self.parse_amount(dr_match.group(8)),
                    "total_withdrawal": (
                        self.parse_amount(dr_match.group(6)) +
                        self.parse_amount(dr_match.group(7)) +
                        self.parse_amount(dr_match.group(8))
                    )
                })
                continue
            #else:
                #print("  ✗ DR pattern did not match.")

        #print(f"\n--- DEBUG: Total transactions found: {len(transactions)} ---")
        return transactions

    # ///

    def extract_transfer_transactions(self, line: str, year: str, transactions: list):
        #"""Extract transfer transactions with flexible pattern matching."""
        #print(f"***************************************************")
        #print(f"Full line: {line}")
        #print(f"***************************************************")

        # Pattern 1: Standard TRANSFER IN format
        transfer_in_pattern = re.compile(r'''
            ([A-Za-z]{3}-\d{4})\s+                # Month-Year
            (\d{2}-\d{2}-\d{4})\s+                # Date
            CR\s+                                 # Credit Type
            (TRANSFER\s+IN\s+-\s+.*?)\s+          # Description
            (\d+(?:,\d{3})*|0)\s+                 # Wages
            (\d+(?:,\d{3})*|0)\s+                 # Basic Wages
            (\d+(?:,\d{3})*|0)\s+                 # Employee Contribution
            (\d+(?:,\d{3})*|0)\s+                 # Employer Contribution
            (\d+(?:,\d{3})*|0)                    # Pension Contribution
        ''', re.IGNORECASE | re.VERBOSE)

        # Pattern 2: OFFICE format with Old Member ID at the end
        office_transfer_pattern = re.compile(r'''
            ([A-Za-z]{3}-\d{4})\s+                # Month-Year
            (\d{2}-\d{2}-\d{4})\s+                # Date
            CR\s+                                 # Credit Type
            (OFFICE\([^)]*Old\s+Member\s+Id[^)]*\s+) # Description part before amounts
            (\d+(?:,\d{3})*|0)\s+                 # Wages
            (\d+(?:,\d{3})*|0)\s+                 # Basic Wages
            (\d+(?:,\d{3})*|0)\s+                 # Employee Contribution
            (\d+(?:,\d{3})*|0)\s+                 # Employer Contribution
            (\d+(?:,\d{3})*|0)\s+                 # Pension Contribution
            :([A-Z0-9]+)\s*\)                     # Old Member ID at the end
        ''', re.IGNORECASE | re.VERBOSE)

        # Pattern 3: Generic transfer pattern (catches other variations)
        generic_transfer_pattern = re.compile(r'''
            ([A-Za-z]{3}-\d{4})\s+                # Month-Year
            (\d{2}-\d{2}-\d{4})\s+                # Date
            CR\s+                                 # Credit Type
            (.*?(?:TRANSFER|OFFICE|Old\s+Member).*?)\s+ # Any description with transfer keywords
            (\d+(?:,\d{3})*|0)\s+                 # Wages
            (\d+(?:,\d{3})*|0)\s+                 # Basic Wages
            (\d+(?:,\d{3})*|0)\s+                 # Employee Contribution
            (\d+(?:,\d{3})*|0)\s+                 # Employer Contribution
            (\d+(?:,\d{3})*|0)                    # Pension Contribution
            (?:.*?:([A-Z0-9]+).*?)?               # Optional Old Member ID anywhere
        ''', re.IGNORECASE | re.VERBOSE)

        # Try Pattern 1: Standard TRANSFER IN
        transfer_match = transfer_in_pattern.search(line)
        if transfer_match:
            #print(f"  ✓ STANDARD TRANSFER IN match: {transfer_match.groups()}")
            desc = transfer_match.group(3).strip()

            # Extract Old Member ID from description
            old_member_id = None
            old_id_patterns = [
                r'Old\s+Member\s+Id\s*[:-]?\s*([A-Z0-9]+)',
                r'Old\s+A/c\s+No\s*[:-]?\s*([A-Z0-9]+)',
                r'Previous\s+Member\s+Id\s*[:-]?\s*([A-Z0-9]+)'
            ]
            
            for pattern in old_id_patterns:
                old_id_match = re.search(pattern, desc, re.IGNORECASE)
                if old_id_match:
                    old_member_id = old_id_match.group(1)
                    break

            # if old_member_id:
            #     print(f"  >> Extracted Old Member ID: {old_member_id}")
            # else:
            #     print("  >> No Old Member ID found in description")

            transactions.append({
                "year": year,
                "month": transfer_match.group(1),
                "date": transfer_match.group(2),
                "type": "CR",
                "description": desc,
                "old_member_id": old_member_id,
                "wages": self.parse_amount(transfer_match.group(4)),
                "basic_wages": self.parse_amount(transfer_match.group(5)),
                "employee_contribution": self.parse_amount(transfer_match.group(6)),
                "employer_contribution": self.parse_amount(transfer_match.group(7)),
                "pension_contribution": self.parse_amount(transfer_match.group(8))
            })
            return True

        # Try Pattern 2: OFFICE format with ID at end
        office_match = office_transfer_pattern.search(line)
        if office_match:
            #print(f"  ✓ OFFICE TRANSFER match: {office_match.groups()}")
            desc = office_match.group(3).strip()
            old_member_id = office_match.group(9)  # ID captured at the end
            
            #print(f"  >> Extracted Old Member ID from end: {old_member_id}")

            transactions.append({
                "year": year,
                "month": office_match.group(1),
                "date": office_match.group(2),
                "type": "CR",
                "description": desc + f":{old_member_id})",  # Complete description
                "old_member_id": old_member_id,
                "wages": self.parse_amount(office_match.group(4)),
                "basic_wages": self.parse_amount(office_match.group(5)),
                "employee_contribution": self.parse_amount(office_match.group(6)),
                "employer_contribution": self.parse_amount(office_match.group(7)),
                "pension_contribution": self.parse_amount(office_match.group(8))
            })
            return True

        # Try Pattern 3: Generic transfer pattern
        generic_match = generic_transfer_pattern.search(line)
        if generic_match and any(keyword in line.upper() for keyword in ['TRANSFER', 'OFFICE', 'OLD MEMBER']):
            #print(f"  ✓ GENERIC TRANSFER match: {generic_match.groups()}")
            desc = generic_match.group(3).strip()
            old_member_id = generic_match.group(9)  # Optional captured ID
            
            # If ID not captured by pattern, try extracting from entire line
            if not old_member_id:
                id_patterns = [
                    r':([A-Z0-9]{20,})',  # Colon followed by long alphanumeric
                    r'([A-Z]{2}[A-Z0-9]{18,})',  # State code + long alphanumeric
                    r'Old\s+Member\s+Id[^:]*:\s*([A-Z0-9]+)',
                ]
                
                for pattern in id_patterns:
                    id_match = re.search(pattern, line, re.IGNORECASE)
                    if id_match:
                        old_member_id = id_match.group(1)
                        break

            #print(f"  >> Extracted Old Member ID: {old_member_id if old_member_id else 'None'}")

            transactions.append({
                "year": year,
                "month": generic_match.group(1),
                "date": generic_match.group(2),
                "type": "CR",
                "description": desc,
                "old_member_id": old_member_id,
                "wages": self.parse_amount(generic_match.group(4)),
                "basic_wages": self.parse_amount(generic_match.group(5)),
                "employee_contribution": self.parse_amount(generic_match.group(6)),
                "employer_contribution": self.parse_amount(generic_match.group(7)),
                "pension_contribution": self.parse_amount(generic_match.group(8))
            })
            return True

        #print("  ✗ No TRANSFER pattern matched.")
        return False
    # ///


    def process_single_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process a single PDF file and extract data."""

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
                    "transactions": self.extract_transactions_from_text(
                        clean_text, year
                    ),
                    "pdf_path": pdf_path,
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

        #logger.info(f"Found {len(pdf_files)} PDF files to process")

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
        self.consolidated_data["member_info"] = self.member_info
        self.consolidated_data["extraction_metadata"]["extracted_at"] = (
            datetime.now().isoformat()
        )
        self.consolidated_data["extraction_metadata"]["total_files_processed"] = len(
            self.yearly_data
        )
        self.consolidated_data["extraction_metadata"]["years_covered"] = sorted(
            self.yearly_data.keys()
        )

        # Initialize total withdrawals tracking
        total_withdrawals = {"employee": 0, "employer": 0, "pension": 0, "total": 0}
        total_withdrawal_transactions = 0

        # Create yearly summaries
        for year in sorted(self.yearly_data.keys()):
            year_data = self.yearly_data[year]
            balances = year_data["balances"]

            # Calculate withdrawals for this year
            year_withdrawals = {"employee": 0, "employer": 0, "pension": 0, "total": 0}

            # Get withdrawals from balance summary
            year_withdrawals["employee"] += balances["withdrawals"]["employee"]
            year_withdrawals["employer"] += balances["withdrawals"]["employer"]
            year_withdrawals["pension"] += balances["withdrawals"]["pension"]

            # Count DR transactions for withdrawal count
            for trans in year_data["transactions"]:
                if trans.get("type") == "DR":
                    total_withdrawal_transactions += 1

            year_withdrawals["total"] = (
                year_withdrawals["employee"]
                + year_withdrawals["employer"]
                + year_withdrawals["pension"]
            )

            # Add to total withdrawals
            total_withdrawals["employee"] += year_withdrawals["employee"]
            total_withdrawals["employer"] += year_withdrawals["employer"]
            total_withdrawals["pension"] += year_withdrawals["pension"]
            total_withdrawals["total"] += year_withdrawals["total"]

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
                "withdrawals_employee": year_withdrawals["employee"],
                "withdrawals_employer": year_withdrawals["employer"],
                "withdrawals_pension": year_withdrawals["pension"],
                "withdrawals_total": year_withdrawals["total"],
                "interest_employee": balances["interest"]["employee"],
                "interest_employer": balances["interest"]["employer"],
                "interest_pension": balances["interest"]["pension"],
                "interest_total": sum(balances["interest"].values()),
                "closing_employee": balances["closing_balance"]["employee"],
                "closing_employer": balances["closing_balance"]["employer"],
                "closing_pension": balances["closing_balance"]["pension"],
                "closing_total": sum(balances["closing_balance"].values()),
                "transactions_count": len(year_data["transactions"]),
            }

            self.consolidated_data["yearly_summaries"].append(summary)
            self.consolidated_data["all_transactions"].extend(year_data["transactions"])

        # Set consolidated withdrawal totals
        self.consolidated_data["total_withdrawals"] = total_withdrawals
        self.consolidated_data["extraction_metadata"][
            "total_withdrawal_transactions"
        ] = total_withdrawal_transactions

        # Set final balances (from the latest year)
        if self.consolidated_data["yearly_summaries"]:
            latest_year = self.consolidated_data["yearly_summaries"][-1]
            self.consolidated_data["final_balances"] = {
                "employee": latest_year["closing_employee"],
                "employer": latest_year["closing_employer"],
                "pension": latest_year["closing_pension"],
                "total": latest_year["closing_total"],
                "year": latest_year["year"],
            }

        self.consolidated_data["extraction_metadata"]["total_transactions"] = len(
            self.consolidated_data["all_transactions"]
        )

    def generate_excel_report(self, output_path: str):
        """Generate Excel report with multiple sheets (requires pandas and openpyxl)."""
        try:
            import pandas as pd

            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                # Member Info Sheet
                member_df = pd.DataFrame([self.consolidated_data["member_info"]])
                member_df.to_excel(writer, sheet_name="Member Info", index=False)

                # Yearly Summary Sheet
                summary_df = pd.DataFrame(self.consolidated_data["yearly_summaries"])
                summary_df.to_excel(writer, sheet_name="Yearly Summary", index=False)

                # All Transactions Sheet
                if self.consolidated_data["all_transactions"]:
                    transactions_df = pd.DataFrame(
                        self.consolidated_data["all_transactions"]
                    )
                    transactions_df.to_excel(
                        writer, sheet_name="All Transactions", index=False
                    )

                # Final Balances Sheet
                final_df = pd.DataFrame([self.consolidated_data["final_balances"]])
                final_df.to_excel(writer, sheet_name="Final Balances", index=False)

                # Total Withdrawals Sheet
                withdrawals_df = pd.DataFrame(
                    [self.consolidated_data["total_withdrawals"]]
                )
                withdrawals_df.to_excel(
                    writer, sheet_name="Total Withdrawals", index=False
                )

        except ImportError:
            logger.warning(
                "pandas/openpyxl not installed. Skipping Excel report generation."
            )
        except Exception as e:
            logger.error(f"Error generating Excel report: {e}")

    def generate_csv_reports(self, output_dir: str, member_id: str):
        """Generate CSV reports as alternative to Excel."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Member Info CSV
            member_csv = os.path.join(
                output_dir, f"{member_id}_member_info_{timestamp}.csv"
            )
            with open(member_csv, "w", newline="", encoding="utf-8") as f:
                if self.consolidated_data["member_info"]:
                    headers = list(self.consolidated_data["member_info"].keys())
                    values = list(self.consolidated_data["member_info"].values())
                    f.write(",".join(headers) + "\n")
                    f.write(",".join(str(v) for v in values) + "\n")

            # Yearly Summary CSV
            summary_csv = os.path.join(
                output_dir, f"{member_id}_yearly_summary_{timestamp}.csv"
            )
            with open(summary_csv, "w", newline="", encoding="utf-8") as f:
                if self.consolidated_data["yearly_summaries"]:
                    headers = list(self.consolidated_data["yearly_summaries"][0].keys())
                    f.write(",".join(headers) + "\n")
                    for summary in self.consolidated_data["yearly_summaries"]:
                        values = [str(summary.get(h, "")) for h in headers]
                        f.write(",".join(values) + "\n")

            # Transactions CSV
            transactions_csv = None
            if self.consolidated_data["all_transactions"]:
                transactions_csv = os.path.join(
                    output_dir, f"{member_id}_transactions_{timestamp}.csv"
                )
                with open(transactions_csv, "w", newline="", encoding="utf-8") as f:
                    headers = list(self.consolidated_data["all_transactions"][0].keys())
                    f.write(",".join(headers) + "\n")
                    for trans in self.consolidated_data["all_transactions"]:
                        values = [str(trans.get(h, "")) for h in headers]
                        f.write(",".join(values) + "\n")

            # Total Withdrawals CSV
            withdrawals_csv = os.path.join(
                output_dir, f"{member_id}_total_withdrawals_{timestamp}.csv"
            )
            with open(withdrawals_csv, "w", newline="", encoding="utf-8") as f:
                headers = list(self.consolidated_data["total_withdrawals"].keys())
                values = list(self.consolidated_data["total_withdrawals"].values())
                f.write(",".join(headers) + "\n")
                f.write(",".join(str(v) for v in values) + "\n")

            logger.info(f"CSV reports generated in: {output_dir}")
            return [member_csv, summary_csv, transactions_csv, withdrawals_csv]

        except Exception as e:
            logger.error(f"Error generating CSV reports: {e}")
            return []

    

    def validate_balance_continuity(self) -> List[str]:
        """Validate that closing balance of one year matches opening balance of next year."""
        issues = []

        summaries = sorted(
            self.consolidated_data["yearly_summaries"], key=lambda x: x["year"]
        )

        for i in range(len(summaries) - 1):
            current_year = summaries[i]
            next_year = summaries[i + 1]

            # Check Employee balance continuity
            if current_year["closing_employee"] != next_year["opening_employee"]:
                issues.append(
                    f"Employee balance mismatch between {current_year['year']} and {next_year['year']}: "
                    f"Closing: ₹{current_year['closing_employee']:,}, Opening: ₹{next_year['opening_employee']:,}"
                )

            # Check Employer balance continuity
            if current_year["closing_employer"] != next_year["opening_employer"]:
                issues.append(
                    f"Employer balance mismatch between {current_year['year']} and {next_year['year']}: "
                    f"Closing: ₹{current_year['closing_employer']:,}, Opening: ₹{next_year['opening_employer']:,}"
                )

            # Check Pension balance continuity
            if current_year["closing_pension"] != next_year["opening_pension"]:
                issues.append(
                    f"Pension balance mismatch between {current_year['year']} and {next_year['year']}: "
                    f"Closing: ₹{current_year['closing_pension']:,}, Opening: ₹{next_year['opening_pension']:,}"
                )

        return issues


def main_entry():
    """Main function to run the multi-year parser."""
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python epfo_multi_year_parser.py <member_folder_path> [output_directory]"
        )
        print(
            "Example: python epfo_multi_year_parser.py ./PF/MHBAN20138650000010289/ ./output/"
        )
        sys.exit(1)

    member_folder = sys.argv[1]
    output_dir = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.path.dirname(os.path.abspath(member_folder))
    )

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

        # Print summary to console
        #parser.print_summary_table()

        # Validate balance continuity
        balance_issues = parser.validate_balance_continuity()

        print(f"\n✅ Processing completed successfully!")
        print(f"📁 JSON Output: {json_path}")
        if os.path.exists(excel_path):
            print(f"📊 Excel Report: {excel_path}")
        print(
            f"📈 Years Processed: {', '.join(result['extraction_metadata']['years_covered'])}"
        )
        print(f"💰 Final Total Balance: ₹{result['final_balances']['total']:,}")

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
