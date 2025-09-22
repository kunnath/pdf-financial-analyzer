# 💰 PDF Financial Analyzer

A powerful web-based application built with Streamlit that extracts, analyzes, and visualizes financial data from PDF documents. Perfect for analyzing bank statements, invoices, receipts, and other financial documents.

## 🌟 Features

### 📊 Smart Data Extraction
- **Multi-method extraction**: Combines text parsing and table extraction for comprehensive data capture
- **Currency detection**: Automatically detects various currency formats (₹, $, €, £, etc.)
- **Page-by-page analysis**: Processes all pages of multi-page documents
- **Transaction classification**: Automatically identifies Credit (CR) and Debit (DR) transactions

### 💱 Multi-Currency Support
- **17+ currencies supported**: INR, USD, EUR, GBP, JPY, CAD, AUD, CNY, and more
- **Real-time conversion**: Convert amounts between different currencies
- **Flexible display**: Choose source currency (PDF) and display currency separately
- **Live exchange rates**: Uses current exchange rates for accurate conversions

### 💬 Natural Language Queries
Ask business questions in plain English:
- "What's the total amount?"
- "Show me credit transactions"
- "How many amounts are above ₹500?"
- "What's the average transaction value?"
- "Show net balance analysis"

### 📈 Rich Visualizations
- **Interactive charts**: Distribution histograms, bar charts, box plots
- **Credit/Debit analysis**: Detailed breakdown of transaction types
- **Page-wise insights**: See which pages contain the most transactions
- **Amount range analysis**: Categorize transactions by value ranges

### 📋 Comprehensive Reporting
- **Dashboard view**: Key metrics and summary statistics
- **Detailed analysis**: Credit vs Debit comparison
- **Export capabilities**: Download data as CSV/Excel
- **Raw data access**: View extracted tables and amounts

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd pdf-financial-analyzer
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

#### Option 1: Using the launcher script (macOS/Linux)
```bash
./launch_app.sh
```

#### Option 2: Direct command
```bash
streamlit run pdf_analyzer_app.py
```

The application will open in your browser at `http://localhost:8501`

## 📖 How to Use

### 1. Upload PDF
- Click "Choose a PDF file" in the sidebar
- Upload your bank statement, invoice, or financial document
- Supported formats: PDF files containing text and/or tables

### 2. Configure Currency Settings
- **PDF Currency**: Select the currency used in your PDF document
- **Display Currency**: Choose how you want amounts displayed
- The app will automatically convert between currencies

### 3. Explore Your Data
Navigate through the tabs:

#### 📊 Dashboard
- View key financial metrics
- See page-wise distribution
- Analyze amount ranges

#### 💬 Ask Questions
- Type natural language queries
- Get instant answers about your data
- Use quick action buttons for common questions

#### 💳 Credit/Debit Analysis
- Compare credit vs debit transactions
- View transaction breakdowns
- Analyze net balance

#### 📈 Visualizations
- Interactive charts and graphs
- Amount distribution analysis
- Box plots for statistical insights

#### 📋 Raw Data
- View extracted data tables
- Download CSV files
- Inspect original extracted amounts

## 💼 Use Cases

### Personal Finance
- **Bank statement analysis**: Track income, expenses, and spending patterns
- **Budget monitoring**: Analyze monthly spending across categories
- **Transaction verification**: Quickly find and verify specific transactions

### Business Finance
- **Invoice processing**: Extract amounts from supplier invoices
- **Expense reports**: Analyze company spending patterns
- **Financial auditing**: Review transaction data for compliance

### Accounting
- **Data entry automation**: Reduce manual data entry from PDF statements
- **Reconciliation**: Match transactions across different documents
- **Financial reporting**: Generate summaries from PDF financial documents

## 🛠️ Technical Details

### Architecture
- **Frontend**: Streamlit web interface
- **PDF Processing**: PyPDF2 for text extraction, tabula-py for table extraction
- **Data Analysis**: pandas for data manipulation and analysis
- **Visualization**: Plotly for interactive charts
- **Currency**: Built-in currency conversion with live rates

### Supported Currencies
- **INR** (₹) - Indian Rupee
- **USD** ($) - US Dollar
- **EUR** (€) - Euro
- **GBP** (£) - British Pound
- **JPY** (¥) - Japanese Yen
- **CAD** (C$) - Canadian Dollar
- **AUD** (A$) - Australian Dollar
- **CNY** (¥) - Chinese Yuan

