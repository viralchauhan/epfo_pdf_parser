# Technical Documentation

## Project Structure

```
epfo_pdf_parser/
├── epfo_parser_final.py    # Main parser implementation
├── display_epfo.py         # Console display utilities
├── setup.py               # Package configuration
└── README.md             # Project documentation
```

## Core Components

### EPFOMultiYearParser Class

The main class that handles PDF parsing and data processing. Key methods:

#### process_member_folder(folder_path)
- Processes all PDF files in a member's folder
- Returns consolidated data dictionary

#### consolidate_data()
- Combines data from all years
- Calculates active member status
- Validates balance continuity

#### extract_transactions_from_text(text, year)
- Extracts individual transactions
- Processes wages, contributions, and dates

#### generate_excel_report(output_path)
- Creates multi-sheet Excel report
- Includes member info, yearly summary, and transactions

## Data Structures

### Consolidated Data Format
```json
{
    "member_info": {
        "member_id": "string",
        "member_name": "string",
        "establishment_id": "string",
        "establishment_name": "string",
        "date_of_birth": "string",
        "uan": "string",
        "is_active": boolean,
        "last_transaction_date": "string"
    },
    "yearly_summaries": [
        {
            "year": "string",
            "opening_employee": number,
            "opening_employer": number,
            "opening_pension": number,
            "closing_employee": number,
            "closing_employer": number,
            "closing_pension": number,
            "contributions_total": number,
            "interest_total": number
        }
    ],
    "all_transactions": [
        {
            "year": "string",
            "month": "string",
            "date": "string",
            "type": "string",
            "description": "string",
            "wages": number,
            "employee_contribution": number,
            "employer_contribution": number,
            "pension_contribution": number
        }
    ],
    "final_balances": {
        "employee": number,
        "employer": number,
        "pension": number,
        "total": number,
        "as_of_year": "string"
    }
}
```

## Active Member Detection Logic

The system determines active status based on:
1. Most recent transaction date
2. 3-month activity window
3. Transaction presence in the period

```python
# Pseudocode for active member detection
latest_date = most_recent_transaction_date
three_months_ago = today - 3_months
is_active = latest_date >= three_months_ago
```

## Error Handling

The parser implements comprehensive error handling for:
- Missing or corrupt PDF files
- Invalid date formats
- Balance mismatches
- PDF parsing errors

## Performance Considerations

- Processes PDFs sequentially to manage memory
- Caches extracted text to avoid repeated processing
- Uses efficient data structures for large datasets
