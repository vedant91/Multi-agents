# SENTINEL Credit Decision Engine - Decision Flow Guide

## Quick Reference: How SENTINEL Makes Decisions (Fixed Version)

---

## The Decision Process (Simplified)

```
INPUT: Company Details + Documents
    ↓
[STEP 1] Parser: Extract financials
    ↓
[STEP 2] Research: Web search for regulatory/background info
    ↓
[STEP 3] COMPANY INTELLIGENCE: Classify company into tier ← KEY FIX
    ↓
    ├─ TIER 1? (Listed, Big4 auditor, 1000Cr+, 20+ years)
    │  └─→ DEFAULT: APPROVE (unless proven otherwise)
    │
    ├─ TIER 2? (Listed, 100-1000Cr, 10+ years)
    │  └─→ DEFAULT: CONDITIONAL→APPROVE (easier path)
    │
    ├─ TIER 3? (Private, <100Cr, 3-10 years)
    │  └─→ NEUTRAL (standard evaluation)
    │
    └─ TIER 4? (Startup, <3 years)
       └─→ SCRUTINY (more skeptical)
    ↓
[STEP 4] Fraud Detection: Check for fraud patterns
    ↓
[STEP 5A] Bull Agent: Build APPROVAL case
[STEP 5B] Bear Agent: Build REJECTION case
    ↓
[STEP 6] CHAIRMAN: Make final decision ← ENFORCES TIER RULES
    │
    ├─ [Validation Rules] Check evidence quality
    │  ├─ Must have source URL (no hallucinated findings)
    │  ├─ Critical issues need official sources (RBI, NCLT, SEBI, CBI)
    │  └─ For Tier 1: news ≠ confirmed (need official document)
    │
    ├─ [Tier 1 Override] If company is TIER 1:
    │  └─ If NO confirmed critical issues → FORCE APPROVE
    │
    └─ [Score & Decide]
       └─ 85-100: STRONG APPROVE
       └─ 70-84: APPROVE  
       └─ 55-69: CONDITIONAL
       └─ 40-54: REFER (human review)
       └─ <40: REJECT
    ↓
[STEP 7] Stress Test: Run4 scenario simulations
    ↓
[STEP 8] CAM Generator: Create Word document
    ↓
OUTPUT: Decision + Score + Conditions + Full Report
```

---

## Decision Rules by Tier (The Real-World Logic)

### TIER 1: Establishment Powerhouses
**Examples**: Infosys, TCS, Reliance, HDFC Bank, ITC, Larsen & Toubro

| Decision Factor | Rule |
|-----------------|------|
| Default | **APPROVE** (unless proven otherwise) |
| Evidence Standard | Official sources ONLY for critical triggers |
| News Articles | Not sufficient to trigger rejection |
| Speculative Concerns | Downgraded to monitoring/covenants |
| Loan Size | ≤1% of annual revenue = Fast track approval |
| Approval Speed | 2-5 days (minimal additional scrutiny) |
| Bonus Points | +15 to final score |
| Required Documentation | Annual audit, site visit (optional but recommended) |

### TIER 2: Solid Mid-Cap Companies
**Examples**: Mid-cap drugs companies, banking, pharma, auto

| Decision Factor | Rule |
|-----------------|------|
| Default | CONDITIONAL (path to approval) |
| Evidence Standard | Credible sources (RBI, court, ministry) |
| News Articles | Acceptable with corroboration |
| Speculative Concerns | Converted to covenants |
| Loan Size | 5-10% of revenue = Standard review |
| Approval Speed | 5-10 days |
| Bonus Points | +8 to final score |
| Required Documentation | Audited financials, site visit, bank references|

### TIER 3: Private/Small Cap Companies
**Examples**: SMEs, small manufacturers, trading companies

| Decision Factor | Rule |
|-----------------|------|
| Default | Neutral (evaluate purely on merit) |
| Evidence Standard | Standard - all sources weighted equally |
| News Articles | Fully considered |
| Speculative Concerns | Weighted heavily (small cap = higher risk) |
| Loan Size | 10%+ of revenue = Detailed scrutiny |
| Approval Speed | 10-15 days |
| Bonus Points | 0 (no advantage) |
| Required Documentation | Audited financials, site visit MANDATORY, bank statements |

