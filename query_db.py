#!/usr/bin/env python3
"""Query the Lakebase database directly.

Usage:
    # Using a Databricks CLI profile (reads credentials from secrets):
    python query_db.py --profile fe-vm-serverless-jsr0s9 "SELECT * FROM rule_headers"

    # Using direct connection params:
    python query_db.py --host <host> --user <user> --password <pass> --database spirit_rules "SELECT * FROM rule_headers"

    # Interactive mode (keeps connection open for multiple queries):
    python query_db.py --profile <profile> --interactive
"""

import argparse
import base64
import json
import sys
import psycopg2
from psycopg2.extras import RealDictCursor


def get_creds_from_secrets(profile: str, scope: str = "spirit-rules-config") -> dict:
    """Read DB credentials from Databricks Secrets via CLI."""
    import subprocess

    def read_secret(key):
        result = subprocess.run(
            ["databricks", "secrets", "get-secret", scope, key, "--profile", profile],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to read secret '{key}': {result.stderr.strip()}")
        data = json.loads(result.stdout)
        return base64.b64decode(data["value"]).decode("utf-8")

    return {
        "host": read_secret("db-host"),
        "user": read_secret("db-user"),
        "password": read_secret("db-password"),
        "database": read_secret("db-name"),
    }


def run_query(conn, sql: str):
    """Execute a query and print results as a table."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(sql)

    if cur.description is None:
        print(f"OK ({cur.rowcount} rows affected)")
        return

    rows = cur.fetchall()
    if not rows:
        print("(no rows)")
        return

    cols = list(rows[0].keys())
    widths = {c: len(c) for c in cols}
    for row in rows:
        for c in cols:
            widths[c] = max(widths[c], len(str(row[c] or "")))

    header = " | ".join(c.ljust(widths[c]) for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    print(header)
    print(sep)
    for row in rows:
        print(" | ".join(str(row[c] or "").ljust(widths[c]) for c in cols))
    print(f"\n({len(rows)} rows)")


def main():
    parser = argparse.ArgumentParser(description="Query the Lakebase database")
    parser.add_argument("sql", nargs="?", help="SQL query to run")
    parser.add_argument("--profile", "-p", help="Databricks CLI profile (reads creds from secrets)")
    parser.add_argument("--scope", default="spirit-rules-config", help="Secret scope name")
    parser.add_argument("--host", help="Direct DB host")
    parser.add_argument("--user", help="Direct DB user")
    parser.add_argument("--password", help="Direct DB password")
    parser.add_argument("--database", default="spirit_rules", help="Database name")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    args = parser.parse_args()

    if not args.sql and not args.interactive:
        parser.error("Provide a SQL query or use --interactive")

    # Get connection params
    if args.profile:
        print(f"Reading credentials from secrets (profile: {args.profile})...")
        creds = get_creds_from_secrets(args.profile, args.scope)
    elif args.host:
        creds = {"host": args.host, "user": args.user, "password": args.password, "database": args.database}
    else:
        parser.error("Provide --profile or --host/--user/--password")

    conn = psycopg2.connect(
        host=creds["host"], port=5432, dbname=creds["database"],
        user=creds["user"], password=creds["password"], sslmode="require",
    )
    conn.autocommit = True
    print(f"Connected to {creds['host']} / {creds['database']}\n")

    if args.interactive:
        print("Type SQL queries (Ctrl+D to exit):\n")
        while True:
            try:
                sql = input("sql> ").strip()
                if not sql:
                    continue
                run_query(conn, sql)
                print()
            except EOFError:
                break
            except Exception as e:
                print(f"ERROR: {e}\n")
    else:
        run_query(conn, args.sql)

    conn.close()


if __name__ == "__main__":
    main()
