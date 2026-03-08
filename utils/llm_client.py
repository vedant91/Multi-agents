# utils/llm_client.py
import os
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── RATE LIMITING FOR FREE TIER ────────────────────────────────
# Free Groq: ~30 req/min per model
# Add delays between calls to stay under limit
_last_call_time = {"llama-3.3-70b-versatile": 0, "llama-3.1-8b-instant": 0}
GROQ_FREE_TIER_DELAY = 2.5  # seconds between calls (conservative)

# ── CONFIRMED ACTIVE GROQ MODELS (March 2025) ────────────────
# llama-3.3-70b-versatile  → Smart, 12k TPM limit (heavy agents)
# llama-3.1-8b-instant     → Fast, 30k TPM limit  (fast agents)


def call_groq(system_prompt: str, user_message: str,
              model: str = "llama-3.3-70b-versatile",
              max_sys_chars: int = 6000, max_usr_chars: int = 12000,
              max_tokens: int = 4000) -> str:
    """Call Groq API with rate limiting for free tier."""
    import time

    # Cap prompts to stay under token limits
    sys_content = system_prompt[:max_sys_chars]
    usr_content = user_message[:max_usr_chars]

    if len(system_prompt) > max_sys_chars:
        print(f"  ⚠️  System prompt truncated: {len(system_prompt)} → {max_sys_chars} chars")
    if len(user_message) > max_usr_chars:
        print(f"  ⚠️  User message truncated: {len(user_message)} → {max_usr_chars} chars")

    # ── RATE LIMIT: Add delay between API calls ────────────────
    elapsed_since_last_call = time.time() - _last_call_time.get(model, 0)
    if elapsed_since_last_call < GROQ_FREE_TIER_DELAY:
        wait_time = GROQ_FREE_TIER_DELAY - elapsed_since_last_call
        time.sleep(wait_time)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            _last_call_time[model] = time.time()  # Record call time
            response = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": sys_content},
                    {"role": "user",   "content": usr_content}
                ],
                temperature=0.3,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content

        except Exception as e:
            err = str(e)
            if "413" in err or "rate_limit" in err.lower() or "429" in err:
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                print(f"  ⚠️  Rate limit on {model} (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
                time.sleep(wait)
                if attempt == max_retries - 1:
                    # Final fallback: smaller model with tighter limits
                    print(f"  ⚠️  Falling back to llama-3.1-8b-instant...")
                    try:
                        time.sleep(GROQ_FREE_TIER_DELAY)  # Delay before fallback too
                        _last_call_time["llama-3.1-8b-instant"] = time.time()
                        response = groq_client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[
                                {"role": "system", "content": system_prompt[:2000]},
                                {"role": "user",   "content": user_message[:5000]}
                            ],
                            temperature=0.3,
                            max_tokens=1500
                        )
                        return response.choices[0].message.content
                    except Exception as e2:
                        return f"[GROQ ERROR]: {str(e2)}"
            else:
                return f"[GROQ ERROR]: {err}"
    return f"[GROQ ERROR]: Max retries exceeded"


def call_llm(agent_name: str, system_prompt: str, user_message: str) -> str:
    """
    Smart router — uses fast small model for simple agents,
    smart large model for reasoning-heavy agents.
    Adjusts context limits based on agent complexity.
    """
    import time

    # Heavy reasoning agents → smarter model, larger context
    heavy = ["chairman", "cam_generator", "document_parser", "research"]
    # Medium agents that benefit from more context
    medium = ["fraud_detector", "bull", "bear", "fact_checker"]

    start = time.time()

    if agent_name in heavy:
        result = call_groq(system_prompt, user_message,
                          model="llama-3.3-70b-versatile",
                          max_sys_chars=6000, max_usr_chars=12000,
                          max_tokens=4000)
    elif agent_name in medium:
        result = call_groq(system_prompt, user_message,
                          model="llama-3.1-8b-instant",
                          max_sys_chars=4000, max_usr_chars=8000,
                          max_tokens=2500)
    else:
        result = call_groq(system_prompt, user_message,
                          model="llama-3.1-8b-instant",
                          max_sys_chars=3000, max_usr_chars=6000,
                          max_tokens=2000)

    elapsed = time.time() - start
    print(f"  ⏱️  {agent_name} LLM call: {elapsed:.1f}s")
    return result

# ── TEST ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing SENTINEL LLM connections...\n")

    print("1. Testing llama-3.3-70b-versatile (heavy agents)...")
    r1 = call_groq(
        system_prompt="You are helpful.",
        user_message="Say exactly: LLAMA 70B WORKING",
        model="llama-3.3-70b-versatile"
    )
    print(f"   {r1[:80]}\n")

    print("2. Testing llama-3.1-8b-instant (fast agents)...")
    r2 = call_groq(
        system_prompt="You are helpful.",
        user_message="Say exactly: LLAMA 8B INSTANT WORKING",
        model="llama-3.1-8b-instant"
    )
    print(f"   {r2[:80]}\n")

    print("✅ Both models ready. SENTINEL is go!")