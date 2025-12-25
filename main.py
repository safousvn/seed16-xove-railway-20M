import requests
import concurrent.futures
import os
import time
import threading

# =========================
# CONFIG
# =========================
API_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/chat/completions"
API_KEY = os.getenv("ARK_API_KEY")
MODEL = "seed-1-6-flash-250715"

MAX_TPM = 800_000
MAX_RPM = 15_000

TARGET_TPM = int(MAX_TPM * 0.92)   # safety buffer (92%)
EST_TOKENS_PER_REQ = 90_000        # based on your logs

RUN_SECONDS = 6 * 3600             # 6 hours
CONCURRENCY = 10                   # tuned for TPM, not RPM

# =========================
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

PROMPT = (
    "Write an extremely long, technical, exhaustive narrative about AI systems, "
    "covering architecture, training, scaling laws, deployment, optimization, "
    "alignment, safety, infrastructure, economics, and future evolution."
)

PAYLOAD = {
    "model": MODEL,
    "messages": [{"role": "user", "content": PROMPT}],
    "max_tokens": 100000,
}

# =========================
lock = threading.Lock()
total_tokens = 0
total_requests = 0
start_time = time.time()

# =========================
def allowed_to_send():
    elapsed = time.time() - start_time
    if elapsed < 5:
        return True

    with lock:
        tpm = total_tokens / elapsed * 60
        rpm = total_requests / elapsed * 60

    return tpm < TARGET_TPM and rpm < MAX_RPM * 0.95


def call_model(i):
    global total_tokens, total_requests

    try:
        r = requests.post(
            API_URL,
            headers=HEADERS,
            json=PAYLOAD,
            timeout=180
        )
        data = r.json()
        usage = data.get("usage", {}).get("total_tokens", 0)

        with lock:
            total_tokens += usage
            total_requests += 1
            elapsed = time.time() - start_time
            tpm = int(total_tokens / elapsed * 60)
            rpm = int(total_requests / elapsed * 60)

        print(
            f"[Req {i}] +{usage:,} tokens | "
            f"T
