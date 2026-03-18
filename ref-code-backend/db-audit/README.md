# Database QA Audit Tool

Standalone Python script to audit and compare PostgreSQL database schemas across all deployment environments (Develom, TT, USFS).

---

## Prerequisites

- Python 3.9+
- `psycopg2-binary` — `pip install psycopg2-binary`
- `pyyaml` — `pip install pyyaml`
- `google-cloud-secret-manager` — `pip install google-cloud-secret-manager` *(only needed if using Secret Manager for passwords)*
- Cloud SQL Auth Proxy running on port **5434** for `--target cloud`

---

## Authentication

Password resolution order (no `gcloud` commands required):

1. `DB_PASSWORD` environment variable
2. `password_secret_name` field in environment YAML → fetched from **Secret Manager** via Application Default Credentials (ADC)
3. Interactive password prompt (`getpass`)

### Set up ADC (required for Secret Manager access):
```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project <project-id>
```

---

## Modes

### 1. Single-environment audit
Audits one database against the canonical schema in `schema_init.py`.

```bash
python backend/db-audit/db_audit.py --env environments/develom.yaml --target cloud
python backend/db-audit/db_audit.py --env environments/tt.yaml      --target cloud
python backend/db-audit/db_audit.py --env environments/usfs.yaml    --target cloud
```

### 2. Audit + Export snapshot
Same as audit, but also saves a portable schema snapshot JSON for use in `--compare`.

```bash
python backend/db-audit/db_audit.py --env environments/develom.yaml --target cloud --export
python backend/db-audit/db_audit.py --env environments/tt.yaml      --target cloud --export
```

Snapshots are saved to `backend/db-audit/snapshots/<env_name>.json`.

### 3. Cross-environment comparison (offline)
Compares snapshot files — **no live DB connection required**. Run this after collecting snapshots from all environments.

```bash
python backend/db-audit/db_audit.py --compare \
  backend/db-audit/snapshots/develom.json \
  backend/db-audit/snapshots/tt.json \
  backend/db-audit/snapshots/usfs.json
```

---

## Full Cross-Environment Workflow

USFS Cloud SQL is **only reachable from the USFS Cloud Workstation**, not from a Mac.
Use the collect-then-compare pattern:

```
Step 1 — On Mac:
  python backend/db-audit/db_audit.py --env environments/develom.yaml --target cloud --export
  python backend/db-audit/db_audit.py --env environments/tt.yaml      --target cloud --export

Step 2 — On USFS Cloud Workstation:
  python backend/db-audit/db_audit.py --env environments/usfs.yaml --target cloud --export
  # Copy snapshots/usfs.json back to Mac (scp, or commit to a temp branch)

Step 3 — On Mac (offline, no DB needed):
  python backend/db-audit/db_audit.py --compare \
    backend/db-audit/snapshots/develom.json \
    backend/db-audit/snapshots/tt.json \
    backend/db-audit/snapshots/usfs.json
```

---

## Options

| Flag | Description |
|------|-------------|
| `--env PATH` | Path to environment YAML file |
| `--target` | `cloud` (proxy port 5434), `cloud-socket` (Cloud Run), `local` (Docker port 5433) |
| `--export` | Also save schema snapshot to `snapshots/<env>.json` |
| `--compare FILE ...` | Offline diff of 2+ snapshot JSON files |
| `--quiet` | Suppress color/console output; JSON report only |

---

## Output

- **Console**: color-coded `✅ PASS` / `⚠️  WARN` / `❌ FAIL` per check
- **Reports**: `backend/db-audit/reports/<env>_<timestamp>.json` (full audit)
- **Snapshots**: `backend/db-audit/snapshots/<env>.json` (schema-only, for `--compare`)

Reports and snapshots are gitignored.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All checks passed |
| `1` | One or more failures or divergences found |
| `2` | Connection error (DB unreachable, auth failed) |
