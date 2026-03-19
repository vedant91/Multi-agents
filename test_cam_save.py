#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick test to verify CAM document saving works
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Override web search with mock
import utils.web_search as ws

def mock_search(query, max_results=5, timeout_seconds=30):
    return "No issues found"

def mock_research(company_name, promoter_name, sector):
    return "No issues found"

ws.search_web = mock_search
ws.run_all_research_searches = mock_research

from Orchestrator import run_quantisense

print("="*80)
print("CAM DOCUMENT SAVE TEST")
print("="*80 + "\n")

print("Running QUANTISENSE analysis for Infosys...\n")

try:
    results = run_quantisense(
        company_name="Infosys Limited",
        promoter_name="Nandan Nilekali",
        sector="IT Services",
        loan_amount=10,
        loan_purpose="Working capital",
        loan_tenure_months=36,
        uploaded_files=[],
        primary_notes="Site visit: All good",
    )
    
    cam_path = results.get('cam_doc_path', '')
    
    print("\n" + "="*80)
    print("RESULT")
    print("="*80)
    
    if cam_path and os.path.exists(cam_path):
        file_size = os.path.getsize(cam_path)
        print(f"\n✅ SUCCESS: CAM document created!")
        print(f"   Path: {cam_path}")
        print(f"   Size: {file_size} bytes")
        print(f"\n   The permission error has been FIXED! 🎉")
    else:
        print(f"\n⚠️ File might not exist or path is: {cam_path}")
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\n   If still seeing 'Permission denied':")
    print("   - Close any open Word documents in output/ folder")
    print("   - Try again in a few seconds")
    print("   - The retry logic will now create _v2.docx, _v3.docx etc if needed")

print("\n" + "="*80)
