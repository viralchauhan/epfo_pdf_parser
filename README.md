# EPFO PDF Passbook Parser & Console Display Tool

A CLI tool for parsing and displaying Employees' Provident Fund Organization (EPFO) PDF passbooks. Extracts, consolidates, and displays member and transaction data from multiple years' worth of passbook PDFs, outputting results in JSON and human-readable tabular formats.

---

## Features
- **Parse multiple EPFO PDF passbooks** and extract:
  - Member information
  - Yearly summaries
  - All transactions (monthly, yearly)
  - Final balances
  - Extraction metadata
- **Consolidate data** from multiple years/files
- **Display results** in a well-formatted console table
- **Easy CLI usage** with a single command

---

## Installation

```bash
cd C:\Users\virch\CascadeProjects\epfo_pdf_parser
pip install -e .
```
This makes the `epfoparser` command available globally in your Python environment.

---

## Usage

**Parse EPFO PDFs and generate output:**
```bash
epfoparser "C:\Users\test\CascadeProjects\epfo_pdf_parser\PF\MHBAN0XXXXXXXX" "C:\Users\test\CascadeProjects\epfo_pdf_parser\output"
```
- The first argument is the directory containing your EPFO PDF files.
- The second argument is the output directory for the generated JSON and reports.

**Display the parsed data in the console:**
```python
from display_epfo import display_epfo_console
display_epfo_console("output/parsed_data.json")
```

---

## File Structure
- `epfo_parser_final.py`: Main parser and CLI entry point
- `display_epfo.py`: Console display utility
- `setup.py`: Packaging and installation
- `PF/`: Directory containing sample/input PDF files
- `output/`: Directory for parsed JSON and reports
- `readme.txt`: This file

---

## Requirements
- Python 3.7+
- Packages: `pdfplumber`, `tabulate`, `colorama`, `reportlab`

---

## Extending
- Add more PDF files to the `PF` directory and rerun the parser
- Customize `display_epfo.py` for different output formats or analytics

---

## Authors
- Your Name (update in `setup.py`)

---

## License
Specify your license here (MIT, Apache, etc.)