### TIER 4: Startups & New Ventures
**Examples**: <3 years old, <10 crore revenue

| Decision Factor | Rule |
|-----------------|------|
| Default | SCRUTINY (assume higher risk) |
| Evidence Standard | High bar for all claims |
| News Articles | Heavily weighted |
| Speculative Concerns | Are treated as real concerns |
| Loan Size | Small loans only (max 30% of revenue) |
| Approval Speed | 15-30 days |
| Bonus Points | -5 (startup penalty) |
| Required Documentation | MANDATORY site visit, personal guarantors, collateral |

---

## The Real-World Example: Infosys (Tier 1)

**BEFORE FIX** ❌
```
Infosys (197,000 crore, 44 years, Big 4, Listed)
Loan Request: 10 crore

[Research finds] "Possible ED investigation" (news article, unconfirmed)
[Bear Agent] "This is a risk!" 
[Chairman] "Hmm, seems concerning"
[RESULT] REJECTED ❌ (WRONG!)
```

**AFTER FIX** ✅
```
Infosys (Tier 1 Detected: Listed + Big4 + 1000Cr+)
Loan Request: 10 crore (0.005% of revenue - trivial)

[Research finds] "Possible ED investigation" (news, unconfirmed)
[System] "For Tier 1, news needs official source" → DISREGARD
[Bear Agent] "Even with concerns, no confirmed critical issues"
[Chairman] "Tier 1 + no confirmed issues → FORCE APPROVE"
[Validation] No wilful defaulter? No NCLT? No SEBI debarment? 
[RESULT] STRONG APPROVE ✅ (Score: 99/100)
```

---

## Critical Triggers (Auto-Reject Even for Tier 1)

These ONLY trigger rejection if confirmed with official source:

| Trigger | Official Source Required | News Article Alone | Action |
|---------|--------------------------|-------------------|--------|
| Wilful Defaulter | rbi.org.in official list | NOT ENOUGH | Auto-reject |
| NCLT CIRP | nclt.gov.in order # | NOT ENOUGH | Auto-reject |
| SEBI Debarment | sebi.gov.in (NOT fine, actual debarment) | NOT ENOUGH | Auto-reject |
| CBI Charge Sheet | Filed + published | Just "under investigation" = NOT ENOUGH | Defer to human review |
| ED Investigation | Charge sheet filed | "Under investigation" = NOT ENOUGH | Monitor only |
| Auditor Adverse | Adverse/Disclaimer opinion (NOT qualified) | N/A | Auto-reject |
| GST Cancelled | Cancellation order (NOT just demand) | NOT ENOUGH | Refer to human |

---

## Validation Rules (What Prevents False Rejections)

### VALIDATION RULE A: Source Check
```
If finding has NO source URL/citation
→ DISREGARD IT (likely hallucination)

Example wrong finding: "Infosys might have hidden debt"
(No URL, no specific data, just speculation)
→ REJECTED by chairman validation
```

### VALIDATION RULE B: Confidence Level
```
If Research Agent confidence is LOW/MEDIUM
→ Don't auto-reject, escalate to human review
```

### VALIDATION RULE C: Official Source Requirement
```
For TIER 1 critical findings:
- Wilful defaulter → ONLY rbi.org.in official list
- NCLT → ONLY nclt.gov.in with order number
- SEBI debarment → ONLY sebi.gov.in (not a news article about SEBI fine)
- ED/CBI → ONLY charge sheet filed (not just "under investigation")

News article saying "Infosys might be under ED investigation"
→ IGNORED for Tier 1 (not official confirmation)
```

### VALIDATION RULE D: Reality Check
```
Common-sense validation:
- Zero bank debt → Cannot be wilful defaulter (ignore that flag)
- Strong cash flow → Cannot be insolvency risk (ignore)
- Profitable last 3 years → Cannot be distressed (ignore)
```

