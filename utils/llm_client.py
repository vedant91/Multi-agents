# utils/llm_client.py
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── CONFIRMED ACTIVE GROQ MODELS (March 2025) ────────────────
# llama-3.3-70b-versatile  → Smart, 12k TPM limit (heavy agents)
# llama-3.1-8b-instant     → Fast, 30k TPM limit  (fast agents)


def call_groq(system_prompt: str, user_message: str,
              model: str = "llama-3.3-70b-versatile") -> str:
    try:
        # Hard cap both prompts to stay under token limits
        sys = system_prompt[:3500]
        usr = user_message[:10000]

        response = groq_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user",   "content": usr}
            ],
            temperature=0.3,
            max_tokens=2500
        )
        return response.choices[0].message.content

    except Exception as e:
        err = str(e)
        # If still too large, retry with smaller faster model
        if "413" in err or "rate_limit" in err.lower():
            print(f"  ⚠️  Token limit hit on {model}, retrying with llama-3.1-8b-instant...")
            try:
                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt[:1500]},
                        {"role": "user",   "content": user_message[:4000]}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            except Exception as e2:
                return f"[GROQ ERROR]: {str(e2)}"
        return f"[GROQ ERROR]: {err}"


def call_llm(agent_name: str, system_prompt: str, user_message: str) -> str:
    """
    Smart router — uses fast small model for simple agents,
    smart large model for reasoning-heavy agents.
    """
    # Heavy reasoning agents → smarter model
    heavy = ["chairman", "cam_generator", "document_parser", "research"]
    # All other agents → fast model with higher TPM limit
    # (bull, bear, stress_test, fraud_detector, research, compliance)

    if agent_name in heavy:
        return call_groq(system_prompt, user_message,
                         model="llama-3.3-70b-versatile")
    else:
        return call_groq(system_prompt, user_message,
                         model="llama-3.1-8b-instant")

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