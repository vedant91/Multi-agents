# utils/llm_client.py
# LLM integration using Groq — 100% free API tier
# - Model: llama-3.3-70b-versatile (128,000 token context window)
# - Free tier: 30 RPM, 14,400 RPD, no credit card required
# - API key: https://console.groq.com/ (sign up, no billing required)
# - Much larger context than the old Cerebras 8,192-token limit

import os
import time
from dotenv import load_dotenv

load_dotenv()

# GROQ_API_KEY is the primary env var; legacy names also accepted
GROQ_API_KEY = (
    os.getenv("GROQ_API_KEY")
    or os.getenv("GROQ_API_KEY_FREE")
)

# ── RATE LIMITING FOR GROQ FREE TIER ──────────────────────────
# Free tier: 30 RPM → minimum 2 s between calls
_last_call_time: dict[str, float] = {}
GROQ_FREE_TIER_DELAY = 2.0  # seconds between calls

# ── GROQ llama-3.3-70b CONTEXT LIMITS ─────────────────────────
# Context window: 128,000 tokens  (~512,000 chars)
# Output (max):   8,192 tokens    → we request up to 4,096 by default
GROQ_MAX_INPUT_TOKENS = 128_000
CHARS_PER_TOKEN = 4
# Reserve tokens for completion output and system prompt overhead
COMPLETION_RESERVE_TOKENS = 4_096
MAX_INPUT_TOKENS = GROQ_MAX_INPUT_TOKENS - COMPLETION_RESERVE_TOKENS  # 123,904 tokens
MAX_INPUT_CHARS = MAX_INPUT_TOKENS * CHARS_PER_TOKEN  # ~495,616 chars

# ── GLOBAL FINANCIAL AWARENESS INSTRUCTION ────────────────────
_FINANCIAL_AWARENESS = (
    "\n[CRITICAL INSTRUCTION: MONETARY UNIT DETECTION]\n"
    "Whenever you analyze financial amounts, they may be in different units "
    "(exact Rupees, Lakhs, or Crores). Detect the unit being used and "
    "standardize before comparing (e.g., '10 Crores' = 100,000,000 Rupees).\n"
)


def estimate_tokens(text: str) -> int:
    """Rough token count estimate (1 token ≈ 4 chars)."""
    return len(text) // CHARS_PER_TOKEN


def truncate_to_fit(system_prompt: str, user_message: str) -> tuple[str, str]:
    """
    Truncate the user message to fit within Groq's 128K token limit.
    System prompt is preserved; user message is trimmed only if needed.
    Returns (system_prompt, user_message) — both guaranteed to fit.
    """
    combined_chars = len(system_prompt) + len(user_message)
    if combined_chars <= MAX_INPUT_CHARS:
        return system_prompt, user_message

    available_for_user = MAX_INPUT_CHARS - len(system_prompt)
    if available_for_user < 1_000:
        # System prompt itself is too large — split evenly
        half = MAX_INPUT_CHARS // 2
        system_prompt = system_prompt[:half] + "\n\n[System prompt truncated]"
        available_for_user = MAX_INPUT_CHARS - len(system_prompt)

    if len(user_message) > available_for_user:
        keep_start = int(available_for_user * 0.75)
        keep_end = int(available_for_user * 0.20)
        user_message = (
            user_message[:keep_start]
            + f"\n\n[... {len(user_message) - keep_start - keep_end:,} chars "
            "truncated to fit context limit ...]\n\n"
            + user_message[-keep_end:]
        )
        print(
            f"  ⚠️  Input too large ({combined_chars:,} chars), "
            f"trimmed to ~{len(system_prompt) + len(user_message):,} chars."
        )

    return system_prompt, user_message


def call_groq(
    system_prompt: str,
    user_message: str,
    model: str = "llama-3.3-70b-versatile",
    max_tokens: int = 4096,
) -> str:
    """
    Call Groq API with rate limiting and retry logic.

    Groq free tier limits (no credit card required):
      - 30 requests per minute     (enforced by GROQ_FREE_TIER_DELAY)
      - 14,400 requests per day
      - 128,000-token context window (llama-3.3-70b-versatile)
    Get your free API key at: https://console.groq.com/
    """
    try:
        from groq import Groq
    except ImportError:
        return (
            "[LLM ERROR]: groq is not installed. "
            "Run: pip install groq"
        )

    if not GROQ_API_KEY:
        return (
            "[LLM ERROR]: No API key found. Set GROQ_API_KEY in your .env file. "
            "Get a free key at https://console.groq.com/ (no credit card required)."
        )

    # Inject financial awareness and truncate if necessary
    full_system = system_prompt + _FINANCIAL_AWARENESS
    full_system, user_message = truncate_to_fit(full_system, user_message)

    client = Groq(api_key=GROQ_API_KEY)

    max_retries = 5
    for attempt in range(max_retries):
        # ── RATE LIMIT ────────────────────────────────────────
        elapsed = time.time() - _last_call_time.get(model, 0)
        if elapsed < GROQ_FREE_TIER_DELAY:
            time.sleep(GROQ_FREE_TIER_DELAY - elapsed)

        _last_call_time[model] = time.time()

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": full_system},
                    {"role": "user",   "content": user_message},
                ],
                temperature=0,     # deterministic
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        except Exception as e:
            err = str(e)
            # 429 = rate limit / daily quota exceeded
            if "429" in err or "rate_limit" in err.lower():
                wait = 60
                print(
                    f"  ⚠️  Groq rate limit hit (attempt {attempt+1}/{max_retries}), "
                    f"waiting {wait}s..."
                )
                time.sleep(wait)
            elif any(code in err for code in ("500", "502", "503", "504")):
                wait = 2 ** (attempt + 1)
                print(
                    f"  ⚠️  Groq server error (attempt {attempt+1}/{max_retries}), "
                    f"waiting {wait}s..."
                )
                time.sleep(wait)
            else:
                return f"[LLM ERROR]: {err}"

    return "[LLM ERROR]: Max retries exceeded"


def call_llm(agent_name: str, system_prompt: str, user_message: str) -> str:
    """
    Unified LLM router — uses Groq llama-3.3-70b-versatile for all agents.

    Why Groq (free tier):
      • 100% free — no credit card, no billing surprises
      • 128,000-token context window (vs 8,192 for old Cerebras)
      • Processes large Indian financial PDFs without truncation
      • llama-3.3-70b is a strong model for financial analysis tasks
      • Get your API key at: https://console.groq.com/
    """
    start = time.time()
    result = call_groq(system_prompt, user_message)
    elapsed = time.time() - start
    print(f"  ⏱️  {agent_name} LLM call: {elapsed:.1f}s")
    return result


# ── TEST ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing QUANTISENSE LLM connections...\n")

    print("1. Testing Groq llama-3.3-70b-versatile (free)...")
    r = call_groq(
        system_prompt="You are a helpful assistant.",
        user_message="Say exactly: GROQ LLAMA 70B WORKING",
    )
    print(f"   {r[:80]}\n")

    print("✅ Model ready. QUANTISENSE is go!")