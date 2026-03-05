# Databricks notebook source
# MAGIC %md
# MAGIC # Lakebase Setup for Spirit Rules Config
# MAGIC Run once after `databricks bundle deploy`.

# COMMAND ----------

# MAGIC %pip install "databricks-sdk>=0.61.0" psycopg2-binary

# COMMAND ----------

import psycopg2
import secrets
import string
import time
import uuid
from databricks.sdk import WorkspaceClient

# Read config from job parameters (set in databricks.yml variables)
INSTANCE_NAME = dbutils.widgets.get("instance_name")
DATABASE_NAME = dbutils.widgets.get("database_name")
APP_NAME = dbutils.widgets.get("app_name")
SECRET_SCOPE = dbutils.widgets.get("secret_scope")
DB_ROLE = dbutils.widgets.get("db_role")

w = WorkspaceClient()
me = w.current_user.me()
print(f"Running as: {me.user_name}")

# Wait for provisioned Lakebase instance to be AVAILABLE (can take several minutes)
MAX_WAIT = 600  # 10 minutes
POLL_INTERVAL = 15
waited = 0
host = None

print(f"Waiting for Lakebase instance '{INSTANCE_NAME}' to become AVAILABLE...")
while waited < MAX_WAIT:
    try:
        resp = w.api_client.do("GET", f"/api/2.0/database/instances/{INSTANCE_NAME}")
        state = resp.get("state", "UNKNOWN")
        host = resp.get("read_write_dns")
        print(f"  State: {state}, DNS: {host} ({waited}s)")
        if state == "AVAILABLE" and host:
            break
        host = None  # Not ready yet
    except Exception as e:
        print(f"  Instance not found yet ({waited}s): {e}")

    time.sleep(POLL_INTERVAL)
    waited += POLL_INTERVAL

if not host:
    raise RuntimeError(
        f"Lakebase instance '{INSTANCE_NAME}' did not become AVAILABLE within {MAX_WAIT}s. "
        "Provisioned instances can take several minutes. Re-run this job to retry."
    )

print(f"Instance ready! Host: {host}")

# Generate a temporary credential to connect as admin
cred = w.api_client.do("POST", "/api/2.0/database/credentials", body={
    "request_id": str(uuid.uuid4()),
    "instance_names": [INSTANCE_NAME],
})
token = cred.get("token") or cred.get("password")
print("Generated database credential")

# Wait for instance to accept connections
connect_waited = 0
print("Waiting for instance to accept connections...")
while connect_waited < MAX_WAIT:
    try:
        conn = psycopg2.connect(
            host=host, port=5432, dbname="postgres",
            user=me.user_name, password=token, sslmode="require",
            connect_timeout=10,
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1 AS ok")
        print(f"Instance reachable: {cur.fetchone()}")
        cur.close()
        conn.close()
        break
    except Exception as e:
        print(f"  Not accepting connections yet ({connect_waited}s): {e}")
        time.sleep(POLL_INTERVAL)
        connect_waited += POLL_INTERVAL

if connect_waited >= MAX_WAIT:
    raise RuntimeError(
        f"Lakebase instance not accepting connections after {MAX_WAIT}s. "
        "Re-run this job to retry."
    )

# Create database
conn = psycopg2.connect(
    host=host, port=5432, dbname="postgres",
    user=me.user_name, password=token, sslmode="require",
)
conn.autocommit = True
cur = conn.cursor()
cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DATABASE_NAME}'")
if not cur.fetchone():
    cur.execute(f"CREATE DATABASE {DATABASE_NAME}")
    print(f"Created database: {DATABASE_NAME}")
else:
    print(f"Database exists: {DATABASE_NAME}")
cur.close()
conn.close()

# Connect to spirit_rules database as admin for role/extension setup
conn = psycopg2.connect(
    host=host, port=5432, dbname=DATABASE_NAME,
    user=me.user_name, password=token, sslmode="require",
)
conn.autocommit = True
cur = conn.cursor()

# Install pgcrypto extension (requires admin)
cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
print("Installed pgcrypto extension")

# Create app role with password
password = "".join(
    secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
)

cur.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{DB_ROLE}'")
if cur.fetchone():
    cur.execute(f"""ALTER ROLE "{DB_ROLE}" WITH LOGIN PASSWORD '{password}'""")
    print(f"Updated password for role: {DB_ROLE}")
else:
    cur.execute(f"""CREATE ROLE "{DB_ROLE}" WITH LOGIN PASSWORD '{password}'""")
    print(f"Created role: {DB_ROLE}")

# Grant permissions to the app role
grants = [
    f'GRANT ALL ON DATABASE {DATABASE_NAME} TO "{DB_ROLE}"',
    f'GRANT ALL ON SCHEMA public TO "{DB_ROLE}"',
    f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{DB_ROLE}"',
    f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{DB_ROLE}"',
]
for g in grants:
    cur.execute(g)
