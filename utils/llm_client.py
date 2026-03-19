# utils/llm_client.py
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

CEREBRAS_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("CEREBRAS_API_KEY")
DEFAULT_CEREBRAS_MODEL = os.getenv("CEREBRAS_MODEL", "llama3.1-8b")

# ── RATE LIMITING FOR FREE TIER ────────────────────────────────
_last_call_time = {"llama3.1-8b": 0}
CEREBRAS_FREE_TIER_DELAY = 2.0  # seconds between calls (increased for larger payloads)

# ── CEREBRAS llama3.1-8b CONTEXT LIMIT ────────────────────────
# The Cerebras free tier llama3.1-8b has an 8192 token TOTAL limit
# (system + user + completion). We must stay well within this.
CEREBRAS_MAX_TOKENS = 8192
# Reserve tokens for completion output
COMPLETION_RESERVE_TOKENS = 2000
# Available for input (system + user message)
MAX_INPUT_TOKENS = CEREBRAS_MAX_TOKENS - COMPLETION_RESERVE_TOKENS  # 6192 tokens
# Rough char-to-token ratio (1 token ≈ 4 chars for English text)
CHARS_PER_TOKEN = 4
MAX_INPUT_CHARS = MAX_INPUT_TOKENS * CHARS_PER_TOKEN  # ~24,768 chars total for system+user


def estimate_tokens(text: str) -> int:
    """Rough token count estimate (1 token ≈ 4 chars)."""
    return len(text) // CHARS_PER_TOKEN


def truncate_to_fit(system_prompt: str, user_message: str) -> tuple:
    """
    Truncate the user message to fit within the Cerebras 8192 token limit.
    System prompt is preserved fully; user message is trimmed if needed.
    
    Returns (system_prompt, user_message) — both guaranteed to fit.
    """
    system_tokens = estimate_tokens(system_prompt)
    user_tokens = estimate_tokens(user_message)
    total_tokens = system_tokens + user_tokens
    
    if total_tokens <= MAX_INPUT_TOKENS:
        return system_prompt, user_message
    
    # Calculate how many chars we can afford for user message
    system_chars = len(system_prompt)
    available_for_user = MAX_INPUT_CHARS - system_chars
    
    if available_for_user < 500:
        # System prompt itself is too large — trim it too
        max_sys_chars = MAX_INPUT_CHARS // 2
        system_prompt = system_prompt[:max_sys_chars] + "\n\n[System prompt truncated to fit context limit]"
        available_for_user = MAX_INPUT_CHARS - len(system_prompt)
    
    if len(user_message) > available_for_user:
        # Truncate user message, keeping beginning (instructions) and end (sometimes has key data)
        keep_start = int(available_for_user * 0.7)
        keep_end = int(available_for_user * 0.25)
        truncated = (
            user_message[:keep_start] +
            f"\n\n[... {len(user_message) - keep_start - keep_end} characters truncated to fit context limit ...]\n\n" +
            user_message[-keep_end:]
        )
        user_message = truncated
        print(f"  ⚠️  Truncated input: {total_tokens} est. tokens → ~{estimate_tokens(system_prompt + user_message)} tokens")
    
    return system_prompt, user_message


def _is_model_not_found_error(error_text: str) -> bool:
    """Detect model-not-found style errors across provider formats."""
    msg = (error_text or "").lower()
    return (
        ("model" in msg or "models/" in msg)
        and ("not found" in msg or "not supported" in msg or "unsupported" in msg)
    )


def call_cerebras(system_prompt: str, user_message: str,
              model: str = DEFAULT_CEREBRAS_MODEL,
              max_tokens: int = 2000) -> str:
    """Call Cerebras API with rate limiting and automatic context truncation."""
    import time
    import requests

    # ── TRUNCATE TO FIT CONTEXT LIMIT ────────────────────────
    system_prompt, user_message = truncate_to_fit(system_prompt, user_message)

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
Whenever you analyze financial amounts, they may be in different units (exact Rupees, Lakhs, or Crores). 
Detect the unit being used. Standardize before comparing (e.g., '10 Crores' = 100,000,000 Rupees).
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
                "temperature": 0,     # ZERO temperature = fully deterministic (greedy decoding)
                "top_p": 1,           # No nucleus sampling randomness
                "seed": 42,           # Fixed seed for reproducibility across runs
                "max_completion_tokens": max_tokens
            }
            # Use high timeout for very deep searches
            response = requests.post(url, headers=headers, json=payload, timeout=600)

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                err = f"HTTP {response.status_code}: {response.text}"
                if _is_model_not_found_error(response.text) and model != "llama3.1-8b":
                    print(f"  ⚠️  Model '{model}' unavailable. Falling back to llama3.1-8b...")
                    model = "llama3.1-8b"
                    continue
                if response.status_code == 400 and "context_length" in response.text:
                    # Context still too long even after truncation — aggressively trim
                    print(f"  ⚠️  Context still too long, aggressively truncating...")
                    user_message = user_message[:MAX_INPUT_CHARS // 3]
                    system_prompt = system_prompt[:MAX_INPUT_CHARS // 3]
                    continue  # Retry with shorter input
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
    Smart router using Cerebras llama3.1-8b model.
    Automatically truncates to fit 8192 token context window.
    """
    import time

    start = time.time()

    # We use configurable default model with safe fallback in call_cerebras
    result = call_cerebras(system_prompt, user_message, model=DEFAULT_CEREBRAS_MODEL)

    elapsed = time.time() - start
    print(f"  ⏱️  {agent_name} LLM call: {elapsed:.1f}s")
    return result

# ── TEST ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing QUANTISENSE LLM connections...\n")

    print("1. Testing llama3.1-8b (fast agents)...")
    r2 = call_cerebras(
        system_prompt="You are helpful.",
        user_message="Say exactly: LLAMA 8B INSTANT WORKING",
        model="llama3.1-8b"
    )
    print(f"   {r2[:80]}\n")

    print("✅ Model ready. QUANTISENSE is go!")
