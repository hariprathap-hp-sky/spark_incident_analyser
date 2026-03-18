# Setup Guide - macOS & Linux

Complete setup instructions for running Spark Insight Agent on macOS and Linux systems (local Docker setup).

---

## Prerequisites

- **Python 3.9+** installed
- **Docker** installed and running
- **OpenAI API Key** (get one from https://platform.openai.com/api-keys)
- **Terminal** access (bash/zsh)

---

## Step 1: Navigate to Project Directory

```bash
cd /path/to/spark_incident_analyser
```

---

## Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv myenv

# Activate it
source myenv/bin/activate

# You should see (myenv) in your terminal prompt
```

---

## Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

**✅ This installs:** OpenAI SDK, Qdrant client, Streamlit, NumPy, and other dependencies with proper SSL compatibility.

---

## Step 4: Start Qdrant (Local Vector Database)

Start Qdrant in a Docker container:

```bash
# Option 1: Using Makefile
make start-qdrant

# Option 2: Direct Docker command
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

**Verify Qdrant is running:**

```bash
# Check container status
docker ps | grep qdrant

# Test connection
curl http://localhost:6333/collections
```

**Expected response:** `{"result":{"collections":[]},"status":"ok",...}`

---

## Step 5: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cat > .env << 'EOF'
# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-your-actual-api-key-here

# Qdrant Configuration (Local Docker)
QDRANT_URL=http://localhost:6333

# Note: QDRANT_API_KEY not needed for local Docker setup
EOF
```

**⚠️ Important:** Replace `sk-proj-your-actual-api-key-here` with your real OpenAI API key!

**Test your configuration:**

```bash
python backend/test_connection.py
```

**Expected output:**
```
✅ Qdrant connection successful!
GetCollectionsResponse(collections=[])
```

---

## Step 6: Ingest Sample Incident Data

Load the 20 sample incidents into Qdrant:

```bash
python ingestion_qdrant.py
```

**Expected output:**
```
🚀 Loading Spark incident reports...
✅ Collection 'spark-incidents-openai' created
📄 Found 20 incident files
✅ Processed: INC-2024-001.txt (1 chunks)
...
✅ Ingested 20 chunks into Qdrant!
```

**Verify data was loaded:**

```bash
curl http://localhost:6333/collections/spark-incidents-openai
```

Look for `"points_count": 20` in the response.

---

## Step 7: Run the Application

Start the Streamlit web interface:

```bash
streamlit run main.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

**Open your browser:** http://localhost:8501

---

## Step 8: Test with Sample Queries

Try these queries in the Streamlit interface:

```
What caused the executor lost issue in INC-2024-001?
Show me all memory-related incidents
What are common patterns in OOM errors?
How do we fix data skew issues?
Summarize shuffle service failures
```

---

## Daily Usage (After Initial Setup)

After the first-time setup, you only need these commands:

```bash
# 1. Navigate to project
cd /path/to/spark_incident_analyser

# 2. Activate virtual environment
source myenv/bin/activate

# 3. Ensure Qdrant is running
docker ps | grep qdrant || docker start qdrant

# 4. Run the app
streamlit run main.py
```

---

## Stopping the Application

```bash
# Stop Streamlit
# Press Ctrl+C in the terminal where it's running

# Stop Qdrant container
docker stop qdrant

# Deactivate virtual environment
deactivate
```

---

## Managing Qdrant Container

```bash
# Start existing container
docker start qdrant

# Stop container
docker stop qdrant

# Restart container
docker restart qdrant

# View container logs
docker logs qdrant

# Remove container (data persists in qdrant_storage/)
docker stop qdrant
docker rm qdrant

# Remove container AND data
docker stop qdrant
docker rm qdrant
rm -rf qdrant_storage
```

---

## Adding Your Own Incident Data

### Method 1: Add Text Files

1. **Create incident files** in `spark_incidents/` directory:

```bash
cat > spark_incidents/INC-2024-021.txt << 'EOF'
Incident ID: INC-2024-021
Date: 2024-03-15
Cluster: Spark-Cluster-B
Application: ETL Pipeline
Error Summary: Job failed with OutOfMemoryError during aggregation
Root Cause: Insufficient driver memory for collect operation
Resolution:
  - Increased driver memory from 2g to 8g
  - Changed collect() to write() for large datasets
Key Learnings: Avoid collect() on large datasets
Work Notes:
Driver ran out of memory during final aggregation step.
Changed logic to write results directly to storage.
Job completed successfully after changes.
EOF
```

2. **Re-run ingestion:**

```bash
python ingestion_qdrant.py
```

The script will recreate the collection with all incidents.

### Method 2: Append Without Recreating

To add new incidents without recreating the entire collection, modify `ingestion_qdrant.py`:

```python
# Comment out this line:
# qdrant.recreate_collection(...)

# Use create_collection with exist_ok parameter instead
# Or use upsert directly if collection exists
```

---

## Updating Dependencies

If you need to update packages:

```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade openai

# Freeze current versions
pip freeze > requirements.txt
```

---

## Checking System Status

```bash
# Check Python version
python3 --version

# Check virtual environment is activated
which python
# Should show: /path/to/spark_incident_analyser/myenv/bin/python

# List installed packages
pip list

# Check Docker is running
docker info

# Check Qdrant status
curl http://localhost:6333/health

# View Qdrant collections
curl http://localhost:6333/collections

# Check specific collection
curl http://localhost:6333/collections/spark-incidents-openai
```

---

## Backup and Restore

### Backup Qdrant Data

```bash
# Method 1: Backup storage directory
tar -czf qdrant_backup_$(date +%Y%m%d).tar.gz qdrant_storage/

# Method 2: Docker volume backup
docker run --rm \
  -v $(pwd)/qdrant_storage:/source \
  -v $(pwd):/backup \
  alpine tar -czf /backup/qdrant_backup.tar.gz -C /source .
```

### Restore Qdrant Data

```bash
# Stop Qdrant
docker stop qdrant

# Extract backup
tar -xzf qdrant_backup_20240315.tar.gz

# Start Qdrant
docker start qdrant
```

---

## Performance Optimization

### For macOS

```bash
# Allocate more resources to Docker Desktop
# Docker Desktop → Preferences → Resources
# - CPUs: 4+
# - Memory: 4GB+
# - Swap: 1GB+

# Exclude project from Time Machine
tmutil addexclusion myenv/
tmutil addexclusion qdrant_storage/
```

### For Linux

```bash
# Check available resources
free -h
df -h

# Optimize Docker
# Edit /etc/docker/daemon.json if needed
```

---

## Environment Variables Reference

Create or edit `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-proj-your-key-here

# Local Qdrant (Docker)
QDRANT_URL=http://localhost:6333
# QDRANT_API_KEY not needed for local setup

# Optional: Customize collection name
# QDRANT_COLLECTION=spark-incidents-openai

# Optional: Database (if using PostgreSQL source)
# DB_USER=postgres
# DB_PASSWORD=your-password
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=spark_incidents
```

---

## Uninstall / Cleanup

To completely remove the installation:

```bash
# 1. Stop and remove Qdrant container
docker stop qdrant
docker rm qdrant

# 2. Remove Qdrant data
rm -rf qdrant_storage/

# 3. Remove virtual environment
rm -rf myenv/

# 4. Remove .env file (contains API key)
rm .env

# 5. (Optional) Remove cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

---

## Docker-Free Setup (Advanced)

If you prefer not to use Docker, you can install Qdrant directly:

### macOS (Homebrew)

```bash
# Install Qdrant
brew install qdrant

# Run Qdrant
qdrant --config-path ./qdrant_config.yaml
```

### Linux

```bash
# Download Qdrant
wget https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz

# Extract
tar xzf qdrant-x86_64-unknown-linux-gnu.tar.gz

# Run
./qdrant
```

**Note:** Docker is the recommended approach for easier management.

---

## Cost Estimates

Based on current OpenAI API pricing:

| Operation | Cost per Query | Note |
|-----------|---------------|------|
| Embedding (first time) | ~$0.00001 | Cached after first use |
| Embedding (cached) | $0 | No API call |
| LLM (when needed) | ~$0.0001-$0.0002 | Only ~25% of queries |
| LLM (cached) | $0 | No API call |
| Qdrant (local) | $0 | Self-hosted |

**Monthly estimates:**
- 1000 queries/day, mostly cached: **~$3-6/month**
- First-time queries only: **~$6-12/month**
- Mix of new and cached: **~$1.50-6/month**

---

## Troubleshooting

Having issues? Check the troubleshooting guide:
👉 [TROUBLESHOOTING_MACOS_LINUX.md](TROUBLESHOOTING_MACOS_LINUX.md)

Common issues covered:
- SSL/OpenSSL errors
- Qdrant connection problems
- Docker issues
- Import errors
- Permission problems
- Port conflicts

---

## Need Help?

- **Troubleshooting:** [TROUBLESHOOTING_MACOS_LINUX.md](TROUBLESHOOTING_MACOS_LINUX.md)
- **Quick reference:** [QUICK_START.md](QUICK_START.md)
- **Architecture details:** [README.md](README.md)
- **Code documentation:** See comments in `backend/core_qdrant.py`

---

**Last Updated:** March 2026
**Tested on:** macOS 14.x, Ubuntu 22.04, Debian 12
