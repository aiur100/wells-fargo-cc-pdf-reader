# Wells Fargo Credit Card Statement Parser

Author: Christopher Hill (chrishill9 [at] gmail [dot] com)

This project parses Wells Fargo credit card statement PDFs and outputs a CSV file of the transaction data. I made this so that I can parse my credit card statements quickly. I download all the PDF's for the year to a directory, run this on it, and it creates a final CSV for me.  Lovely.

## Requirements

- Python 3.x
- `requirements.txt` file for dependencies

## Installation

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the script with the directory containing your PDF files as an argument:

```bash
python main.py <directory_path>
```

2. The script will generate `extracted_expenses.csv` with the parsed data.

## Notes

- The finance charge line in the output CSV will not have a specific date.