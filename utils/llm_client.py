# utils/llm_client.py
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

CEREBRAS_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("CEREBRAS_API_KEY")

# ── RATE LIMITING FOR FREE TIER ────────────────────────────────
_last_call_time = {"llama3.1-8b": 0}
CEREBRAS_FREE_TIER_DELAY = 1.0  # seconds between calls

# ── CONFIRMED ACTIVE CEREBRAS MODELS ────────────────
# llama3.1-8b   → Fast (fast and heavy agents)


def call_cerebras(system_prompt: str, user_message: str,
              model: str = "llama3.1-8b",
              max_tokens: int = 150000) -> str:
    """Call Cerebras API with rate limiting using native requests, unlimited context."""
    import time
    import requests

    # ── RATE LIMIT: Add delay between API calls ────────────────
    elapsed_since_last_call = time.time() - _last_call_time.get(model, 0)
    if elapsed_since_last_call < CEREBRAS_FREE_TIER_DELAY:
        wait_time = CEREBRAS_FREE_TIER_DELAY - elapsed_since_last_call
        time.sleep(wait_time)

    max_retries = 5
    url = "https://api.cerebras.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {CEREBRAS_API_KEY}",
        "Content-Type": "application/json"
    }

    # ── INJECT GLOBAL FINANCIAL AWARENESS PROMPT ────────────────
    global_financial_prompt = """
[CRITICAL INSTRUCTION: MONETARY UNIT DETECTION]
Whenever you analyze financial amounts (Loan Amount, Revenue, EBITDA, Debt, etc.), they may be provided in different units across documents (e.g., exact Rupees [₹1,00,00,000], Lakhs [100 Lakhs], or Crores [1 Crore]). 
You MUST independently detect, analyze, and state the unit being used. Always standardize the magnitude in your head before comparing numbers (e.g., realize that '10 Crores' is 100,000,000 Rupees). Do not make mathematically flawed rejection arguments by confusing an absolute Rupee figure for a Crore figure, or vice versa. Always evaluate the scale accurately.
"""
    system_prompt = system_prompt + "\n" + global_financial_prompt

    for attempt in range(max_retries):
        try:
            _last_call_time[model] = time.time()  # Record call time
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message}
                ],
                "temperature": 0.3
                # Removed max_completion_tokens completely to allow default unlimited 
                # completion sizing depending on context limits.
            }
            # Use high timeout for very deep searches
            response = requests.post(url, headers=headers, json=payload, timeout=600)

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                err = f"HTTP {response.status_code}: {response.text}"
                if response.status_code in [429, 413, 502, 503, 504]:
                    raise Exception(err)
                return f"[CEREBRAS ERROR]: {err}"

        except Exception as e:
            err = str(e)
            if "413" in err or "429" in err or "50" in err:
                wait = 65 if "429" in err else 2 ** (attempt + 1)  # 65s for token per min rate limit if 429
                print(f"  ⚠️  Rate limit/Error on {model} (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
                time.sleep(wait)
            else:
                return f"[CEREBRAS ERROR]: {err}"
    return f"[CEREBRAS ERROR]: Max retries exceeded"


def call_llm(agent_name: str, system_prompt: str, user_message: str) -> str:
    """
    Smart router using Cerebras llama3.1-8b model. NO LIMITS ON TOKENS.
    """
    import time

    start = time.time()

    # We use llama3.1-8b for everything since it is fast and available
    result = call_cerebras(system_prompt, user_message, model="llama3.1-8b")

    elapsed = time.time() - start
    print(f"  ⏱️  {agent_name} LLM call: {elapsed:.1f}s")
    return result

# ── TEST ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing SENTINEL LLM connections...\n")

    print("1. Testing llama3.1-8b (fast agents)...")
    r2 = call_cerebras(
        system_prompt="You are helpful.",
        user_message="Say exactly: LLAMA 8B INSTANT WORKING",
        model="llama3.1-8b"
    )
    print(f"   {r2[:80]}\n")

    print("✅ Model ready. SENTINEL is go!")