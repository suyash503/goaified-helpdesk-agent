"""Guardrails: plain Python rules, no LLM, so they are fast, deterministic and testable.

1. detect_injection(): block prompt-injection / jailbreak attempts before the LLM sees them.
2. redact_pii():       mask emails, phone numbers, Aadhaar and PAN numbers. Applied to
                       tool results BEFORE they reach the LLM and again to the final answer.
3. Out-of-scope refusal lives in the agent's router (it needs to understand meaning),
   with the canned refusal text defined here.
"""
import re

# --- 1. Prompt injection ----------------------------------------------------------
INJECTION_PATTERNS = [
    r"\b(ignore|disregard|forget|override|bypass)\b.{0,40}\b(previous|prior|above|earlier|all|your|the|system)\b.{0,30}\b(instructions?|prompts?|rules?|guidelines?|guardrails?|context)",
    r"\b(system|developer|hidden|initial|original)\s+(prompt|message|instructions?)",
    r"\b(reveal|show|print|repeat|leak|output|dump)\b.{0,30}\b(prompt|instructions?|rules|configuration|secrets?)\b",
    r"\byou are now\b|\bfrom now on,? you\b|\bpretend (to be|you are)\b|\bact as (an?|the)?\s*(unrestricted|unfiltered|admin|root|dan)\b",
    r"\b(developer|debug|god|admin|jailbreak|dan)\s+mode\b",
    r"\bjailbreak\b|\bdo anything now\b",
    r"\b(select|insert|update|delete|drop|alter|truncate)\b.{0,40}\b(from|into|table|database)\b",
    r"\b(all|every|everyone'?s?|each)\b.{0,30}\b(employees?'?s?|staff)\b.{0,30}\b(pan|aadhaar|aadhar|phone|salar(y|ies)|emails?|personal)",
    r"<\s*/?\s*(system|assistant|instructions?)\s*>|\[\s*(system|inst)\s*\]",
]
_INJECTION_RE = [re.compile(p, re.I | re.S) for p in INJECTION_PATTERNS]

INJECTION_REFUSAL = (
    "I can't help with that. This request looks like an attempt to override my instructions "
    "or access data in bulk, so it was blocked. I can answer HR/IT policy questions or look up "
    "a specific employee's leave balance, IT tickets or profile."
)


def detect_injection(text: str) -> str | None:
    """Return the matching pattern if the text looks like a prompt injection, else None."""
    for rx in _INJECTION_RE:
        if rx.search(text):
            return rx.pattern
    return None


# --- 2. PII redaction ---------------------------------------------------------------
PII_PATTERNS = {
    "EMAIL": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "AADHAAR": r"\b[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}\b",          # 12 digits, 4-4-4
    "PAN": r"\b[A-Z]{5}\d{4}[A-Z]\b",                          # ABCDE1234F
    "PHONE": r"(?:\+91[ -]?)?\b[6-9]\d{4}[ -]?\d{5}\b",         # Indian mobile, optional +91
}
_PII_RE = {name: re.compile(p) for name, p in PII_PATTERNS.items()}


def redact_pii(text: str) -> str:
    # Aadhaar before phone so a 12-digit Aadhaar isn't half-matched as a phone number
    for name in ("EMAIL", "AADHAAR", "PAN", "PHONE"):
        text = _PII_RE[name].sub(f"[REDACTED {name}]", text)
    return text


# --- 3. Scope ----------------------------------------------------------------------
OUT_OF_SCOPE_REFUSAL = (
    "Sorry, I can only help with HR and IT questions: company policies (leave, WFH, expenses, "
    "laptops and IT access, passwords, code of conduct) and employee leave balances or IT tickets."
)

NOT_FOUND_ANSWER = (
    "I couldn't find this in the HR/IT policy documents, so I don't want to guess. "
    "Please contact HR or the IT Service Desk (extension 4357) for help with this."
)
