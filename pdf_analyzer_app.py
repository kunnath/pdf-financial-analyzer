import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import tabula
import PyPDF2
import re
import os
import tempfile
from decimal import Decimal
import numpy as np
from datetime import datetime
import io
import requests

# Currency exchange rates (you can update these or fetch from an API)
CURRENCY_RATES = {
    'INR': 1.0,  # Base currency (Indian Rupees)
    'USD': 0.012,  # 1 INR = 0.012 USD (approximate)
    'EUR': 0.011,  # 1 INR = 0.011 EUR (approximate)
    'GBP': 0.0095,  # 1 INR = 0.0095 GBP (approximate)
    'JPY': 1.8,    # 1 INR = 1.8 JPY (approximate)
    'CAD': 0.016,  # 1 INR = 0.016 CAD (approximate)
    'AUD': 0.018,  # 1 INR = 0.018 AUD (approximate)
    'CNY': 0.086,  # 1 INR = 0.086 CNY (approximate)
}

CURRENCY_SYMBOLS = {
    'INR': '₹',
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'JPY': '¥',
    'CAD': 'C$',
    'AUD': 'A$',
    'CNY': '¥',
}

def get_exchange_rates():
    """Fetch real-time exchange rates (optional enhancement)"""
    try:
        # You can use a free API like exchangerate-api.com
        # For now, we'll use static rates
        return CURRENCY_RATES
    except:
        return CURRENCY_RATES

def convert_currency(amount, from_currency='INR', to_currency='INR'):
    """Convert amount from one currency to another"""
    if from_currency == to_currency:
        return amount
    
    rates = get_exchange_rates()
    
    # Convert to base currency (INR) first, then to target currency
    if from_currency != 'INR':
        amount_in_inr = amount / rates[from_currency]
    else:
        amount_in_inr = amount
    
    # Convert from INR to target currency
    converted_amount = amount_in_inr * rates[to_currency]
    return converted_amount

def format_currency(amount, currency='INR'):
    """Format amount with appropriate currency symbol"""
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    
    if currency == 'JPY':
        return f"{symbol}{amount:,.0f}"  # No decimals for JPY
    else:
        return f"{symbol}{amount:,.2f}"

def extract_amounts_from_text(text, source_currency='INR'):
    """Extract monetary amounts from text using regex patterns"""
    patterns = [
        r'₹\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # ₹1,234.56 (Rupees)
        r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*₹',  # 1,234.56₹
        r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # $1,234.56
        r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*\$',  # 1,234.56$
        r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?',       # 1,234.56 (plain numbers)
        r'(?:USD|usd|INR|inr|EUR|eur)\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # Currency prefix
        r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|usd|INR|inr|EUR|eur)',  # Currency suffix
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
                        amounts.append({
                            'original_amount': amount,
                            'source_currency': source_currency,
                            'raw_text': match
                        })
                except ValueError:
                    continue
            elif clean_amount and clean_amount.isdigit():
                try:
                    amount = float(clean_amount)
                    if amount > 0:
                        amounts.append({
                            'original_amount': amount,
                            'source_currency': source_currency,
                            'raw_text': match
                        })
                except ValueError:
                    continue
    
    return amounts

