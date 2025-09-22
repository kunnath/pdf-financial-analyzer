import tabula
import pandas as pd
import os
import re
import PyPDF2
from decimal import Decimal

def extract_amounts_from_text(text):
    """Extract monetary amounts from text using regex patterns"""
    # Patterns to match various currency formats
    patterns = [
        r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # $1,234.56
        r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*\$',  # 1,234.56$
        r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?',       # 1,234.56 (plain numbers)
        r'(?:USD|usd)\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # USD1,234.56
        r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|usd)',  # 1,234.56USD
    ]
    
    amounts = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Clean the match and convert to float
            clean_amount = re.sub(r'[^\d.,]', '', match)
            if clean_amount and '.' in clean_amount:
                try:
                    amount = float(clean_amount.replace(',', ''))
                    if amount > 0:  # Only positive amounts
                        amounts.append(amount)
                except ValueError:
                    continue
    
    return amounts

def read_pdf_text(pdf_path):
    """Extract text from all pages of PDF"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_by_page = []
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                text_by_page.append({
                    'page': page_num + 1,
                    'text': text
                })
            
            return text_by_page
    except Exception as e:
        print(f"Error reading PDF text: {e}")
        return []

# Check if input PDF exists
pdf_file = "Statement_1758526731293.pdf"
if not os.path.exists(pdf_file):
    print(f"Error: {pdf_file} not found in the current directory")
    exit(1)

print(f"Processing PDF: {pdf_file}")

try:
    # Method 1: Extract text and search for amounts
    print("\n=== EXTRACTING AMOUNTS FROM TEXT ===")
    pdf_text_pages = read_pdf_text(pdf_file)
    
    all_amounts = []
    for page_data in pdf_text_pages:
        page_num = page_data['page']
        text = page_data['text']
        amounts = extract_amounts_from_text(text)
        
        if amounts:
            print(f"\nPage {page_num} - Found {len(amounts)} amounts:")
            for amount in amounts:
                print(f"  ${amount:,.2f}")
                all_amounts.append({'page': page_num, 'amount': amount})
        else:
            print(f"\nPage {page_num} - No amounts found")
    
    # Method 2: Extract tables and look for amount columns
    print("\n=== EXTRACTING AMOUNTS FROM TABLES ===")
    dfs = tabula.read_pdf(pdf_file, pages='all', multiple_tables=True)
    
    table_amounts = []
    for i, df in enumerate(dfs):
        print(f"\nTable {i+1} structure:")
        print(f"Columns: {list(df.columns)}")
        print(f"Shape: {df.shape}")
        
        # Look for columns that might contain amounts
        amount_columns = []
        for col in df.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['amount', 'balance', 'total', 'sum', 'value', 'price', 'cost']):
                amount_columns.append(col)
        
        if amount_columns:
            print(f"Found potential amount columns: {amount_columns}")
            for col in amount_columns:
                # Try to extract numeric values from the column
                for idx, value in enumerate(df[col]):
                    if pd.notna(value):
                        # Convert to string and extract amounts
                        value_str = str(value)
                        amounts = extract_amounts_from_text(value_str)
                        for amount in amounts:
                            table_amounts.append({
                                'table': i+1,
                                'column': col,
                                'row': idx+1,
                                'amount': amount
                            })
        
        # Also check all cells for amounts
        for col in df.columns:
            for idx, value in enumerate(df[col]):
                if pd.notna(value):
                    value_str = str(value)
                    amounts = extract_amounts_from_text(value_str)
                    for amount in amounts:
                        if amount not in [ta['amount'] for ta in table_amounts]:  # Avoid duplicates
                            table_amounts.append({
                                'table': i+1,
                                'column': col,
                                'row': idx+1,
                                'amount': amount
                            })
    
    # Create summary
    print("\n=== SUMMARY ===")
    print(f"Total amounts found in text: {len(all_amounts)}")
    print(f"Total amounts found in tables: {len(table_amounts)}")
    
    if all_amounts:
        print(f"Text amounts range: ${min(amt['amount'] for amt in all_amounts):,.2f} - ${max(amt['amount'] for amt in all_amounts):,.2f}")
        print(f"Text amounts total: ${sum(amt['amount'] for amt in all_amounts):,.2f}")
    
    if table_amounts:
        print(f"Table amounts range: ${min(amt['amount'] for amt in table_amounts):,.2f} - ${max(amt['amount'] for amt in table_amounts):,.2f}")
        print(f"Table amounts total: ${sum(amt['amount'] for amt in table_amounts):,.2f}")
    
    # Save results to Excel
    with pd.ExcelWriter("amounts_extracted.xlsx", engine='openpyxl') as writer:
        # Save original tables
        for i, df in enumerate(dfs):
            sheet_name = f"Table_{i+1}"
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Save text amounts
        if all_amounts:
            text_amounts_df = pd.DataFrame(all_amounts)
            text_amounts_df.to_excel(writer, sheet_name="Text_Amounts", index=False)
        
        # Save table amounts
        if table_amounts:
            table_amounts_df = pd.DataFrame(table_amounts)
            table_amounts_df.to_excel(writer, sheet_name="Table_Amounts", index=False)
    
    print("\nResults saved to: amounts_extracted.xlsx")
    
except Exception as e:
    print(f"Error processing PDF: {e}")
    exit(1)