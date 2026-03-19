# utils/llm_client.py
# LLM integration using Google Gemini 1.5 Flash
# - 1,000,000 token context window (vs 8,192 for Cerebras)
# - Free tier: 15 RPM, 1M TPM, 1500 RPD
# - Ideal for processing large Indian financial PDFs (200+ pages)

import os
import time
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    # Legacy fallback so existing .env files still work during transition
    or os.getenv("GROQ_API_KEY")
    or os.getenv("CEREBRAS_API_KEY")
)

# ── RATE LIMITING FOR GEMINI FREE TIER ────────────────────────
# Free tier: 15 RPM → minimum 4 s between calls
_last_call_time: dict[str, float] = {}
GEMINI_FREE_TIER_DELAY = 4.0  # seconds between calls

# ── GEMINI 1.5 FLASH CONTEXT LIMITS ───────────────────────────
# Input context: 1,000,000 tokens  (~4,000,000 chars)
# Output (max):  8,192 tokens      → we request up to 4,096 by default
GEMINI_MAX_INPUT_TOKENS = 1_000_000
CHARS_PER_TOKEN = 4
GEMINI_MAX_INPUT_CHARS = GEMINI_MAX_INPUT_TOKENS * CHARS_PER_TOKEN  # 4 M chars

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


def call_gemini(
    system_prompt: str,
    user_message: str,
    model: str = "gemini-1.5-flash",
    max_tokens: int = 4096,
) -> str:
    """
    Call Google Gemini 1.5 Flash with rate limiting and retry logic.

    Gemini 1.5 Flash free tier limits:
      - 15 requests per minute  (enforced by GEMINI_FREE_TIER_DELAY)
      - 1,000,000 tokens per minute
      - 1,500 requests per day
    """
    try:
        import google.generativeai as genai
    except ImportError:
        return (
            "[LLM ERROR]: google-generativeai is not installed. "
            "Run: pip install google-generativeai>=0.8.0"
        )

    if not GEMINI_API_KEY:
        return (
            "[LLM ERROR]: No API key found. Set GEMINI_API_KEY (or GOOGLE_API_KEY) "
            "in your .env file."
        )

    genai.configure(api_key=GEMINI_API_KEY)

    # Inject financial awareness into the system prompt
    full_system = system_prompt + _FINANCIAL_AWARENESS

    # Gemini 1.5 Flash can handle 1M tokens; only truncate if somehow exceeded
    combined_chars = len(full_system) + len(user_message)
    if combined_chars > GEMINI_MAX_INPUT_CHARS:
        overflow = combined_chars - GEMINI_MAX_INPUT_CHARS
        user_message = user_message[: len(user_message) - overflow - 100]
        print(
            f"  ⚠️  Input too large ({combined_chars:,} chars), "
            f"trimmed user message by {overflow:,} chars."
        )

    generation_config = {
        "max_output_tokens": max_tokens,
        "temperature": 0.0,      # deterministic
        "top_p": 1.0,
    }

    max_retries = 5
    for attempt in range(max_retries):
        # ── RATE LIMIT ────────────────────────────────────────
        elapsed = time.time() - _last_call_time.get(model, 0)
        if elapsed < GEMINI_FREE_TIER_DELAY:
            time.sleep(GEMINI_FREE_TIER_DELAY - elapsed)

        _last_call_time[model] = time.time()

        try:
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=full_system,
                generation_config=generation_config,
            )
            response = gemini_model.generate_content(user_message)
            return response.text

        except Exception as e:
            err = str(e)
            # 429 = quota exceeded; 500/503 = transient server errors
            if "429" in err or "quota" in err.lower():
                wait = 60  # wait a full minute on quota errors
                print(
                    f"  ⚠️  Gemini quota hit (attempt {attempt+1}/{max_retries}), "
                    f"waiting {wait}s..."
                )
                time.sleep(wait)
            elif any(code in err for code in ("500", "502", "503", "504")):
                wait = 2 ** (attempt + 1)
                print(
                    f"  ⚠️  Gemini server error (attempt {attempt+1}/{max_retries}), "
                    f"waiting {wait}s..."
                )
                time.sleep(wait)
            else:
                return f"[LLM ERROR]: {err}"

    return "[LLM ERROR]: Max retries exceeded"


def call_llm(agent_name: str, system_prompt: str, user_message: str) -> str:
    """
    Unified LLM router — uses Gemini 1.5 Flash for all agents.

    Gemini 1.5 Flash advantages over the previous Cerebras llama3.1-8b:
      • 1,000,000-token context window  (vs 8,192 tokens)
      • Processes full 200-page Indian financial PDFs without truncation
      • Higher free-tier quotas (1M TPM vs 8K per call)
      • Better instruction following for structured extraction tasks
    """
    start = time.time()
    result = call_gemini(system_prompt, user_message)
    elapsed = time.time() - start
    print(f"  ⏱️  {agent_name} LLM call: {elapsed:.1f}s")
    return result


# ── TEST ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing QUANTISENSE LLM connections...\n")

    print("1. Testing Gemini 1.5 Flash...")
    r = call_gemini(
        system_prompt="You are a helpful assistant.",
        user_message="Say exactly: GEMINI 1.5 FLASH WORKING",
    )
    print(f"   {r[:80]}\n")

    print("✅ Model ready. QUANTISENSE is go!")