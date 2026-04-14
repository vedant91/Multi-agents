# utils/llm_client.py
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

CEREBRAS_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("CEREBRAS_API_KEY")

# ── RATE LIMITING FOR FREE TIER ────────────────────────────────
_last_call_time = {"llama3.1-8b": 0}
CEREBRAS_FREE_TIER_DELAY = 0.5  # seconds between calls (reduced from 1.0)

# ── CONFIRMED ACTIVE CEREBRAS MODELS ────────────────
# llama3.1-8b   → Fast (fast and heavy agents)


def call_cerebras(system_prompt: str, user_message: str,
              model: str = "llama3.1-8b",
              max_tokens: int = 150000,
              max_completion_tokens: int = 1200) -> str:
    """Call Cerebras API with rate limiting. max_completion_tokens controls output length."""
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

    # Do NOT inject global_financial_prompt -- it adds unnecessary tokens
    # each agent's own prompt already handles unit detection where needed

    for attempt in range(max_retries):
        try:
            _last_call_time[model] = time.time()  # Record call time
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message}
                ],
                "temperature": 0.3,
                "max_completion_tokens": max_completion_tokens
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
                print(f"  [WARN]  Rate limit/Error on {model} (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
                time.sleep(wait)
            else:
                return f"[CEREBRAS ERROR]: {err}"
    return f"[CEREBRAS ERROR]: Max retries exceeded"


def call_llm(agent_name: str, system_prompt: str, user_message: str,
             max_completion_tokens: int = 1200) -> str:
    """
    Smart router using Cerebras llama3.1-8b model.
    max_completion_tokens: controls response length. Set lower for speed.
    """
    import time

    start = time.time()
    result = call_cerebras(system_prompt, user_message, model="llama3.1-8b",
                           max_completion_tokens=max_completion_tokens)
    elapsed = time.time() - start
    print(f"  [TIME]  {agent_name} LLM call: {elapsed:.1f}s")
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

    print("[SUCCESS] Model ready. SENTINEL is go!")