def read_pdf_text(pdf_file):
    """Extract text from all pages of PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
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
        st.error(f"Error reading PDF text: {e}")
        return []

def classify_transaction_type(df):
    """Classify transactions as Credit (CR) or Debit (DR)"""
    transactions = []
    
    for idx, row in df.iterrows():
        transaction = {}
        
        # Look for amount column
        amount_col = None
        for col in df.columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['amount', 'balance', 'value']) or col_str.replace('.', '').replace(',', '').isdigit():
                amount_col = col
                break
        
        # Look for type column (explicitly CR/DR)
        type_col = None
        for col in df.columns:
            col_str = str(col).upper()
            if col_str in ['DR', 'CR', 'TYPE'] or any(keyword in col_str for keyword in ['DEBIT', 'CREDIT']):
                type_col = col
                break
        
        # Extract transaction details
        if amount_col and pd.notna(row[amount_col]):
            try:
                amount_str = str(row[amount_col])
                # Extract numeric amount
                amount_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d{2})?)', amount_str)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    
                    # Determine transaction type
                    trans_type = 'Unknown'
                    
                    # Check explicit type column first
                    if type_col and pd.notna(row[type_col]):
                        type_str = str(row[type_col]).upper().strip()
                        if type_str == 'CR' or 'CREDIT' in type_str:
                            trans_type = 'CR'
                        elif type_str == 'DR' or 'DEBIT' in type_str:
                            trans_type = 'DR'
                    
                    # If no explicit type column, try to infer from description or other columns
                    if trans_type == 'Unknown':
                        row_text = ' '.join([str(val) for val in row if pd.notna(val)]).upper()
                        if any(keyword in row_text for keyword in ['CR', 'CREDIT', 'DEPOSIT', 'RECEIVED', 'IMPS', 'NEFT', 'RTGS']):
                            trans_type = 'CR'
                        elif any(keyword in row_text for keyword in ['DR', 'DEBIT', 'WITHDRAWAL', 'PAID', 'UPI', 'ATM', 'POS']):
                            trans_type = 'DR'
                    
                    transaction = {
                        'amount': amount,
                        'type': trans_type,
                        'description': str(row.get(df.columns[1], '') if len(df.columns) > 1 else ''),
                        'date': str(row.get(df.columns[0], '') if len(df.columns) > 0 else ''),
                        'raw_data': dict(row)
                    }
                    transactions.append(transaction)
            except Exception as e:
                continue
    
    return transactions

def analyze_cr_dr_data(transactions):
    """Analyze Credit and Debit transactions"""
    cr_transactions = [t for t in transactions if t['type'] == 'CR']
    dr_transactions = [t for t in transactions if t['type'] == 'DR']
    unknown_transactions = [t for t in transactions if t['type'] == 'Unknown']
    
    analysis = {
        'credit': {
            'count': len(cr_transactions),
            'total': sum(t['amount'] for t in cr_transactions),
            'average': sum(t['amount'] for t in cr_transactions) / len(cr_transactions) if cr_transactions else 0,
            'max': max(t['amount'] for t in cr_transactions) if cr_transactions else 0,
            'min': min(t['amount'] for t in cr_transactions) if cr_transactions else 0,
            'transactions': cr_transactions
        },
        'debit': {
            'count': len(dr_transactions),
            'total': sum(t['amount'] for t in dr_transactions),
            'average': sum(t['amount'] for t in dr_transactions) / len(dr_transactions) if dr_transactions else 0,
            'max': max(t['amount'] for t in dr_transactions) if dr_transactions else 0,
            'min': min(t['amount'] for t in dr_transactions) if dr_transactions else 0,
            'transactions': dr_transactions
        },
        'unknown': {
            'count': len(unknown_transactions),
            'total': sum(t['amount'] for t in unknown_transactions),
            'transactions': unknown_transactions
        }
    }
    
    return analysis

def extract_table_amounts_with_types(pdf_file):
    """Extract amounts from PDF tables with transaction types"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_file.getvalue())
            tmp_path = tmp_file.name
        
        dfs = tabula.read_pdf(tmp_path, pages='all', multiple_tables=True)
        
        all_transactions = []
        table_amounts = []
        
        for i, df in enumerate(dfs):
            # Classify transactions in this table
            transactions = classify_transaction_type(df)
            all_transactions.extend(transactions)
            
            # Also extract basic amounts (for backward compatibility)
            for col in df.columns:
                col_str = str(col).lower()
                if any(keyword in col_str for keyword in ['amount', 'balance', 'total', 'sum', 'value', 'price', 'cost']):
                    for idx, value in enumerate(df[col]):
                        if pd.notna(value):
                            value_str = str(value)
                            amounts = extract_amounts_from_text(value_str, 'INR')
                            for amount_data in amounts:
                                table_amounts.append({
                                    'table': i+1,
                                    'column': col,
                                    'row': idx+1,
                                    'amount': amount_data['original_amount']
                                })
            
            # Check all cells for amounts
            for col in df.columns:
                for idx, value in enumerate(df[col]):
                    if pd.notna(value):
                        value_str = str(value)
                        amounts = extract_amounts_from_text(value_str, 'INR')
                        for amount_data in amounts:
                            amount = amount_data['original_amount']
                            if amount not in [ta['amount'] for ta in table_amounts]:
                                table_amounts.append({
                                    'table': i+1,
                                    'column': col,
                                    'row': idx+1,
                                    'amount': amount
                                })
        
        # Clean up temporary file
        os.unlink(tmp_path)
        return table_amounts, dfs, all_transactions
        
    except Exception as e:
        st.error(f"Error extracting table amounts: {e}")
        return [], [], []

