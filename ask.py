"""Ask the helpdesk agent.

    python ask.py "How many leave days does E102 have left?"
    python ask.py            # interactive chat
    python ask.py -v "..."   # also print the trace (which nodes ran, what was retrieved)
"""
import asyncio
import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows console: print § and ·
from helpdesk.agent import HelpdeskAgent, format_answer


async def main(argv: list[str]) -> None:
    verbose = "-v" in argv
    args = [a for a in argv if a != "-v"]
    async with HelpdeskAgent() as agent:
        async def run(q: str) -> None:
            result = await agent.ask(q)
            if verbose:
                print("\n".join(f"  · {t}" for t in result["trace"]))
            print(format_answer(result) + "\n")

        if args:
            await run(" ".join(args))
            return
        print("HR/IT helpdesk. Ask a question, or press Enter on an empty line to quit.")
        while q := input("> ").strip():
            await run(q)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