### File Structure
```
pdf-financial-analyzer/
├── pdf_analyzer_app.py      # Main Streamlit application
├── pdfxl.py                 # Original command-line script
├── launch_app.sh            # Launcher script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Dependencies

### Core Libraries
- `streamlit` - Web interface framework
- `pandas` - Data manipulation and analysis
- `plotly` - Interactive visualizations
- `tabula-py` - PDF table extraction
- `PyPDF2` - PDF text extraction
- `openpyxl` - Excel file handling
- `numpy` - Numerical computations

### Installation via requirements.txt
```bash
pip install -r requirements.txt
```

## 📝 Sample Queries

### General Analysis
- "What's the total amount in the document?"
- "How many transactions are there?"
- "What's the average transaction value?"
- "Show me the highest amount"

### Range Queries
- "Show amounts between ₹1000 and ₹5000"
- "How many amounts are above $100?"
- "What transactions are below €50?"

### Credit/Debit Analysis
- "Show me all credit transactions"
- "What's the total debit amount?"
- "Compare credits vs debits"
- "What's the net balance?"

### Page-Specific
- "What amounts are on page 3?"
- "Which page has the most transactions?"

## 🎯 Output Examples

### Dashboard Metrics
```
💰 Total Amount: ₹46,778.57
📊 Total Records: 186
📈 Average Amount: ₹251.50
🔝 Highest Amount: ₹999.00
```

### Credit/Debit Analysis
```
💳 Total Credits (CR): ₹25,430.50 (45 transactions)
💸 Total Debits (DR): ₹21,348.07 (141 transactions)
⚖️ Net Balance: ₹4,082.43 surplus
```

## 🚨 Troubleshooting

### Common Issues

#### PDF Not Processing
- Ensure PDF contains selectable text (not scanned images)
- Check if PDF is password protected
- Verify file is not corrupted

#### No Amounts Found
- PDF might contain only images - try OCR preprocessing
- Check if amounts use non-standard formatting
- Verify currency symbols are recognized

#### Currency Conversion Issues
- Check internet connection for live rates
- Verify selected currencies are supported
- Fallback to manual rate entry if needed

### Error Messages

#### "No module named 'tabula'"
```bash
pip install tabula-py
```

#### "Java not found"
```bash
# Install Java for tabula-py
# macOS: brew install openjdk
# Ubuntu: sudo apt-get install openjdk-8-jdk
```

## 🔄 Updates and Enhancements

### Current Version: 1.0.0
- Multi-currency support
- Natural language queries
- Credit/Debit analysis
- Interactive visualizations
- Export capabilities

### Planned Features
- OCR support for scanned PDFs
- Machine learning for better transaction categorization
- API integration for real-time exchange rates
- Batch processing for multiple PDFs
- Advanced filtering and search

## 🚀 Deploy to Vercel

### Option 1: One-Click Deploy
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/pdf-financial-analyzer)

### Option 2: Manual Deployment

#### Prerequisites
- [Vercel account](https://vercel.com/signup)
- [Vercel CLI](https://vercel.com/cli) (optional but recommended)

#### Step-by-Step Deployment

1. **Prepare your project**
   ```bash
   # Make sure all files are ready
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Deploy via GitHub (Recommended)**
   - Push your code to GitHub
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
   - Vercel will automatically detect the configuration

3. **Deploy via Vercel CLI**
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   
   # Login to Vercel
   vercel login
   
   # Deploy
   vercel
   
   # For production deployment
   vercel --prod
   ```

#### Deployment Files Included
- `vercel.json` - Vercel configuration
- `main.py` - FastAPI application optimized for Vercel
- `runtime.txt` - Python version specification
- `requirements.txt` - Updated with FastAPI dependencies

#### Environment Variables
No environment variables are required for basic functionality. For advanced features, you may set:
- `EXCHANGE_API_KEY` - For real-time currency rates (optional)

#### Post-Deployment
After successful deployment:
1. Your app will be available at `https://your-project.vercel.app`
2. Test the upload functionality
3. Verify currency conversion works
4. Check that all features are accessible

#### Troubleshooting Deployment

**Common Issues:**

1. **Build Timeout**
   - Increase timeout in `vercel.json` (already set to 60s)
   - Consider using serverless functions for heavy processing

2. **File Size Limits**
   - Vercel has a 250MB limit for serverless functions
   - Large PDFs might need chunked processing

3. **Java Dependencies (for tabula-py)**
   - Vercel includes Java runtime
   - If issues persist, consider switching to pdfplumber

**Alternative: Using Railway**
If Vercel doesn't work well for your use case, consider Railway:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For support, questions, or feature requests:
- Create an issue in the repository
- Check the troubleshooting section
- Review the documentation

---

**Made with ❤️ using Streamlit and Python**

*Transform your PDF financial documents into actionable insights!*