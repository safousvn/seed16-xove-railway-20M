import requests
import time
import concurrent.futures
import os
import random
import string

# ================= CONFIG =================
API_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/chat/completions"
API_KEY = os.getenv("ARK_API_KEY")

MODEL = "seed-1-6-flash-250715"

RUN_HOURS = 3
CONCURRENCY = 150          # increase to 200 if allowed
MAX_TOKENS = 8192          # must be supported by model
TIMEOUT = 240
# =========================================

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

def generate_big_prompt():
    base = (
        "Write an extremely long, detailed, technical analysis of artificial intelligence, "
        "its evolution, societal impact, future risks, alignment challenges, and economic effects. "
    )
    noise = " ".join(
        "".join(random.choices(string.ascii_letters + string.digits, k=20))
        for _ in range(6000)
    )
    return base + noise


def build_payload():
    return {
        "model": MODEL,
        "messages": [{"role": "user", "content": generate_big_prompt()}],
        "max_tokens": MAX_TOKENS,
    }


def call_seed(i):
    try:
        payload = build_payload()
        start = time.time()
        r = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT)
        latency = time.time() - start

        data = r.json()
        tokens = data.get("usage", {}).get("total_tokens", 0)

        print(f"[Req {i}] +{tokens} tokens ({latency:.1f}s)")
        return tokens

    except Exception as e:
        print(f"[Req {i}] ERROR: {str(e)[:120]}")
        return 0


def run_load():
    if not API_KEY:
        raise RuntimeError("❌ ARK_API_KEY not set")

    deadline = time.time() + RUN_HOURS * 3600
    total_tokens = 0
    req_id = 0

    print("🔥 Starting HIGH-VOLUME Seed 1.6 load runner")
    print(f"🔥 Target: ~500M tokens in {RUN_HOURS} hours")
    print(f"🔥 Concurrency: {CONCURRENCY}")

    while time.time() < deadline:
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
            futures = []
            for _ in range(CONCURRENCY):
                req_id += 1
                futures.append(executor.submit(call_seed, req_id))

            for f in concurrent.futures.as_completed(futures):
                total_tokens += f.result()

        elapsed = max(1, time.time() - (deadline - RUN_HOURS * 3600))
        rate = int(total_tokens / elapsed)
        print(f"🚀 TOTAL: {total_tokens:,} tokens | ~{rate:,} tokens/sec")

    print("===================================")
    print(f"✅ FINISHED — Total tokens: {total_tokens:,}")
    print("===================================")


if __name__ == "__main__":
    run_load()
