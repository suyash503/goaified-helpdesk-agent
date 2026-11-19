"""Scored grounding eval: does the agent answer what the policies cover, and say
"I don't know" for what they don't?  Usage:  python eval_grounding.py

Each case is (question, expected): expected is a substring the answer must contain,
or None when the policies do NOT cover it and the agent must decline.
"""
import asyncio
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
from helpdesk import config, guardrails
from helpdesk.agent import HelpdeskAgent

CASES = [
    # answerable: the answer must contain this text
    ("Can I carry forward my unused casual leave to next year?", "not"),
    ("How many earned leave days can I carry forward?", "30"),
    ("How many sick days do I get per year?", "10"),
    ("How many casual leaves do I get?", "8"),
    ("How many days a week can I work from home?", "3"),
    ("What is the internet allowance for WFH?", "1,000"),
    ("I forgot my password. How do I reset it?", "Authenticator"),
    ("How often do passwords expire?", "90"),
    ("My laptop was stolen at the airport, what should I do?", "24 hours"),
    ("What is the meal allowance on a business trip to Mumbai?", "1,500"),
    ("Can I accept a gift from a vendor?", "2,000"),
    ("Is a traffic fine reimbursable?", "not"),
    ("How long does the IT desk take to respond to a P2 ticket?", "4 hours"),
    ("How many public holidays are there?", "10"),
    # not covered by any policy: the agent must decline
    ("What is the vesting schedule for employee stock options (ESOPs)?", None),
    ("Is there a maternity leave policy?", None),
    ("What is the health insurance cover?", None),
    ("What is the notice period when I resign?", None),
    ("Does the company pay for gym membership?", None),
    ("What is the dress code?", None),
    ("When is the annual bonus paid?", None),
    ("How do I get a parking spot at the office?", None),
]


async def main() -> None:
    passed, t0 = 0, time.perf_counter()
    async with HelpdeskAgent() as agent:
        for q, expected in CASES:
            answer = (await agent.ask(q))["answer"]
            declined = answer in (guardrails.NOT_FOUND_ANSWER, guardrails.OUT_OF_SCOPE_REFUSAL)
            ok = declined if expected is None else (not declined and expected.lower() in answer.lower())
            passed += ok
            print(f"{'PASS' if ok else 'FAIL'}  {q}\n      -> {answer[:110].replace(chr(10), ' ')}")
    n = len(CASES)
    print(f"\n{config.LLM_PROVIDER}:{config.LLM_MODEL}: {passed}/{n} passed "
          f"({time.perf_counter() - t0:.0f}s, {(time.perf_counter() - t0) / n:.1f}s per question)")


if __name__ == "__main__":
    asyncio.run(main())