def process_pdf(uploaded_file, source_currency='INR'):
    """Main function to process PDF and extract all amounts"""
    if uploaded_file is None:
        return None, None, None, None
    
    # Extract text amounts
    pdf_text_pages = read_pdf_text(uploaded_file)
    
    all_amounts = []
    for page_data in pdf_text_pages:
        page_num = page_data['page']
        text = page_data['text']
        amounts = extract_amounts_from_text(text, source_currency)
        
        for amount_data in amounts:
            all_amounts.append({
                'page': page_num, 
                'amount': amount_data['original_amount'], 
                'source': 'text',
                'source_currency': source_currency
            })
    
    # Extract table amounts with transaction types
    table_amounts, tables, transactions = extract_table_amounts_with_types(uploaded_file)
    
    # Analyze CR/DR data
    cr_dr_analysis = analyze_cr_dr_data(transactions) if transactions else None
    
    # Combine all amounts
    combined_amounts = all_amounts + [
        {**amt, 'source': 'table'} for amt in table_amounts
    ]
    
    return combined_amounts, all_amounts, table_amounts, cr_dr_analysis

def answer_business_query(query, amounts_data, cr_dr_analysis=None, display_currency='INR'):
    """Process business queries about the amounts"""
    query_lower = query.lower()
    
    if not amounts_data:
        return "No data available to analyze."
    
    amounts_df = pd.DataFrame(amounts_data)
    
    # Credit/Debit specific queries
    if cr_dr_analysis and ('credit' in query_lower or 'cr' in query_lower or 'debit' in query_lower or 'dr' in query_lower):
        if 'credit' in query_lower or ('cr' in query_lower and 'cr' not in 'records'):
            cr_data = cr_dr_analysis['credit']
            return f"""
            💳 **Credit (CR) Transactions:**
            - Count: {cr_data['count']} transactions
            - Total: {format_currency(cr_data['total'], display_currency)}
            - Average: {format_currency(cr_data['average'], display_currency)}
            - Highest: {format_currency(cr_data['max'], display_currency)}
            - Lowest: {format_currency(cr_data['min'], display_currency)}
            """
        
        if 'debit' in query_lower or ('dr' in query_lower and 'dr' not in 'records'):
            dr_data = cr_dr_analysis['debit']
            return f"""
            💸 **Debit (DR) Transactions:**
            - Count: {dr_data['count']} transactions
            - Total: {format_currency(dr_data['total'], display_currency)}
            - Average: {format_currency(dr_data['average'], display_currency)}
            - Highest: {format_currency(dr_data['max'], display_currency)}
            - Lowest: {format_currency(dr_data['min'], display_currency)}
            """
        
        if 'net' in query_lower or 'balance' in query_lower:
            net_amount = cr_dr_analysis['credit']['total'] - cr_dr_analysis['debit']['total']
            return f"""
            ⚖️ **Net Balance Analysis:**
            - Total Credits (CR): {format_currency(cr_dr_analysis['credit']['total'], display_currency)}
            - Total Debits (DR): {format_currency(cr_dr_analysis['debit']['total'], display_currency)}
            - Net Balance: {format_currency(net_amount, display_currency)}
            - Transaction Ratio: {cr_dr_analysis['credit']['count']}CR : {cr_dr_analysis['debit']['count']}DR
            """
    
    # Total amount queries
    if any(word in query_lower for word in ['total', 'sum', 'altogether']):
        total = amounts_df['amount'].sum()
        return f"💰 **Total Amount**: {format_currency(total, display_currency)}"
    
    # Count queries
    elif any(word in query_lower for word in ['how many', 'count', 'number of']):
        count = len(amounts_df)
        return f"📊 **Total Records**: {count} amounts found"
    
    # Average queries
    elif any(word in query_lower for word in ['average', 'mean']):
        avg = amounts_df['amount'].mean()
        return f"📈 **Average Amount**: {format_currency(avg, display_currency)}"
    
    # Maximum queries
    elif any(word in query_lower for word in ['maximum', 'max', 'highest', 'largest']):
        max_amount = amounts_df['amount'].max()
        max_record = amounts_df[amounts_df['amount'] == max_amount].iloc[0]
        return f"🔝 **Highest Amount**: {format_currency(max_amount, display_currency)} (Page {max_record.get('page', 'N/A')})"
    
    # Minimum queries
    elif any(word in query_lower for word in ['minimum', 'min', 'lowest', 'smallest']):
        min_amount = amounts_df['amount'].min()
        min_record = amounts_df[amounts_df['amount'] == min_amount].iloc[0]
        return f"🔻 **Lowest Amount**: {format_currency(min_amount, display_currency)} (Page {min_record.get('page', 'N/A')})"
    
    # Range queries
    elif 'between' in query_lower or 'range' in query_lower:
        # Try to extract numbers from query
        numbers = re.findall(r'\d+(?:\.\d+)?', query)
        if len(numbers) >= 2:
            low, high = float(numbers[0]), float(numbers[1])
            filtered = amounts_df[(amounts_df['amount'] >= low) & (amounts_df['amount'] <= high)]
            return f"🎯 **Amounts between {format_currency(low, display_currency)} - {format_currency(high, display_currency)}**: {len(filtered)} records, Total: {format_currency(filtered['amount'].sum(), display_currency)}"
    
    # Greater than queries
    elif any(word in query_lower for word in ['greater than', 'more than', 'above']):
        numbers = re.findall(r'\d+(?:\.\d+)?', query)
        if numbers:
            threshold = float(numbers[0])
            filtered = amounts_df[amounts_df['amount'] > threshold]
            return f"📈 **Amounts above {format_currency(threshold, display_currency)}**: {len(filtered)} records, Total: {format_currency(filtered['amount'].sum(), display_currency)}"
    
    # Less than queries
    elif any(word in query_lower for word in ['less than', 'below', 'under']):
        numbers = re.findall(r'\d+(?:\.\d+)?', query)
        if numbers:
            threshold = float(numbers[0])
            filtered = amounts_df[amounts_df['amount'] < threshold]
            return f"📉 **Amounts below {format_currency(threshold, display_currency)}**: {len(filtered)} records, Total: {format_currency(filtered['amount'].sum(), display_currency)}"
    
    # Page-specific queries
    elif 'page' in query_lower:
        page_numbers = re.findall(r'page\s+(\d+)', query_lower)
        if page_numbers:
            page_num = int(page_numbers[0])
            page_amounts = amounts_df[amounts_df['page'] == page_num]
            if not page_amounts.empty:
                return f"📄 **Page {page_num}**: {len(page_amounts)} amounts, Total: {format_currency(page_amounts['amount'].sum(), display_currency)}"
            else:
                return f"📄 **Page {page_num}**: No amounts found"
    
    # Default response with summary
    else:
        total = amounts_df['amount'].sum()
        count = len(amounts_df)
        avg = amounts_df['amount'].mean()
        return f"""
        📊 **Summary Statistics**:
        - Total Amount: {format_currency(total, display_currency)}
        - Number of Records: {count}
        - Average Amount: {format_currency(avg, display_currency)}
        - Range: {format_currency(amounts_df['amount'].min(), display_currency)} - {format_currency(amounts_df['amount'].max(), display_currency)}
        """

