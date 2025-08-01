# EPFO PDF Parser

A Python-based tool for parsing and analyzing Employee Provident Fund Organisation (EPFO) PDF passbooks. This tool helps in extracting, consolidating, and analyzing EPFO statement data across multiple years.

## Features

- 📄 Parse EPFO PDF passbooks across multiple years
- 💰 Extract detailed transaction history
- 📊 Generate consolidated reports in JSON and Excel formats
- 🔍 Detect active/inactive member status
- ✅ Balance continuity validation
- 📈 Summary statistics and analysis
- 🖨️ Console-based data display

## Installation

```bash
# Clone the repository
git clone https://github.com/viralchauhan/epfo_pdf_parser.git

# Navigate to the project directory
cd epfo_pdf_parser

# Install the package
pip install -e .
```

## Usage

### Basic Usage

```bash
epfoparser <member_folder_path> [output_directory]
```

Example:
```bash
epfoparser ./PF/MHBDR002889389/ ./output/
```

### Input Structure
Place your EPFO PDF files in a folder structure like:
```
PF/
└── MHBDR002889389/
    ├── MHBDR002889389_2021.pdf
    ├── MHBDR002889389_2022.pdf
    └── MHBDR002889389_2023.pdf
```

### Output Files

The tool generates:
1. JSON file (`*_consolidated.json`) containing:
   - Member information
   - Yearly summaries
   - Transaction details
   - Active/Inactive status
   - Final balances

2. Excel report (`*_report.xlsx`) with sheets for:
   - Member Info
   - Yearly Summary
   - All Transactions
   - Final Balances

## Key Features Explained

### Active Member Detection
- Members are marked as active if they have transactions within the last 3 months
- Active status is included in member_info section of the output
- Last transaction date is tracked for reference

### Balance Continuity Validation
- Automatically checks if closing balances match opening balances of subsequent years
- Validates employee, employer, and pension components separately
- Reports any mismatches found

### Data Processing
- Extracts member details (ID, name, DOB, UAN)
- Processes yearly transactions and balances
- Calculates contributions, interest, and total balances
- Maintains chronological transaction history

## Dependencies

- pdfplumber==0.7.6
- tabulate
- colorama
- reportlab

## Version History

- v1.0.2: Added active member detection
- v1.0.1: Added Excel report generation
- v1.0.0: Initial release with basic parsing capabilities