print("Granted permissions to app role")

# Drop existing tables so we can recreate as the app role
for tbl in ["rule_audit_log", "rule_lines", "rule_headers"]:
    cur.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE")
print("Dropped existing tables (will recreate as app role)")

cur.close()
conn.close()

# Reconnect AS the app role to create tables (so they're owned by it)
conn = psycopg2.connect(
    host=host, port=5432, dbname=DATABASE_NAME,
    user=DB_ROLE, password=password, sslmode="require",
)
conn.autocommit = True
cur = conn.cursor()
print(f"Connected as: {DB_ROLE}")

tables = [
    """CREATE TABLE IF NOT EXISTS rule_headers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        start_date DATE NOT NULL, end_date DATE NOT NULL,
        cost_category VARCHAR(100) NOT NULL, rate_category VARCHAR(100),
        category VARCHAR(100), account_group VARCHAR(100),
        groupby_costcenter BOOLEAN DEFAULT FALSE, groupby_account BOOLEAN DEFAULT FALSE,
        fixed_variable_pct_split DECIMAL(5,2), fixed_variable_type VARCHAR(50),
        status VARCHAR(20) NOT NULL DEFAULT 'draft', version INTEGER NOT NULL DEFAULT 1,
        cloned_from_id UUID REFERENCES rule_headers(id),
        created_by VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS rule_lines (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        header_id UUID NOT NULL REFERENCES rule_headers(id) ON DELETE CASCADE,
        account_number VARCHAR(50) NOT NULL, account_name VARCHAR(200),
        stat_type VARCHAR(50) NOT NULL, proration_rate DECIMAL(10,6) NOT NULL,
        effective_date DATE, notes TEXT, sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS rule_audit_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        header_id UUID NOT NULL REFERENCES rule_headers(id) ON DELETE CASCADE,
        action VARCHAR(20) NOT NULL, changed_by VARCHAR(100) NOT NULL,
        changed_at TIMESTAMP DEFAULT NOW(), old_values JSONB, new_values JSONB
    )""",
]

indexes = [
    "CREATE INDEX IF NOT EXISTS idx_rule_headers_status ON rule_headers(status)",
    "CREATE INDEX IF NOT EXISTS idx_rule_headers_cost_category ON rule_headers(cost_category)",
    "CREATE INDEX IF NOT EXISTS idx_rule_lines_header_id ON rule_lines(header_id)",
    "CREATE INDEX IF NOT EXISTS idx_rule_audit_header_id ON rule_audit_log(header_id)",
]

for sql in tables + indexes:
    cur.execute(sql)
print("Tables and indexes created (owned by app role)")

cur.close()
conn.close()

# Store credentials in Databricks Secrets
try:
    w.secrets.create_scope(scope=SECRET_SCOPE)
    print(f"Created secret scope: {SECRET_SCOPE}")
except Exception as e:
    if "already exists" in str(e).lower():
        print(f"Secret scope exists: {SECRET_SCOPE}")
    else:
        raise

w.secrets.put_secret(scope=SECRET_SCOPE, key="db-host", string_value=host)
w.secrets.put_secret(scope=SECRET_SCOPE, key="db-user", string_value=DB_ROLE)
w.secrets.put_secret(scope=SECRET_SCOPE, key="db-password", string_value=password)
w.secrets.put_secret(scope=SECRET_SCOPE, key="db-name", string_value=DATABASE_NAME)
print("Stored credentials in secrets")

# Grant app service principal READ access to secrets
try:
    app_info = w.api_client.do("GET", f"/api/2.0/apps/{APP_NAME}")
    sp_client_id = app_info.get("service_principal_client_id")
    sp_name = app_info.get("service_principal_name")
    print(f"App SP: client_id={sp_client_id}, name={sp_name}")

    # Try granting by client_id first, then by name, then REST API
    granted = False
    for principal in [sp_client_id, sp_name]:
        if not principal:
            continue
        try:
            w.secrets.put_acl(scope=SECRET_SCOPE, principal=principal, permission="READ")
            print(f"Granted secret READ to: {principal}")
            granted = True
            break
        except Exception as acl_err:
            print(f"  put_acl with '{principal}' failed: {acl_err}")

    if not granted:
        w.api_client.do("POST", "/api/2.0/secrets/acls/put", body={
            "scope": SECRET_SCOPE,
            "principal": sp_client_id,
            "permission": "READ",
        })
        print(f"Granted secret READ via REST API to: {sp_client_id}")
except Exception as e:
    print(f"WARNING: Could not grant SP access: {e}")
    print(f"Manual fix: databricks secrets put-acl {SECRET_SCOPE} <sp-client-id> READ")

print("Setup complete!")
