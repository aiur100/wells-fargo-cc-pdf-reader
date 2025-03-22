import pdfplumber
import pandas as pd
import os
import sys
import re
from datetime import datetime

def is_valid_date(date_str):
    """Check if a string is in the format MM/DD"""
    if not date_str:
        return False
    
    pattern = r'^\d{2}/\d{2}$'
    return bool(re.match(pattern, date_str))

def clean_amount(amount_str):
    """Clean the amount string to a proper numeric format"""
    # Remove commas and other non-numeric characters except for decimals
    cleaned = re.sub(r'[^\d.-]', '', amount_str)
    return cleaned

def extract_expenses_from_pdf(pdf_path, filter_year=None):
    """
    Extract expenses from a PDF statement.
    If filter_year is provided, only include transactions from that year.
    """
    filename = os.path.basename(pdf_path)
    expenses = []
    parse = False
    current_year = datetime.now().year
    statement_date = None
    statement_year = None
    
    with pdfplumber.open(pdf_path) as pdf:
        # First, try to find the statement date to determine the year
        for page in pdf.pages[:1]:  # Only check first page for statement date
            text = page.extract_text()
            if text:
                # Look for statement date patterns
                date_match = re.search(r'Statement\s+Date:?\s+(\d{1,2}/\d{1,2}/(\d{2,4}))', text, re.IGNORECASE)
                if date_match:
                    statement_date = date_match.group(1)
                    statement_year = int(date_match.group(2))
                    if statement_year < 100:  # Handle 2-digit year
                        statement_year += 2000
        
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for line in lines:
                    # Try to detect statement period or billing cycle
                    if not statement_year and ('billing cycle' in line.lower() or 'statement period' in line.lower()):
                        date_matches = re.findall(r'(\d{1,2}/\d{1,2}/(\d{2,4}))', line)
                        if len(date_matches) >= 1:
                            statement_year = int(date_matches[0][1])
                            if statement_year < 100:  # Handle 2-digit year
                                statement_year += 2000
                    
                    # Start parsing when we see the transaction header
                    if not parse and 'Trans Post Reference' in line:
                        parse = True
                        continue
                    
                    # Skip payment entries
                    if 'PAYMENT THANK YOU' in line or 'AUTOMATIC PAYMENT' in line:
                        continue
                        
                    # Skip page header/footer lines
                    if re.search(r'Page\s+\d+\s+of\s+\d+', line, re.IGNORECASE) or 'account ending' in line.lower():
                        continue
                        
                    # Skip folio and check-in lines
                    if re.search(r'CHECK-IN|FOLIO|^\s*#', line):
                        continue
                        
                    # Special handling for PERIODIC*FINANCE lines
                    if 'PERIODIC*FINANCE' in line:
                        try:
                            # Extract the amount from the finance charge line
                            parts = line.split(' ')
                            amount = clean_amount(parts[-1])
                            
                            # Create an entry with "PERIODIC*FINANCE" as the date marker
                            # We'll replace this with the previous transaction's date later
                            if amount and float(amount) != 0:
                                expenses.append({
                                    'Date': 'FINANCE', 
                                    'Name': 'PERIODIC FINANCE CHARGE',
                                    'Amount': amount,
                                    'Year': statement_year  # Use statement year for finance charges
                                })
                        except (ValueError, IndexError):
                            continue
                        continue
                        
                    # Check if this is a valid transaction line that starts with a date
                    if parse and line and len(line.strip()) > 0:
                        parts = line.split(' ')
                        
                        # Check if the first part is a valid date format (MM/DD)
                        if len(parts) >= 3 and is_valid_date(parts[0]):
                            try:
                                date = parts[0]
                                
                                # Check if the second part also looks like a date
                                if is_valid_date(parts[1]):
                                    # This is a line with both transaction and posting date
                                    # Use the second date (posting date) and skip the first one
                                    name_parts = parts[2:-1]
                                    date = parts[1]  # Use posting date
                                else:
                                    # Regular line with just one date
                                    name_parts = parts[1:-1]
                                
                                # Extract name by joining all parts except the first (date) and last (amount)
                                name = ' '.join(name_parts)
                                
                                # Get the amount from the last part
                                amount = clean_amount(parts[-1])
                                
                                # Determine transaction year
                                transaction_year = statement_year
                                
                                # Handle December transactions in January statements (previous year)
                                if statement_year and date.startswith('12/') and '01_' in filename:
                                    transaction_year = statement_year - 1
                                    
                                # For 2025 file, only include transactions from 2024
                                if filter_year and transaction_year != filter_year:
                                    continue
                                
                                # Only add if we have all required fields and amount is numeric
                                if date and name and amount and float(amount) != 0:
                                    # Store the current date for potential finance charges
                                    current_date = date
                                    
                                    expenses.append({
                                        'Date': date, 
                                        'Name': name, 
                                        'Amount': amount,
                                        'Year': transaction_year
                                    })
                                    
                                    # Update any preceding finance charges with this date
                                    # This handles the case where finance charges appear before transactions
                                    for i in range(len(expenses) - 2, -1, -1):
                                        if expenses[i]['Date'] == 'FINANCE':
                                            expenses[i]['Date'] = current_date
                                            break
                            except (ValueError, IndexError):
                                # Skip lines that can't be parsed properly
                                continue
                    
                    # End parsing if we reach the end of transactions section
                    if parse and 'TOTAL PURCHASES' in line:
                        parse = False
    
    # Final pass to fix any remaining "FINANCE" dates
    last_real_date = None
    for expense in expenses:
        if expense['Date'] != 'FINANCE':
            last_real_date = expense['Date']
        elif last_real_date:
            expense['Date'] = last_real_date

    return expenses

