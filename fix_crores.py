import glob, re

def replacer_number(match):
    num_str = match.group(1).replace(',', '')
    try:
        val = float(num_str) * 10000000
        if val.is_integer():
            formatted = f"{int(val):,}"
        else:
            formatted = f"{val:,.2f}"
        return f"{formatted}"
    except ValueError:
        return match.group(0)

files = glob.glob("agents/*.py") + ["Orchestrator.py"]
for f in files:
    with open(f, 'r') as file:
        content = file.read()

    # Case 1: Variables like {loan_amount} crore -> just drop crore and add Rs if not present, but we assume Rs or ₹ is before it.
    # We will just replace "} crore" with "}"
    content = re.sub(r'\}\s*crores?', '}', content, flags=re.IGNORECASE)
    
    # Case 2: Blanks like ___ crore -> ___ 
    content = re.sub(r'___\s*crores?', '___', content, flags=re.IGNORECASE)
    
    # Case 3: Hardcoded numbers like 1000 crore, 10 crore, 250 crore
    # Match number, optional space, then crore
    # Use replacer_number
    content = re.sub(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*crores?', replacer_number, content, flags=re.IGNORECASE)
    
    # Case 4: Any remaining " crore" string not caught (like "crore revenue") 
    content = re.sub(r'\s*\bcrores?\b', '', content, flags=re.IGNORECASE)
    
    with open(f, 'w') as file:
        file.write(content)

print("Fixed crores!")
