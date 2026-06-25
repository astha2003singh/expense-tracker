"""PDF parser for bank statements."""

import re
from pathlib import Path
from sqlite3 import Connection

import pdfplumber

from expense_tracker.database import add_expense
from expense_tracker.date_utils import parse_date

def extract_expenses_from_pdf(pdf_path: str | Path, conn: Connection) -> int:
    """
    Extract expenses from a bank statement PDF and save to database.
    Returns the number of expenses added.
    """
    # Common date formats at the start of a line
    # e.g., 01/12/2023, 2023-12-01, 12-01-2023, 01 Jan 2023
    date_pattern = r'^\s*(\d{1,4}[-/\.\s][a-zA-Z0-9]{2,3}[-/\.\s]\d{2,4}|\d{2}[-/\.\s]\d{2}[-/\.\s]\d{4}|\d{4}[-/\.\s]\d{2}[-/\.\s]\d{2})'
    
    # Amount at the end of the line
    # e.g. 1,234.56 or 1234.56
    amount_pattern = r'([\d,]+\.\d{2})\s*(Cr|Dr)?\s*$'
    
    count = 0
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
                
            for line in text.split('\n'):
                date_match = re.search(date_pattern, line)
                if not date_match:
                    continue
                    
                amount_match = re.search(amount_pattern, line)
                if not amount_match:
                    continue
                    
                date_str = date_match.group(1).strip()
                amount_str = amount_match.group(1).replace(',', '')
                cr_dr = amount_match.group(2)
                
                # In many bank statements, Credit (Cr) is income, Debit (Dr) or unmarked is expense.
                if cr_dr and cr_dr.lower() == 'cr':
                    continue
                if ' credit ' in line.lower():
                    continue
                    
                try:
                    amount = float(amount_str)
                    if amount <= 0:
                        continue
                        
                    desc_start = date_match.end()
                    desc_end = amount_match.start()
                    description = line[desc_start:desc_end].strip()
                    
                    # Clean up description
                    description = re.sub(r'\s+', ' ', description)
                    
                    try:
                        expense_date = parse_date(date_str)
                    except ValueError:
                        continue # skip invalid dates
                        
                    add_expense(
                        conn,
                        amount=amount,
                        category="Other", # Default category for imports
                        note=description,
                        date=expense_date
                    )
                    count += 1
                except ValueError:
                    pass
                    
    return count
