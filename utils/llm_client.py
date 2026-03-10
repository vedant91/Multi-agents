# utils/llm_client.py
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# The user is putting their Cerebras API Key (csk-...) into the GROQ_API_KEY variable
CEREBRAS_API_KEY = os.getenv("GROQ_API_KEY") 

# ── RATE LIMITING ───────────────────────────────────────────────
_last_call_time = {"llama3.1-8b": 0}
CEREBRAS_DELAY = 1.0  

def call_cerebras(system_prompt: str, user_message: str,
              model: str = "llama3.1-8b") -> str:
    """Call Cerebras API (Lightning Fast Llama 3 API)."""
    
    # ── INJECT GLOBAL FINANCIAL AWARENESS PROMPT ────────────────
    global_financial_prompt = """
[CRITICAL INSTRUCTION: MONETARY UNIT DETECTION]
Whenever you analyze financial amounts (Loan Amount, Revenue, EBITDA, Debt, etc.), they may be provided in different units across documents (e.g., exact Rupees [₹1,00,00,000], Lakhs [100 Lakhs], or Crores [1 Crore]). 
You MUST independently detect, analyze, and state the unit being used. Always standardize the magnitude in your head before comparing numbers (e.g., realize that '10 Crores' is 100,000,000 Rupees). Do not make mathematically flawed rejection arguments by confusing an absolute Rupee figure for a Crore figure, or vice versa. Always evaluate the scale accurately.
"""
    system_prompt = system_prompt + "\n" + global_financial_prompt

    url = "https://api.cerebras.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {CEREBRAS_API_KEY}",
        "Content-Type": "application/json"
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Enforce minimum delay between requests
            elapsed = time.time() - _last_call_time.get(model, 0)
            if elapsed < CEREBRAS_DELAY:
                time.sleep(CEREBRAS_DELAY - elapsed)

            _last_call_time[model] = time.time()

            payload = {
                "model": model,  # Cerebras expects 'llama3.1-8b'
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message}
                ],
                "temperature": 0.3,
                "max_completion_tokens": 4096  # Cap output to avoid exhausting quota
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            
            # Identify rate limiting specifically and wait it out
            if response.status_code == 429:
                wait_time = 15 * (attempt + 1)  # Exponential backoff for rate limits
                print(f"  ⚠️  Cerebras Rate Limit on {model} (attempt {attempt+1}/{max_retries}), waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            # For other HTTP errors
            err = f"HTTP {response.status_code}: {response.text[:300]}"
            if response.status_code in [413, 502, 503, 504]:
                wait_time = 5 * (attempt + 1)
                print(f"  ⚠️  Cerebras Server Error {response.status_code} (attempt {attempt+1}/{max_retries}), waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            return f"[CEREBRAS ERROR]: {err}"

        except requests.exceptions.Timeout:
            print(f"  ⚠️  Cerebras Timeout on {model} (attempt {attempt+1}/{max_retries}), waiting 5s...")
            time.sleep(5)
            
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  Cerebras Connection Error on {model} (attempt {attempt+1}/{max_retries}): {e}")
            time.sleep(5)

    return f"[CEREBRAS ERROR]: Max retries exhausted"


def call_llm(agent_name: str, system_prompt: str, user_message: str) -> str:
    """
    Primary LLM router: uses Cerebras llama3.1-8b.
    """
    start = time.time()
    result = call_cerebras(system_prompt, user_message)
    elapsed = time.time() - start
    print(f"  ⏱️  {agent_name} LLM call: {elapsed:.1f}s")
    return result


# ── TEST ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing SENTINEL LLM connections...\n")
    print("1. Testing Cerebras Llama 3.1 8B...")
    r = call_llm("test", "You are helpful.", "Say exactly: CEREBRAS WORKING")
    print(f"   {r[:80]}\n")
    print("✅ Model ready. SENTINEL is go!")