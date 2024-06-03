import pdfplumber
import pandas as pd
import os
import sys

def extract_expenses_from_pdf(pdf_path):
    expenses = []
    parse = False

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for line in lines:
                    if not parse and 'Trans Post Reference' in line:
                        parse = True
                        continue

                    if parse and 'PAYMENT' not in line: 
                        parts = line.split(' ')
                        name = ' '.join(parts[1:-1])
                        amount = parts[-1]
                        date = parts[0]
                        expenses.append({'Date': date, 'Name': name, 'Amount': amount})
                        
                    if parse and 'PERIODIC*FINANCE CHARGE*' in line:
                        parse = False

    return expenses

def extract_expenses_from_directory(directory_path):
    all_expenses = []

    for filename in os.listdir(directory_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(directory_path, filename)
            expenses = extract_expenses_from_pdf(pdf_path)
            all_expenses.extend(expenses)

    df = pd.DataFrame(all_expenses)
    return df

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: main.py <directory_path>")
        sys.exit(1)

    directory_path = sys.argv[1]
    expenses_df = extract_expenses_from_directory(directory_path)
    print(expenses_df)

    # Save to CSV
    expenses_df.to_csv('extracted_expenses.csv', index=False)
