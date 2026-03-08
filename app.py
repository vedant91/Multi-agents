# app.py  ← Run this with: streamlit run app.py
# SENTINEL Web Interface — Clean, professional UI for the hackathon demo

import streamlit as st
import os
import sys
import tempfile
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ── Page Config (must be first Streamlit call) ────────────────
st.set_page_config(
    page_title="SENTINEL — Credit Intelligence",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main theme */
    .main { background-color: #0a0f1e; }
    
    /* Title */
    .sentinel-title {
        font-size: 2.5rem;
        font-weight: 900;
        color: #ff3333;
        letter-spacing: 4px;
        text-align: center;
        margin-bottom: 0;
    }
    .sentinel-tagline {
        color: #888;
        text-align: center;
        font-style: italic;
        margin-top: 0;
        font-size: 1rem;
    }
    
    /* Agent cards */
    .agent-card {
        background: #1a1f2e;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #ff3333;
        margin: 10px 0;
    }
    
    /* Decision box */
    .decision-approve { 
        background: #0d2d0d; 
        border: 2px solid #00cc44;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .decision-reject { 
        background: #2d0d0d; 
        border: 2px solid #ff3333;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .decision-conditional { 
        background: #2d2000; 
        border: 2px solid #ffaa00;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    
    /* Score display */
    .score-display {
        font-size: 3rem;
        font-weight: 900;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ── HEADER ────────────────────────────────────────────────────
st.markdown('<div class="sentinel-title">⬛ SENTINEL</div>', unsafe_allow_html=True)
st.markdown('<div class="sentinel-tagline">"We don\'t just read documents. We interrogate them."</div>', unsafe_allow_html=True)
st.markdown("---")

# ── SIDEBAR — Input Form ──────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏢 Company Details")
    
    company_name = st.text_input("Company Name *", placeholder="ABC Steel Manufacturing Pvt Ltd")
    promoter_name = st.text_input("Promoter / MD Name *", placeholder="Rajesh Kumar Sharma")
    sector = st.selectbox("Sector *", [
        "Steel Manufacturing", "Textiles", "Real Estate", "NBFC / Finance",
        "Pharmaceuticals", "IT Services", "Infrastructure", "Auto Components",
        "Food Processing", "Construction", "Trading", "Other"
    ])

    st.markdown("### 💰 Loan Details")
    loan_amount = st.number_input("Loan Amount (₹ crore) *", min_value=0.1, max_value=5000.0, value=20.0, step=0.5)
    loan_purpose = st.text_area("Loan Purpose *", placeholder="Working capital for expanded manufacturing operations")
    tenure = st.slider("Tenure (months)", min_value=6, max_value=120, value=60, step=6)

    st.markdown("### 📄 Upload Documents")
    uploaded_files = st.file_uploader(
        "Annual Report, Bank Statements, GST Returns, ITR",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload any combination of financial documents"
    )

    st.markdown("### 📝 Primary Due Diligence")
    primary_notes = st.text_area(
        "Site Visit & Management Interview Notes",
        placeholder="Factory visited on 01/06/2025. Operating at ~65% capacity. Machinery well-maintained. Management cooperative. Workers observed: ~150. Any specific observations go here.",
        height=150
    )

    st.markdown("---")
    run_button = st.button("🚀 RUN SENTINEL ANALYSIS", use_container_width=True, type="primary")


# ── MAIN AREA — Show Architecture or Results ──────────────────
if not run_button:
    # Show the architecture when idle
    st.markdown("## 🏗️ SENTINEL Architecture")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **📄 PILLAR 1: DATA INGESTOR**
        - Agent 1: Document Parser
        - Extracts financials from PDFs
        - GST Velocity Fingerprinting
        - Bank statement forensics
        - Revenue triangulation (4-source)
        """)
    with col2:
        st.markdown("""
        **🔍 PILLAR 2: RESEARCH AGENT**
        - Agent 2: Web Intelligence
        - Agent 3: Fraud Detector
        - 12-pattern fraud scan
        - Promoter network mapping
        - Real-time news sentiment
        """)
    with col3:
        st.markdown("""
        **⚖️ PILLAR 3: DECISION ENGINE**
        - Agent 4A: Bull Agent (Approves)
        - Agent 4B: Bear Agent (Rejects)
        - Agent 5: Chairman decides
        - Agent 6: Stress Test
        - Agent 7: CAM Generator
        """)

    st.markdown("---")
    st.markdown("### 🔴 SENTINEL's Unique Edge")
    st.info("""
    🔴 **Adversarial Architecture** — Bull and Bear agents debate every application before the Chairman decides  
    🕸️ **Promoter Network Graph** — Maps all companies connected to the promoter (catches ABG Shipyard-style fraud)  
    📈 **GST Velocity Fingerprinting** — Detects pre-application window dressing in 90-day GST patterns  
    💥 **Stress Test Simulator** — Shows what breaks the company (customer loss, sector shock, rate hike)
    """)

    st.markdown("### 📋 How to Use")
    st.markdown("""
    1. Fill in company and loan details in the sidebar
    2. Upload available documents (Annual Report, Bank Statements, GST returns)
    3. Add your site visit / management interview notes
    4. Click **RUN SENTINEL ANALYSIS**
    5. Download the generated Credit Appraisal Memo
    """)

else:
    # ── VALIDATION ────────────────────────────────────────────
    if not company_name or not promoter_name or not loan_purpose:
        st.error("❌ Please fill in Company Name, Promoter Name, and Loan Purpose.")
        st.stop()

    # ── SAVE UPLOADED FILES TO TEMP ───────────────────────────
    temp_file_paths = []
    if uploaded_files:
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(uploaded_file.read())
                temp_file_paths.append(tmp.name)

    # ── PROGRESS DISPLAY ──────────────────────────────────────
    st.markdown("## 🔄 SENTINEL Analysis Running...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    agent_status = {
        "Document Parser": "⏳",
        "Research Agent": "⏳",
        "Company Intel": "⏳",
        "Fact Checker": "⏳",
        "Fraud Detector": "⏳",
        "Bull Agent": "⏳",
        "Bear Agent": "⏳",
        "Chairman Agent": "⏳",
        "Stress Test": "⏳",
        "CAM Generator": "⏳"
    }
    
    agent_display = st.empty()
    
    def show_agent_status():
        status_str = " | ".join([f"{icon} {name}" for name, icon in agent_status.items()])
        agent_display.markdown(f"**Agents:** {status_str}")
    
    show_agent_status()
    
    def progress_callback(step: str, pct: int):
        progress_bar.progress(pct / 100)
        status_text.markdown(f"**Current:** {step}")
        
        # Update agent icons
        step_lower = step.lower()
        if "parsing" in step_lower or "extracting" in step_lower:
            agent_status["Document Parser"] = "🔵"
        elif "research" in step_lower:
            agent_status["Document Parser"] = "✅"
            agent_status["Research Agent"] = "🔵"
        elif "tier" in step_lower or "credibility" in step_lower:
            agent_status["Research Agent"] = "✅"
            agent_status["Company Intel"] = "🔵"
        elif "fact" in step_lower:
            agent_status["Company Intel"] = "✅"
            agent_status["Fact Checker"] = "🔵"
        elif "fraud" in step_lower:
            agent_status["Fact Checker"] = "✅"
            agent_status["Fraud Detector"] = "🔵"
        elif "bull" in step_lower and "bear" in step_lower:
            agent_status["Fraud Detector"] = "✅"
            agent_status["Bull Agent"] = "🔵"
            agent_status["Bear Agent"] = "🔵"
        elif "bull" in step_lower:
            agent_status["Fraud Detector"] = "✅"
            agent_status["Bull Agent"] = "🔵"
        elif "bear" in step_lower:
            agent_status["Bull Agent"] = "✅"
            agent_status["Bear Agent"] = "🔵"
        elif "chairman" in step_lower:
            agent_status["Bull Agent"] = "✅"
            agent_status["Bear Agent"] = "✅"
            agent_status["Chairman Agent"] = "🔵"
        elif "stress" in step_lower:
            agent_status["Chairman Agent"] = "✅"
            agent_status["Stress Test"] = "🔵"
        elif "generating" in step_lower or "memo" in step_lower:
            agent_status["Stress Test"] = "✅"
            agent_status["CAM Generator"] = "🔵"
        elif "complete" in step_lower:
            agent_status["CAM Generator"] = "✅"
        
        show_agent_status()

    # ── RUN THE FULL PIPELINE ─────────────────────────────────
    try:
        from Orchestrator import run_sentinel
        
        results = run_sentinel(
            company_name=company_name,
            promoter_name=promoter_name,
            sector=sector.lower(),
            loan_amount=loan_amount,
            loan_purpose=loan_purpose,
            loan_tenure_months=tenure,
            uploaded_files=temp_file_paths,
            primary_notes=primary_notes,
            progress_callback=progress_callback
        )
        
        progress_bar.progress(1.0)
        status_text.markdown("**✅ SENTINEL Analysis Complete!**")
        
    except Exception as e:
        st.error(f"❌ Analysis Error: {str(e)}")
        st.exception(e)
        st.stop()
    finally:
        # Clean up temp files
        for path in temp_file_paths:
            if os.path.exists(path):
                os.remove(path)

    # ── DISPLAY RESULTS ───────────────────────────────────────
    st.markdown("---")
    st.markdown(f"## 📊 SENTINEL Report — {company_name}")

    # Quick Summary Row
    col_decision, col_score, col_amount, col_rate = st.columns(4)
    
    # Extract decision from chairman output (simple string search)
    chairman_text = results.get('chairman', '')
    if 'REJECT' in chairman_text.upper() and 'APPROVE' not in chairman_text.upper()[:500]:
        decision_emoji = "🔴"
        decision_label = "REJECTED"
        decision_css = "decision-reject"
    elif 'CONDITIONAL' in chairman_text.upper():
        decision_emoji = "🟡"
        decision_label = "CONDITIONAL"
        decision_css = "decision-conditional"
    else:
        decision_emoji = "🟢"
        decision_label = "APPROVED"
        decision_css = "decision-approve"
    
    with col_decision:
        st.markdown(f"""<div class="{decision_css}">
            <div style="font-size:2rem">{decision_emoji}</div>
            <div style="font-weight:900;font-size:1.2rem">{decision_label}</div>
        </div>""", unsafe_allow_html=True)
    
    with col_score:
        st.metric("SENTINEL Score", "See Report", help="Check Chairman section for full scorecard")
    
    with col_amount:
        st.metric("Amount Requested", f"₹{loan_amount} Cr")
    
    with col_rate:
        st.metric("Tenure", f"{tenure} months")

    st.markdown("")

    # ── TABBED RESULTS VIEW ───────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 Documents", "🔍 Research", "🚨 Fraud Scan",
        "⚔️ The Debate", "💥 Stress Test", "⚖️ Final Decision"
    ])

    with tab1:
        st.markdown("### 📄 Document Parser — Financial Extraction")
        st.text_area("Parser Output", results.get('parser', 'Not run'), height=500)

    with tab2:
        st.markdown("### 🔍 Research Intelligence Report")
        
        # Check for rejection triggers
        research_text = results.get('research', '')
        if 'AUTOMATIC REJECTION' in research_text.upper() and 'NONE' not in research_text.upper()[:500]:
            st.error("⛔ AUTOMATIC REJECTION TRIGGER DETECTED IN RESEARCH!")
        
        st.text_area("Research Output", research_text, height=500)

    with tab3:
        st.markdown("### 🚨 Fraud Detection — 12 Pattern Scan")
        fraud_text = results.get('fraud', '')
        
        if 'CRITICAL' in fraud_text.upper() or 'CONFIRMED' in fraud_text.upper():
            st.warning("⚠️ Fraud patterns detected — review carefully")
        
        st.text_area("Fraud Detection Output", fraud_text, height=500)

    with tab4:
        st.markdown("### ⚔️ The Adversarial Debate")
        
        col_bull, col_bear = st.columns(2)
        
        with col_bull:
            st.markdown("#### 🟢 BULL AGENT — Case for Approval")
            st.text_area("Bull Brief", results.get('bull', ''), height=400, label_visibility="collapsed")
        
        with col_bear:
            st.markdown("#### 🔴 BEAR AGENT — Case for Rejection")
            st.text_area("Bear Brief", results.get('bear', ''), height=400, label_visibility="collapsed")

    with tab5:
        st.markdown("### 💥 Stress Test — What Breaks This Company?")
        st.text_area("Stress Test Results", results.get('stress_test', ''), height=500)

    with tab6:
        st.markdown("### ⚖️ Chairman's Final Verdict")
        
        if decision_label == "REJECTED":
            st.error(f"## {decision_emoji} APPLICATION REJECTED")
        elif decision_label == "CONDITIONAL":
            st.warning(f"## {decision_emoji} CONDITIONAL APPROVAL")
        else:
            st.success(f"## {decision_emoji} APPROVED")
        
        st.text_area("Full Chairman Verdict", results.get('chairman', ''), height=500)

    # ── DOWNLOAD CAM DOCUMENT ─────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Download Credit Appraisal Memo")
    
    cam_path = results.get('cam_doc_path', '')
    if cam_path and os.path.exists(cam_path):
        with open(cam_path, 'rb') as f:
            doc_bytes = f.read()
        
        st.download_button(
            label="📄 Download CAM (.docx)",
            data=doc_bytes,
            file_name=f"SENTINEL_CAM_{company_name.replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    
    # Also offer raw text download
    cam_text = results.get('cam_text', '')
    if cam_text:
        st.download_button(
            label="📝 Download CAM (text)",
            data=cam_text,
            file_name=f"SENTINEL_CAM_{company_name.replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )

    st.markdown("---")
    st.caption("SENTINEL v1.0 | Adversarial Credit Intelligence | Built for Intelli-Credit Hackathon")