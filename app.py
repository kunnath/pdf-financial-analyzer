from pdf_analyzer_app import main
import streamlit as st
from streamlit.web import cli as stcli
import sys
import os

def run_streamlit():
    """Run Streamlit app for Vercel deployment"""
    if "streamlit" not in sys.modules:
        sys.argv = ["streamlit", "run", "pdf_analyzer_app.py", "--server.port=8501", "--server.headless=true"]
        stcli.main()

if __name__ == "__main__":
    run_streamlit()
