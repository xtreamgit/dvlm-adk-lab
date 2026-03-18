# Account Configuration Management

This directory contains account-specific configurations for the ADK RAG Agent application.

## 📁 Directory Structure

```
backend/config/
├── README.md                 # This file
├── config_loader.py          # Configuration loader utility
├── develom/                  # Develom (root) account
│   ├── __init__.py
│   ├── config.py            # Develom-specific settings
│   └── agent.py             # Develom-specific agent configuration
├── usfs/                     # U.S. Forest Service account
│   ├── __init__.py
│   ├── config.py            # USFS-specific settings
│   └── agent.py             # USFS-specific agent configuration
└── tt/                       # TechTrend account
    ├── __init__.py
    ├── config.py            # TechTrend-specific settings
    └── agent.py             # TechTrend-specific agent configuration
```

## 🎯 Purpose

This configuration system allows the application to support multiple accounts/clients with different:
- GCP Project IDs
- Regions
- Corpus mappings
- Agent personalities and branding
- Organization domains
- Default settings

## 🚀 Usage

### Setting the Account

Use the `ACCOUNT_ENV` environment variable to select which account configuration to use:

```bash
# For Develom (root account)
export ACCOUNT_ENV=develom

# For U.S. Forest Service
export ACCOUNT_ENV=usfs

# For TechTrend
export ACCOUNT_ENV=tt
```

### In Deployment Scripts

Update your deployment scripts to set the account:

```bash
#!/bin/bash

# Set account environment
export ACCOUNT_ENV=usfs

# Run deployment
./infrastructure/deploy-secure-v0.2.sh
```

### In Docker/Cloud Run

Set the environment variable in your Docker run command or Cloud Run configuration:

```bash
# Docker
docker run -e ACCOUNT_ENV=usfs my-app

# Cloud Run
gcloud run deploy backend \
  --set-env-vars="ACCOUNT_ENV=usfs"
```

### In Application Code

The application will automatically load the correct configuration based on `ACCOUNT_ENV`:

```python
# backend/src/rag_agent/__init__.py or similar
import os
from config.config_loader import load_config, load_agent

# Load account-specific configuration
account_env = os.environ.get("ACCOUNT_ENV", "develom")
config = load_config(account_env)
agent = load_agent(account_env)

# Now use config and agent
print(f"Using account: {config.ACCOUNT_NAME}")
print(f"Project ID: {config.PROJECT_ID}")
```

## 📋 Account Details

### Develom (develom)
- **Project:** adk-rag-hdtest6
- **Region:** us-east4
- **Domain:** develom.com
- **Purpose:** Root repository, general development

### USFS (usfs)
- **Project:** usfs-rag-agent *(update with actual)*
- **Region:** us-central1 *(update with actual)*
- **Domain:** usda.gov
- **Purpose:** U.S. Forest Service forestry and environmental documentation

### TechTrend (tt)
- **Project:** techtrend-rag-agent *(update with actual)*
- **Region:** us-east4 *(update with actual)*
- **Domain:** techtrend.com
- **Purpose:** Technology articles, product documentation, research papers

## 🔧 Account-Specific Settings

Each account configuration (`config.py`) includes:

- **PROJECT_ID**: GCP project identifier
- **LOCATION**: GCP region
- **ACCOUNT_NAME**: Short account identifier
- **ACCOUNT_DESCRIPTION**: Human-readable description
- **CORPUS_TO_BUCKET_MAPPING**: Corpus name to GCS bucket mappings
- **ORGANIZATION_DOMAIN**: Organization email domain
- **DEFAULT_CORPUS_NAME**: Default corpus for the account
- **RAG settings**: Chunk size, overlap, top-k, etc.

Each agent configuration (`agent.py`) includes:

- **Agent name**: Account-specific agent identifier
- **Agent description**: Account-specific branding
- **Instructions**: Customized instructions and personality
- **Version info**: Account-specific version strings

## 📝 Adding a New Account

1. **Create account directory:**
   ```bash
   mkdir backend/config/newaccount
   ```

2. **Copy template files:**
   ```bash
   cp backend/config/develom/config.py backend/config/newaccount/
   cp backend/config/develom/agent.py backend/config/newaccount/
   cp backend/config/develom/__init__.py backend/config/newaccount/
   ```

3. **Update configuration:**
   - Edit `config.py` with account-specific settings
   - Edit `agent.py` with account-specific branding
   - Update `__init__.py` with account info

4. **Update config_loader.py:**
   - Add new account to the valid accounts list

5. **Set environment variable:**
   ```bash
   export ACCOUNT_ENV=newaccount
   ```

## 🔐 Security Considerations

- **Never commit sensitive credentials** to config files
- Use environment variables for secrets (OAuth keys, etc.)
- Each account should have its own GCP project for isolation
- Service accounts should have minimal required permissions

## 🧪 Testing Different Accounts

```bash
# Test Develom configuration
ACCOUNT_ENV=develom python -m pytest tests/

# Test USFS configuration
ACCOUNT_ENV=usfs python -m pytest tests/

# Test TechTrend configuration
ACCOUNT_ENV=tt python -m pytest tests/
```

## 📦 Deployment Per Account

### Develom Deployment
```bash
export ACCOUNT_ENV=develom
./infrastructure/deploy-complete-oauth-v0.2.sh
```

### USFS Deployment
```bash
export ACCOUNT_ENV=usfs
./infrastructure/deploy-complete-oauth-v0.2.sh
```

### TechTrend Deployment
```bash
export ACCOUNT_ENV=tt
./infrastructure/deploy-complete-oauth-v0.2.sh
```

## 🔄 Migration Path

### Current State (Before)
- Configuration hardcoded in `backend/src/rag_agent/config.py`
- Agent configuration hardcoded in `backend/src/rag_agent/agent.py`
- Deployment scripts manually edit these files

### New State (After Full Migration)
- Original files reference account-specific configs
- Deployment scripts only set `ACCOUNT_ENV` environment variable
- No file editing required during deployment

### Transition Plan
1. ✅ **Phase 1**: Create account-specific configs (DONE)
2. **Phase 2**: Create config loader utility
3. **Phase 3**: Update original files to use config loader
4. **Phase 4**: Update deployment scripts to set `ACCOUNT_ENV`
5. **Phase 5**: Test each account independently
6. **Phase 6**: Deprecate manual configuration editing

## 📚 Additional Resources

- [GCP Project Configuration](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
- [Cloud Run Environment Variables](https://cloud.google.com/run/docs/configuring/environment-variables)
- [Vertex AI Regional Endpoints](https://cloud.google.com/vertex-ai/docs/general/locations)

## 🆘 Troubleshooting

### Wrong configuration loaded
```bash
# Check current account
echo $ACCOUNT_ENV

# Verify configuration
python -c "from config.config_loader import load_config; \
           import os; \
           print(load_config(os.environ.get('ACCOUNT_ENV', 'develom')).ACCOUNT_NAME)"
```

### Account not found error
- Ensure `ACCOUNT_ENV` is set correctly
- Verify account directory exists in `backend/config/`
- Check for typos in account name

### Import errors
- Ensure all `__init__.py` files exist
- Verify Python path includes the backend directory
- Check that config files have valid Python syntax

---

**Last Updated:** 2025-10-09  
**Maintainer:** hector@develom.com
