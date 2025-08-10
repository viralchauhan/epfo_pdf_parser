# EPFO PDF Parser

A comprehensive Python-based solution for parsing, analyzing, and visualizing Employee Provident Fund Organisation (EPFO) PDF passbooks. This powerful tool enables users to extract, consolidate, and gain valuable insights from their EPF transaction history across multiple years with ease.

## 🌟 Key Features

### 🔍 Data Extraction
- Parse multiple EPFO PDF passbooks in one go
- Extract comprehensive transaction history
- Retrieve member and establishment details
- Process multiple years of data simultaneously

### 📊 Analysis & Reporting
- Generate detailed JSON reports
- Create human-readable console output
- Export to multiple formats (JSON, PDF, TXT)
- Visualize transaction patterns and trends

### 🛠️ Smart Processing
- Automatic detection of active/inactive status
- Balance validation across years
- Transaction categorization
- Error detection and reporting
- Support for various EPFO statement formats

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/viralchauhan/epfo_pdf_parser.git
   cd epfo_pdf_parser
   ```

2. **Install the package**
   ```bash
   # Install in development mode (recommended)
   pip install -e .
   
   # Or install directly from GitHub
   # pip install git+https://github.com/viralchauhan/epfo_pdf_parser.git
   ```

3. **Verify installation**
   ```bash
   epfoparser --version
   ```

## 🛠️ Usage

### Basic Command

```bash
epfoparser <input_directory> [output_directory]
```

### Command Line Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| `input_directory` | Path to directory containing EPFO PDFs | ✅ | - |
| `output_directory` | Directory to save output files | ❌ | `./output` |

### Example

```bash
# Basic usage with default output directory
epfoparser "./PF/MHBDR002889389/"

# Specify custom output directory
epfoparser "./PF/MHBDR002889389/" "./reports/"
```

### Input Structure

Organize your EPFO PDFs in this structure:

```
PF/
└── MHBDR002889389/                 # Member folder (UAN/ID)
    ├── MHBDR002889389_2021.pdf     # Year-wise statements
    ├── MHBDR002889389_2022.pdf
    └── MHBDR002889389_2023.pdf
```

### Output Files

The tool generates the following output files:

1. **JSON Output** (`consolidated_data.json`)
   - Complete structured data in JSON format
   - Includes all transactions, member info, and summaries
   - Ideal for further processing or analysis

2. **PDF Report** (`report.pdf`)
   - Formatted PDF document
   - Professional layout with tables and summaries
   - Ready for printing or sharing

3. **Text Summary** (`summary.txt`)
   - Human-readable text summary
   - Quick overview of key information
   - Easy to read in any text editor

### Viewing Results

The tool automatically displays parsed data in a formatted table. For programmatic access:

```python
from display_epfo import display_epfo_console

# Display parsed data in console
display_epfo_console("output/consolidated_data.json")
```

## 🔍 Feature Details

### Member Status Detection
- **Active/Inactive Status**: Automatically determines if a member is active based on recent transactions
- **Last Transaction Tracking**: Records the date of the most recent transaction
- **Contribution Analysis**: Identifies contribution patterns and gaps

### Financial Validation
- **Balance Continuity**: Ensures closing balances match opening balances of subsequent years
- **Component-wise Validation**: Validates employee, employer, and pension components separately
- **Anomaly Detection**: Flags unusual transactions or balance changes

### Data Processing Pipeline
1. **Extraction**
   - PDF text extraction with intelligent parsing
   - Handles various EPFO statement formats
   - Processes both digital and scanned PDFs (with OCR support)

2. **Transformation**
   - Standardizes transaction formats
   - Categorizes transaction types
   - Converts dates and amounts to consistent formats

3. **Enrichment**
   - Calculates running balances
   - Adds metadata and derived fields
   - Validates data integrity

4. **Output Generation**
   - Creates structured JSON data
   - Generates human-readable reports
   - Formats output for different use cases

## 📦 Dependencies

### Core Dependencies
- `pdfplumber>=0.7.6` - Advanced PDF text extraction
- `tabulate>=0.8.9` - Beautiful table formatting
- `colorama>=0.4.4` - Cross-platform colored output
- `reportlab>=3.6.8` - PDF report generation
- `typing-extensions>=4.0.0` - Type hints support

### Development Dependencies
- `pytest` - Testing framework
- `black` - Code formatting
- `mypy` - Static type checking
- `flake8` - Code linting

### Optional Dependencies
- `pytesseract` - OCR support for scanned PDFs
- `pandas` - Advanced data analysis

## 📜 Version History

### v1.1.0 (Upcoming)
- ✨ Enhanced PDF parsing accuracy
- 📊 Improved report generation
- 🐛 Various bug fixes and optimizations

### v1.0.2
- ✅ Added active member detection
- 📅 Improved date handling
- 🛠️ Better error messages

### v1.0.1
- 📊 Added Excel report generation
- 📈 Enhanced data validation
- 🖥️ Improved console output

### v1.0.0
- 🎉 Initial release
- 📄 Basic PDF parsing functionality
- 💾 JSON output support

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- EPFO for providing the passbook service
- The open-source community for amazing Python libraries
- All contributors who helped improve this tool