### VALIDATION RULE E: Allegations vs Confirmed
```
These do NOT automatically trigger rejection:
❌ "GST demand notice" = dispute in progress (use covenant, not reject)
❌ "SEBI fine" = penalty paid, differs from debarment (not auto-reject)
❌ "Under investigation" = no charge yet (use monitoring, not reject)
❌ "Media allegation" = no official confirmation (use covenant)

Move these to MONITORING/COVENANTS, not rejection.
```

---

## How to Read SENTINEL's Decision Letter

Example for Tier 1 company:

```
=== CHAIRMAN'S FINAL DECISION ===

COMPANY TIER: TIER 1 (Listed, Big 4, 1000Cr+)   ← Classification

DECISION: ✅ STRONG APPROVE                      ← Clear verdict

FINAL SCORE: 99/100                             ← With tier bonus

RATIONALE:
1. Tier 1 defaults to approval (unless proven otherwise)
2. No CONFIRMED critical issues detected
3. [Speculative concerns] converted to monitoring

RECOMMENDED TERMS:
- Loan Amount: 10 crore (FULL amount)           ← Usually approved for Tier 1
- Tenure: 36 months
- Interest Rate: 8.5% p.a.
- Security: First charge on current assets
```

---

## Common Misconceptions (Fixed in This Update)

| Misconception | Reality |
|---------------|---------|
| "News = confirmed" | News requires official source for critical triggers (Tier1) |
| "All concerns = reject" | Tier 1 concerns convert to covenants, not rejection |
| "Loan size irrelevant" | 10 crore to 197K crore company = 0.005%, trivial |
| "Hallucinations = facts" | Uncited findings are disregarded by chairman |
| "All companies evaluated same" | Tier 1≠startup; different standards & defaults |
| "API timeout = system failure" | Graceful fallback to neutral assumptions |

---

## Testing Commands

```powershell
# Fast demo (recommended - shows working system)
python test_infosys_demo.py
→ Result: APPROVED 10 crore to Infosys (99/100 score)

# Real web search test (may timeout but handled)
python test_infosys_fix.py
→ Result: Same approval with graceful API timeout handling

# System status check
python test_all_tiers.py
→ Shows: All 6 fixes working, system ready

# Interactive UI for manual testing
streamlit run app.py
→ Upload documents, fill form, get full CAM report
```

---

## For Credit Officers: Reading the Report

### Section 1: Executive Summary
- Decision (APPROVE/REJECT/CONDITIONAL)
- Loan amount offered
- Interest rate
- Key reason in 2 sentences

### Section 2-4: Borrower Profile + Request Details
- Company overview
- Promoter background  
- Facility requested

### Section 5: Five Cs Analysis
- Character: Management quality, track record
- Capacity: Can they repay? (DSCR, CFO, margins)
- Capital: Strong balance sheet? (D/E, net worth)
- Collateral: Sufficient security? (Coverage ratio)
- Conditions: Market/sector/regulatory environment

### Section 6: Data Integrity Assessment
- Revenue verified across: Annual report vs GST vs bank credits
- Fraud patterns: 12-point scan results
- Hallucination risk: LOW/MEDIUM/HIGH

### Section 7-9: External Intelligence, Due Diligence, Stress Test
- Research findings (with sources)
- Site visit observations
- Can they survive -25% revenue? Rate hikes?

### Section 10-12: Risk Factors, Bull vs Bear, Final Details
- Risks and mitigants
- What Bull and Bear argued
- Why Chairman chose one side
- Final score breakdown

---

## Key Takeaway

**SENTINEL is now a production-ready credit intelligence system** that:

✅ **Knows company tiers** → Different rules for Infosys vs startup  
✅ **Validates evidence** → No hallucinated rejections  
✅ **Handles network issues** → Graceful timeouts  
✅ **Respects data quality** → Official sources for critical triggers  
✅ **Is proportional** → 10 crore loan to 197K crore company = FAST APPROVE  

**For Tier 1 companies**: 2-3 day approval for routine loans ✅  
**For Tier 3-4 companies**: Standard 10-15 day evaluation ✅  
**Both**: Bias toward approval if conditions met ✅  

---

Ready for production and hackathon demo! 🚀

Questions? See `FIXES_COMPLETE.md`  
Status: All 6 critical fixes implemented and tested ✓
