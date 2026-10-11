"""Generate MCQ assessment questions using a local Ollama model."""
import json
import os
import re
import urllib.request


def generate_questions(skill_name, count=10):
    """Return validated questions from local Qwen, or [] if Ollama is unavailable."""
    if os.getenv("QWEN_QUESTION_GENERATION", "enabled").lower() not in {"1", "true", "yes", "enabled"}:
        return []
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    count = max(1, min(int(count), 15))
    prompt = (
        f"Create {count} original, technically correct multiple-choice questions about {skill_name}. "
        "Vary topics and difficulty; avoid duplicates and trick questions. For coding skills, include short code/output questions. "
        "Return ONLY a JSON array. Each item must contain keys question, options, correct_option. "
        "options must contain exactly A, B, C, D with distinct non-empty strings. correct_option must be A, B, C, or D. "
        "No markdown or explanations. Ensure each correct answer is factually correct and only one option is correct."
    )
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False, "format": "json",
                          "options": {"temperature": 0.8, "top_p": 0.9}}).encode("utf-8")
    req = urllib.request.Request(base_url + "/api/generate", data=payload,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "90"))) as response:
            raw = json.loads(response.read().decode("utf-8")).get("response", "")
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            start, end = raw.find("["), raw.rfind("]")
            if start < 0 or end <= start:
                return []
            data = json.loads(raw[start:end + 1])
        if isinstance(data, dict):
            data = data.get("questions", [])
        result, seen = [], set()
        for item in data if isinstance(data, list) else []:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question", "")).strip()
            options = item.get("options", {})
            answer = str(item.get("correct_option", "")).strip().upper()
            if not question or len(question) > 3000 or not isinstance(options, dict) or answer not in "ABCD":
                continue
            options = {k: str(options.get(k, "")).strip() for k in "ABCD"}
            if any(not options[k] or len(options[k]) > 500 for k in "ABCD"):
                continue
            if len({v.casefold() for v in options.values()}) != 4:
                continue
            fingerprint = re.sub(r"\W+", "", question.casefold())
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            result.append({"question_text": question, "option_a": options["A"], "option_b": options["B"],
                           "option_c": options["C"], "option_d": options["D"], "correct_option": answer, "marks": 10})
            if len(result) >= count:
                break
        return result
    except Exception:
        # AI generation is optional; failure must not interrupt the rest of the app.
        return []
