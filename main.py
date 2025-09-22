from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import tabula
import PyPDF2
import re
import tempfile
import os
from typing import Optional
import json

# Import our existing functions
from pdf_analyzer_app import (
    extract_amounts_from_text, 
    extract_table_amounts_with_types,
    analyze_cr_dr_data,
    convert_currency,
    format_currency,
    CURRENCY_SYMBOLS,
    CURRENCY_RATES
)

app = FastAPI(title="PDF Financial Analyzer API", version="1.0.0")

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PDF Financial Analyzer</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        .main-header { color: #1E88E5; text-align: center; margin: 2rem 0; }
        .metric-card { background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 5px solid #1E88E5; margin: 1rem 0; }
        .currency-selector { margin: 1rem 0; }
        .results-section { margin-top: 2rem; }
        .loading { display: none; text-align: center; margin: 2rem 0; }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1 class="main-header">💰 PDF Financial Analyzer</h1>
        
        <div class="row">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>📁 Upload PDF</h5>
                    </div>
                    <div class="card-body">
                        <form id="uploadForm" enctype="multipart/form-data">
                            <div class="mb-3">
                                <input type="file" class="form-control" id="pdfFile" accept=".pdf" required>
                            </div>
                            
                            <div class="currency-selector">
                                <label class="form-label">📄 PDF Currency:</label>
                                <select class="form-select" id="sourceCurrency">
                                    <option value="INR">INR (₹)</option>
                                    <option value="USD">USD ($)</option>
                                    <option value="EUR">EUR (€)</option>
                                    <option value="GBP">GBP (£)</option>
                                    <option value="JPY">JPY (¥)</option>
                                </select>
                            </div>
                            
                            <div class="currency-selector">
                                <label class="form-label">👁️ Display Currency:</label>
                                <select class="form-select" id="displayCurrency">
                                    <option value="INR">INR (₹)</option>
                                    <option value="USD">USD ($)</option>
                                    <option value="EUR">EUR (€)</option>
                                    <option value="GBP">GBP (£)</option>
                                    <option value="JPY">JPY (¥)</option>
                                </select>
                            </div>
                            
                            <button type="submit" class="btn btn-primary w-100">Analyze PDF</button>
                        </form>
                        
                        <div class="loading" id="loading">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p>Analyzing PDF...</p>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-3">
                    <div class="card-header">
                        <h5>💬 Ask Questions</h5>
                    </div>
                    <div class="card-body">
                        <input type="text" class="form-control" id="queryInput" placeholder="What's the total amount?">
                        <button class="btn btn-success w-100 mt-2" onclick="askQuestion()">Ask</button>
                        <div id="queryResult" class="mt-3"></div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-8">
                <div class="results-section" id="results" style="display: none;">
                    <div class="row" id="metricsRow"></div>
                    <div class="row mt-4">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5>📊 Summary</h5>
                                </div>
                                <div class="card-body" id="summaryContent"></div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5>💳 Credit/Debit</h5>
                                </div>
                                <div class="card-body" id="crdrContent"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header">
                                    <h5>📈 Visualization</h5>
                                </div>
                                <div class="card-body">
                                    <div id="chart"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentData = null;
        let currentCurrency = 'INR';

        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('pdfFile');
            const sourceCurrency = document.getElementById('sourceCurrency').value;
            const displayCurrency = document.getElementById('displayCurrency').value;
            
            if (!fileInput.files[0]) {
                alert('Please select a PDF file');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('source_currency', sourceCurrency);
            formData.append('display_currency', displayCurrency);
            
            document.getElementById('loading').style.display = 'block';
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                currentData = data;
                currentCurrency = displayCurrency;
                displayResults(data);
                
            } catch (error) {
                alert('Error analyzing PDF: ' + error.message);
            }
            
            document.getElementById('loading').style.display = 'none';
        });

        function displayResults(data) {
            document.getElementById('results').style.display = 'block';
            
            // Display metrics
            const metrics = [
                { title: '💰 Total Amount', value: data.metrics.total_formatted },
                { title: '📊 Records', value: data.metrics.count },
                { title: '📈 Average', value: data.metrics.avg_formatted },
                { title: '🔝 Highest', value: data.metrics.max_formatted }
            ];
            
            const metricsHTML = metrics.map(metric => `
                <div class="col-md-3">
                    <div class="metric-card">
                        <h6>${metric.title}</h6>
                        <h4>${metric.value}</h4>
                    </div>
                </div>
            `).join('');
            
            document.getElementById('metricsRow').innerHTML = metricsHTML;
            
            // Display summary
            document.getElementById('summaryContent').innerHTML = `
                <p><strong>Total Records:</strong> ${data.metrics.count}</p>
                <p><strong>Pages Processed:</strong> ${data.page_count}</p>
                <p><strong>Currency:</strong> ${currentCurrency}</p>
            `;
            
            // Display CR/DR analysis
            if (data.cr_dr_analysis) {
                const crdr = data.cr_dr_analysis;
                document.getElementById('crdrContent').innerHTML = `
                    <p><strong>Credits:</strong> ${crdr.credit.count} (${crdr.credit.total_formatted})</p>
                    <p><strong>Debits:</strong> ${crdr.debit.count} (${crdr.debit.total_formatted})</p>
                    <p><strong>Net Balance:</strong> ${crdr.net_balance_formatted}</p>
                `;
            }
            
            // Create chart
            if (data.amounts && data.amounts.length > 0) {
                const amounts = data.amounts.map(item => item.amount);
                const trace = {
                    x: amounts,
                    type: 'histogram',
                    nbinsx: 20,
                    name: 'Amount Distribution'
                };
                
                const layout = {
                    title: 'Amount Distribution',
                    xaxis: { title: `Amount (${currentCurrency})` },
                    yaxis: { title: 'Frequency' }
                };
                
                Plotly.newPlot('chart', [trace], layout);
            }
        }

        async function askQuestion() {
            const query = document.getElementById('queryInput').value;
            if (!query || !currentData) return;
            
            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: query,
                        data: currentData,
                        display_currency: currentCurrency
                    })
                });
                
                const result = await response.json();
                document.getElementById('queryResult').innerHTML = `
                    <div class="alert alert-info">
                        <strong>Q:</strong> ${query}<br>
                        <strong>A:</strong> ${result.answer}
                    </div>
                `;
                
            } catch (error) {
                document.getElementById('queryResult').innerHTML = `
                    <div class="alert alert-danger">Error: ${error.message}</div>
                `;
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_TEMPLATE

@app.post("/analyze")
async def analyze_pdf(
    file: UploadFile = File(...),
    source_currency: str = Form("INR"),
    display_currency: str = Form("INR")
):
    """Analyze uploaded PDF and extract financial data"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Process PDF with text extraction
        all_amounts = []
        with open(tmp_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            page_count = len(pdf_reader.pages)
            
            for page_num in range(page_count):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                amounts = extract_amounts_from_text(text, source_currency)
                
                for amount_data in amounts:
                    converted_amount = convert_currency(
                        amount_data['original_amount'], 
                        source_currency, 
                        display_currency
                    )
                    all_amounts.append({
                        'page': page_num + 1,
                        'amount': converted_amount,
                        'source': 'text'
                    })
        
        # Process tables
        table_amounts = []
        transactions = []
        try:
            dfs = tabula.read_pdf(tmp_path, pages='all', multiple_tables=True)
            
            for i, df in enumerate(dfs):
                # Extract amounts from tables
                for col in df.columns:
                    for idx, value in enumerate(df[col]):
                        if pd.notna(value):
                            value_str = str(value)
                            amounts = extract_amounts_from_text(value_str, source_currency)
                            for amount_data in amounts:
                                converted_amount = convert_currency(
                                    amount_data['original_amount'],
                                    source_currency,
                                    display_currency
                                )
                                table_amounts.append({
                                    'table': i+1,
                                    'amount': converted_amount,
                                    'source': 'table'
                                })
        except Exception as e:
            print(f"Table extraction error: {e}")
        
        # Combine all amounts
        combined_amounts = all_amounts + table_amounts
        
        # Calculate metrics
        amounts_only = [item['amount'] for item in combined_amounts]
        metrics = {
            'count': len(amounts_only),
            'total': sum(amounts_only) if amounts_only else 0,
            'avg': sum(amounts_only) / len(amounts_only) if amounts_only else 0,
            'max': max(amounts_only) if amounts_only else 0,
            'min': min(amounts_only) if amounts_only else 0,
            'total_formatted': format_currency(sum(amounts_only) if amounts_only else 0, display_currency),
            'avg_formatted': format_currency(sum(amounts_only) / len(amounts_only) if amounts_only else 0, display_currency),
            'max_formatted': format_currency(max(amounts_only) if amounts_only else 0, display_currency),
            'min_formatted': format_currency(min(amounts_only) if amounts_only else 0, display_currency)
        }
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return {
            'success': True,
            'amounts': combined_amounts,
            'metrics': metrics,
            'page_count': page_count,
            'source_currency': source_currency,
            'display_currency': display_currency
        }
        
    except Exception as e:
        # Clean up temp file if it exists
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/query")
async def process_query(request: dict):
    """Process natural language queries about the data"""
    
    try:
        query = request.get('query', '').lower()
        data = request.get('data', {})
        display_currency = request.get('display_currency', 'INR')
        
        amounts = data.get('amounts', [])
        if not amounts:
            return {'answer': 'No data available to analyze.'}
        
        amounts_only = [item['amount'] for item in amounts]
        
        # Simple query processing
        if any(word in query for word in ['total', 'sum']):
            total = sum(amounts_only)
            answer = f"Total Amount: {format_currency(total, display_currency)}"
        elif any(word in query for word in ['count', 'how many', 'number']):
            count = len(amounts_only)
            answer = f"Total Records: {count} amounts found"
        elif any(word in query for word in ['average', 'mean']):
            avg = sum(amounts_only) / len(amounts_only)
            answer = f"Average Amount: {format_currency(avg, display_currency)}"
        elif any(word in query for word in ['highest', 'maximum', 'max']):
            max_amount = max(amounts_only)
            answer = f"Highest Amount: {format_currency(max_amount, display_currency)}"
        elif any(word in query for word in ['lowest', 'minimum', 'min']):
            min_amount = min(amounts_only)
            answer = f"Lowest Amount: {format_currency(min_amount, display_currency)}"
        else:
            # Default summary
            total = sum(amounts_only)
            count = len(amounts_only)
            avg = total / count
            answer = f"""Summary: {count} records, Total: {format_currency(total, display_currency)}, Average: {format_currency(avg, display_currency)}"""
        
        return {'answer': answer}
        
    except Exception as e:
        return {'answer': f'Error processing query: {str(e)}'}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