def extract_expenses_from_directory(directory_path):
    all_expenses = []

    for filename in os.listdir(directory_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(directory_path, filename)
            try:
                # Apply year filter only for 2025 statements
                filter_year = None
                if '2025' in filename:
                    filter_year = 2024  # Only include 2024 transactions from 2025 statements
                
                expenses = extract_expenses_from_pdf(pdf_path, filter_year)
                all_expenses.extend(expenses)
                print(f"Processed {filename}: {len(expenses)} transactions extracted")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

    # Convert to DataFrame and sort by date
    if all_expenses:
        df = pd.DataFrame(all_expenses)
        
        # Deduplicate entries based on Date, Name, and Amount
        df = df.drop_duplicates(subset=['Date', 'Name', 'Amount'])
        
        # Create sorting date with year if available
        def create_sort_date(row):
            year = row.get('Year', datetime.now().year)
            try:
                return pd.to_datetime(f"{row['Date']}/{year}", format='%m/%d/%Y', errors='coerce')
            except:
                return pd.to_datetime(f"{row['Date']}/{datetime.now().year}", format='%m/%d/%Y', errors='coerce')
        
        df['SortDate'] = df.apply(create_sort_date, axis=1)
        df = df.sort_values('SortDate')
        
        # Remove temporary columns before saving
        if 'SortDate' in df.columns:
            df = df.drop('SortDate', axis=1)
        if 'Year' in df.columns:
            df = df.drop('Year', axis=1)
        
        return df
    else:
        return pd.DataFrame(columns=['Date', 'Name', 'Amount'])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: main.py <directory_path>")
        sys.exit(1)

    directory_path = sys.argv[1]
    expenses_df = extract_expenses_from_directory(directory_path)
    
    # Display summary
    if not expenses_df.empty:
        print(f"\nExtracted {len(expenses_df)} unique transactions")
        total_amount = expenses_df['Amount'].astype(float).sum()
        print(f"Total amount: ${total_amount:.2f}")
        
        # Save to CSV
        output_file = 'extracted_expenses.csv'
        expenses_df.to_csv(output_file, index=False)
        print(f"Data saved to {output_file}")
    else:
        print("No transactions found.")