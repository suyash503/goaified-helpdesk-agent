"""MCP server in front of Postgres.

Exposes three read-only tools. The agent never writes SQL: it can only call these
tools with an employee ID, the SQL is fixed and parameterized, and the server logs
in as `helpdesk_ro`, a role that can only SELECT. So even a successful prompt
injection cannot change or dump the database.

Run standalone (stdio transport):  python -m helpdesk.mcp_server
Inspect it:                        npx @modelcontextprotocol/inspector python -m helpdesk.mcp_server
"""
import re
from datetime import date
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row
from mcp.server.mcpserver import MCPServer  # MCP SDK 2.x (was FastMCP in 1.x)

from helpdesk import config

mcp = MCPServer("helpdesk-postgres")
EMP_ID = re.compile(r"^E\d{3}$")


def _query(sql: str, params: tuple) -> list[dict]:
    with psycopg.connect(config.PG_DSN, row_factory=dict_row) as conn:
        rows = conn.execute(sql, params).fetchall()
    # make Decimal / date JSON-friendly
    return [
        {k: (float(v) if isinstance(v, Decimal) else v.isoformat() if isinstance(v, date) else v)
         for k, v in row.items()}
        for row in rows
    ]


def _check(employee_id: str) -> str | None:
    employee_id = employee_id.strip().upper()
    if not EMP_ID.match(employee_id):
        return None
    if not _query("SELECT 1 FROM employees WHERE employee_id = %s", (employee_id,)):
        return None
    return employee_id


@mcp.tool()
def get_leave_balance(employee_id: str) -> dict:
    """Leave balance for the current year (earned, casual, sick): entitled, used and remaining days."""
    eid = _check(employee_id)
    if not eid:
        return {"error": f"No employee found with ID '{employee_id}'."}
    rows = _query(
        """SELECT e.full_name, lb.year, lb.leave_type, lb.entitled, lb.used,
                  lb.entitled - lb.used AS remaining
           FROM leave_balances lb JOIN employees e USING (employee_id)
           WHERE lb.employee_id = %s AND lb.year = EXTRACT(YEAR FROM CURRENT_DATE)
           ORDER BY lb.leave_type""",
        (eid,),
    )
    return {
        "employee_id": eid,
        "name": rows[0]["full_name"] if rows else None,
        "balances": [{k: r[k] for k in ("leave_type", "entitled", "used", "remaining")} for r in rows],
        "total_remaining": sum(r["remaining"] for r in rows),
    }


@mcp.tool()
def get_it_tickets(employee_id: str) -> dict:
    """IT service-desk tickets raised by an employee, newest first, with status and priority."""
    eid = _check(employee_id)
    if not eid:
        return {"error": f"No employee found with ID '{employee_id}'."}
    rows = _query(
        """SELECT ticket_id, category, summary, status, priority, opened_on, resolved_on
           FROM it_tickets WHERE employee_id = %s ORDER BY opened_on DESC""",
        (eid,),
    )
    return {"employee_id": eid, "tickets": rows}


@mcp.tool()
def get_employee_profile(employee_id: str) -> dict:
    """Employee profile: name, department, designation, manager, location, joining date and contact details."""
    eid = _check(employee_id)
    if not eid:
        return {"error": f"No employee found with ID '{employee_id}'."}
    rows = _query(
        """SELECT e.employee_id, e.full_name, e.department, e.designation,
                  m.full_name AS manager, e.location, e.date_joined,
                  e.work_email, e.phone, e.pan, e.aadhaar
           FROM employees e LEFT JOIN employees m ON m.employee_id = e.manager_id
           WHERE e.employee_id = %s""",
        (eid,),
    )
    return rows[0]


if __name__ == "__main__":
    mcp.run()  # stdio transport