# Main Streamlit App
def main():
    st.markdown('<h1 class="main-header">💰 PDF Financial Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Upload PDF")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type="pdf",
            help="Upload a PDF containing financial data (bank statements, invoices, etc.)"
        )
        
        st.markdown("---")
        st.header("💱 Currency Settings")
        
        # Source currency (what's in the PDF)
        source_currency = st.selectbox(
            "📄 PDF Currency",
            options=list(CURRENCY_SYMBOLS.keys()),
            index=0,  # Default to INR
            help="Select the currency used in your PDF document"
        )
        
        # Display currency (what user wants to see)
        display_currency = st.selectbox(
            "👁️ Display Currency",
            options=list(CURRENCY_SYMBOLS.keys()),
            index=0,  # Default to INR
            help="Select the currency for displaying amounts"
        )
        
        # Show conversion rate
        if source_currency != display_currency:
            rate = CURRENCY_RATES.get(display_currency, 1) / CURRENCY_RATES.get(source_currency, 1)
            st.info(f"💱 1 {source_currency} = {rate:.4f} {display_currency}")
        
        st.markdown("---")
        st.header("❓ Sample Queries")
        st.markdown("""
        **General Queries:**
        - "What's the total amount?"
        - "How many records are there?"
        - "What's the highest amount?"
        - "Show amounts above 500"
        - "What's on page 3?"
        - "Average amount?"
        
        **Credit/Debit Queries:**
        - "Show me credit transactions"
        - "What are the debit amounts?"
        - "Net balance analysis"
        - "CR vs DR comparison"
        """)
    
    if uploaded_file is not None:
        st.success(f"📄 Uploaded: {uploaded_file.name}")
        
        # Process PDF
        with st.spinner("🔍 Analyzing PDF... This may take a moment..."):
            combined_amounts, text_amounts, table_amounts, cr_dr_analysis = process_pdf(uploaded_file, source_currency)
        
        if combined_amounts:
            # Convert amounts to display currency
            if source_currency != display_currency:
                with st.spinner("💱 Converting currencies..."):
                    for amt_list in [combined_amounts, text_amounts, table_amounts]:
                        for amt in amt_list:
                            if 'amount' in amt:
                                amt['original_amount'] = amt['amount']
                                amt['amount'] = convert_currency(amt['amount'], source_currency, display_currency)
                                amt['display_currency'] = display_currency
                                amt['source_currency'] = source_currency
            
            # Create tabs for different views
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Dashboard", 
                "💬 Ask Questions", 
                "💳 Credit/Debit Analysis", 
                "📈 Visualizations", 
                "📋 Raw Data"
            ])
            
            # Tab 1: Dashboard
            with tab1:
                st.header("📊 Financial Summary")
                
                amounts_df = pd.DataFrame(combined_amounts)
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_amount = amounts_df['amount'].sum()
                    st.metric("💰 Total Amount", f"{format_currency(total_amount, display_currency)}")
                
                with col2:
                    total_records = len(amounts_df)
                    st.metric("📊 Total Records", f"{total_records}")
                
                with col3:
                    avg_amount = amounts_df['amount'].mean()
                    st.metric("📈 Average Amount", f"{format_currency(avg_amount, display_currency)}")
                
                with col4:
                    max_amount = amounts_df['amount'].max()
                    st.metric("🔝 Highest Amount", f"{format_currency(max_amount, display_currency)}")
            
            st.markdown("---")
            
            # Additional insights
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📄 Page-wise Distribution")
                if 'page' in amounts_df.columns:
                    page_summary = amounts_df.groupby('page').agg({
                        'amount': ['count', 'sum']
                    }).round(2)
                    page_summary.columns = ['Count', 'Total Amount']
                    st.dataframe(page_summary, use_container_width=True)
            
            with col2:
                st.subheader("🎯 Amount Ranges")
                currency_symbol = CURRENCY_SYMBOLS.get(display_currency, display_currency)
                ranges = [
                    (f"{currency_symbol}0 - {currency_symbol}100", (amounts_df['amount'] <= 100).sum()),
                    (f"{currency_symbol}100 - {currency_symbol}500", ((amounts_df['amount'] > 100) & (amounts_df['amount'] <= 500)).sum()),
                    (f"{currency_symbol}500 - {currency_symbol}1000", ((amounts_df['amount'] > 500) & (amounts_df['amount'] <= 1000)).sum()),
                    (f"{currency_symbol}1000+", (amounts_df['amount'] > 1000).sum())
                ]
                range_df = pd.DataFrame(ranges, columns=['Range', 'Count'])
                st.dataframe(range_df, use_container_width=True)
            
            # Tab 2: Query Interface
            with tab2:
                st.header("💬 Ask Business Questions")
                
                # Query input
                query = st.text_input(
                    "🔍 Enter your question:",
                    placeholder="e.g., What's the total amount? How many records above $500?",
                    help="Ask questions about amounts, counts, ranges, pages, etc."
                )
                
                if query:
                    with st.spinner("🤔 Analyzing your question..."):
                        answer = answer_business_query(query, combined_amounts, cr_dr_analysis, display_currency)
                    
                    st.markdown('<div class="query-box">', unsafe_allow_html=True)
                    st.markdown(f"**Your Question:** {query}")
                    st.markdown(f"**Answer:** {answer}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Quick action buttons
                st.markdown("---")
                st.subheader("🚀 Quick Actions")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("💰 Total Amount"):
                        answer = answer_business_query("total amount", combined_amounts, cr_dr_analysis, display_currency)
                        st.info(answer)
                
                with col2:
                    if st.button("📊 Record Count"):
                        answer = answer_business_query("how many records", combined_amounts, cr_dr_analysis, display_currency)
                        st.info(answer)
                
                with col3:
                    if st.button("🔝 Highest Amount"):
                        answer = answer_business_query("maximum amount", combined_amounts, cr_dr_analysis, display_currency)
                        st.info(answer)
            
            # Tab 3: Credit/Debit Analysis
            with tab3:
                st.header("💳 Credit/Debit Analysis")
                
                if cr_dr_analysis:
                    # Summary metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "💳 Total Credits (CR)", 
                            f"{format_currency(cr_dr_analysis['credit']['total'], display_currency)}",
                            f"{cr_dr_analysis['credit']['count']} transactions"
                        )
                    
                    with col2:
                        st.metric(
                            "💸 Total Debits (DR)", 
                            f"{format_currency(cr_dr_analysis['debit']['total'], display_currency)}",
                            f"{cr_dr_analysis['debit']['count']} transactions"
                        )
                    
                    with col3:
                        net_balance = cr_dr_analysis['credit']['total'] - cr_dr_analysis['debit']['total']
                        st.metric(
                            "⚖️ Net Balance", 
                            f"{format_currency(net_balance, display_currency)}",
                            delta=f"{format_currency(abs(net_balance), display_currency)} {'surplus' if net_balance > 0 else 'deficit'}"
                        )
                    
                    st.markdown("---")
                    
                    # Detailed analysis
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("💳 Credit Transactions")
                        if cr_dr_analysis['credit']['count'] > 0:
                            cr_data = cr_dr_analysis['credit']
                            st.write(f"**Count:** {cr_data['count']}")
                            st.write(f"**Average:** {format_currency(cr_data['average'], display_currency)}")
                            st.write(f"**Highest:** {format_currency(cr_data['max'], display_currency)}")
                            st.write(f"**Lowest:** {format_currency(cr_data['min'], display_currency)}")
                            
                            # Show recent credit transactions
                            if cr_data['transactions']:
                                st.subheader("Recent Credit Transactions")
                                cr_df = pd.DataFrame(cr_data['transactions'])
                                st.dataframe(
                                    cr_df[['date', 'description', 'amount']].head(10),
                                    use_container_width=True
                                )
                        else:
                            st.info("No credit transactions found")
                    
                    with col2:
                        st.subheader("💸 Debit Transactions")
                        if cr_dr_analysis['debit']['count'] > 0:
                            dr_data = cr_dr_analysis['debit']
                            st.write(f"**Count:** {dr_data['count']}")
                            st.write(f"**Average:** {format_currency(dr_data['average'], display_currency)}")
                            st.write(f"**Highest:** {format_currency(dr_data['max'], display_currency)}")
                            st.write(f"**Lowest:** {format_currency(dr_data['min'], display_currency)}")
                            
                            # Show recent debit transactions
                            if dr_data['transactions']:
                                st.subheader("Recent Debit Transactions")
                                dr_df = pd.DataFrame(dr_data['transactions'])
                                st.dataframe(
                                    dr_df[['date', 'description', 'amount']].head(10),
                                    use_container_width=True
                                )
                        else:
                            st.info("No debit transactions found")
                    
                    # Transaction type visualization
                    if cr_dr_analysis['credit']['count'] > 0 or cr_dr_analysis['debit']['count'] > 0:
                        st.markdown("---")
                        st.subheader("📊 Transaction Distribution")
                        
                        # Pie chart of transaction types
                        type_data = {
                            'Transaction Type': ['Credit (CR)', 'Debit (DR)'],
                            'Amount': [cr_dr_analysis['credit']['total'], cr_dr_analysis['debit']['total']],
                            'Count': [cr_dr_analysis['credit']['count'], cr_dr_analysis['debit']['count']]
                        }
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig_amount = px.pie(
                                values=type_data['Amount'],
                                names=type_data['Transaction Type'],
                                title='Distribution by Amount',
                                color_discrete_map={'Credit (CR)': '#2E8B57', 'Debit (DR)': '#DC143C'}
                            )
                            st.plotly_chart(fig_amount, use_container_width=True)
                        
                        with col2:
                            fig_count = px.pie(
                                values=type_data['Count'],
                                names=type_data['Transaction Type'],
                                title='Distribution by Count',
                                color_discrete_map={'Credit (CR)': '#2E8B57', 'Debit (DR)': '#DC143C'}
                            )
                            st.plotly_chart(fig_count, use_container_width=True)
                else:
                    st.info("💡 Credit/Debit analysis is available when the PDF contains structured transaction data with CR/DR indicators.")
                    st.markdown("""
                    **To enable this feature:**
                    - Upload bank statements or financial documents
                    - Ensure the document contains columns with CR/DR indicators
                    - The system will automatically detect and classify transactions
                    """)
            
            # Tab 4: Visualizations
            with tab4:
                st.header("📈 Data Visualizations")
                
                amounts_df = pd.DataFrame(combined_amounts)
                
                # Amount distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_hist = px.histogram(
                        amounts_df, 
                        x='amount', 
                        nbins=20,
                        title='Amount Distribution',
                        labels={'amount': 'Amount ($)', 'count': 'Frequency'}
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with col2:
                    if 'page' in amounts_df.columns:
                        page_totals = amounts_df.groupby('page')['amount'].sum().reset_index()
                        fig_page = px.bar(
                            page_totals,
                            x='page',
                            y='amount',
                            title='Total Amount by Page',
                            labels={'page': 'Page Number', 'amount': 'Total Amount ($)'}
                        )
                        st.plotly_chart(fig_page, use_container_width=True)
                
                # Box plot for amount ranges
                fig_box = px.box(
                    amounts_df,
                    y='amount',
                    title='Amount Distribution (Box Plot)',
                    labels={'amount': 'Amount ($)'}
                )
                st.plotly_chart(fig_box, use_container_width=True)
            
            # Tab 5: Raw Data
            with tab5:
                st.header("📋 Raw Data")
                
                # Display options
                col1, col2 = st.columns(2)
                with col1:
                    show_text_amounts = st.checkbox("Show Text Amounts", True)
                with col2:
                    show_table_amounts = st.checkbox("Show Table Amounts", True)
                
                if show_text_amounts and text_amounts:
                    st.subheader("📝 Amounts from Text")
                    text_df = pd.DataFrame(text_amounts)
                    st.dataframe(text_df, use_container_width=True)
                    
                    # Download button
                    csv = text_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Text Amounts",
                        csv,
                        "text_amounts.csv",
                        "text/csv"
                    )
                
                if show_table_amounts and table_amounts:
                    st.subheader("📊 Amounts from Tables")
                    table_df = pd.DataFrame(table_amounts)
                    st.dataframe(table_df, use_container_width=True)
                    
                    # Download button
                    csv = table_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Table Amounts",
                        csv,
                        "table_amounts.csv",
                        "text/csv"
                    )
        
        else:
            st.warning("⚠️ No amounts found in the PDF. Please check if the file contains financial data.")
    
    else:
        st.info("👆 Please upload a PDF file to get started!")
        
        # Show sample interface
        st.markdown("---")
        st.header("🌟 Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📊 Smart Analysis**
            - Extract amounts from text
            - Parse financial tables
            - Multi-page processing
            """)
        
        with col2:
            st.markdown("""
            **💬 Natural Queries**
            - Ask business questions
            - Get instant answers
            - Interactive exploration
            """)
        
        with col3:
            st.markdown("""
            **📈 Rich Visualizations**
            - Interactive charts
            - Distribution analysis
            - Export capabilities
            """)

if __name__ == "__main__":
    main()
