# Setup Guide - Windows

Complete setup instructions for running Spark Insight Agent on Windows systems (local Docker setup).

---

## Prerequisites

- **Windows 10/11** (64-bit)
- **Python 3.9+** installed
- **Docker Desktop** installed and running
- **OpenAI API Key** (get one from https://platform.openai.com/api-keys)
- **PowerShell** or **Command Prompt**

💡 **Recommended:** Use **WSL2** (Windows Subsystem for Linux) for the best experience. If using WSL2, follow the [macOS/Linux guide](SETUP_GUIDE_MACOS_LINUX.md) instead.

---

## Important: Choose Your Approach

### Option A: WSL2 (Recommended) ⭐

Best experience, fewer issues, faster performance:

```powershell
# In PowerShell (Admin)
wsl --install

# After installation and reboot, open Ubuntu and follow:
# SETUP_GUIDE_MACOS_LINUX.md
```

### Option B: Native Windows

Continue with this guide for native Windows setup using PowerShell.

---

## Step 1: Install Python

If Python is not installed:

1. Download from https://www.python.org/downloads/
2. ✅ **Important:** Check "Add Python to PATH" during installation
3. Verify installation:

```powershell
python --version
# Should show: Python 3.9.x or higher
```

---

## Step 2: Install Docker Desktop

1. Download from https://www.docker.com/products/docker-desktop
2. Install Docker Desktop
3. Launch Docker Desktop
4. Wait for "Docker Desktop is running" in system tray
5. Verify installation:

```powershell
docker --version
```

---

## Step 3: Navigate to Project Directory

```powershell
cd C:\path\to\spark_incident_analyser
```

---

## Step 4: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv myenv

# Activate (PowerShell)
.\myenv\Scripts\Activate.ps1

# If you get execution policy error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Verify activation:** You should see `(myenv)` in your prompt.

**Alternative activation methods:**

```cmd
# Command Prompt
myenv\Scripts\activate.bat

# Git Bash
source myenv/Scripts/activate
```

---

## Step 5: Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

**✅ This installs:** OpenAI SDK, Qdrant client, Streamlit, NumPy, and other dependencies.

---

## Step 6: Start Qdrant (Local Vector Database)

Start Qdrant in a Docker container:

```powershell
# Start Qdrant
docker run -d `
  --name qdrant `
  -p 6333:6333 `
  -v ${PWD}/qdrant_storage:/qdrant/storage `
  qdrant/qdrant
```

**Note:** PowerShell uses backticks `` ` `` for line continuation (not backslash `\`).

**Verify Qdrant is running:**

```powershell
# Check container status
docker ps | Select-String qdrant

# Test connection (PowerShell)
Invoke-WebRequest http://localhost:6333/collections

# Test connection (using curl if installed)
curl http://localhost:6333/collections
```

**Expected response:** JSON with `"status":"ok"`

---

## Step 7: Configure Environment Variables

Create a `.env` file in the project root:

### Using PowerShell:

```powershell
@"
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
QDRANT_URL=http://localhost:6333
"@ | Out-File -FilePath .env -Encoding utf8
```

### Using Command Prompt:

```cmd
echo OPENAI_API_KEY=sk-proj-your-actual-api-key-here > .env
echo QDRANT_URL=http://localhost:6333 >> .env
```

### Or manually create `.env` file:

Use VS Code, Notepad++, or any text editor (NOT Windows Notepad):

```
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
QDRANT_URL=http://localhost:6333
```

**⚠️ Important:** Replace `sk-proj-your-actual-api-key-here` with your real OpenAI API key!

**Test your configuration:**

```powershell
python backend/test_connection.py
```

**Expected output:**
```
✅ Qdrant connection successful!
GetCollectionsResponse(collections=[])
```

---

## Step 8: Ingest Sample Incident Data

Load the 20 sample incidents into Qdrant:

```powershell
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

```powershell
Invoke-WebRequest http://localhost:6333/collections/spark-incidents-openai
```

Look for `"points_count": 20` in the response.

---

## Step 9: Run the Application

Start the Streamlit web interface:

```powershell
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

## Step 10: Test with Sample Queries

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

```powershell
# 1. Navigate to project
cd C:\path\to\spark_incident_analyser

# 2. Activate virtual environment
.\myenv\Scripts\Activate.ps1

# 3. Ensure Qdrant is running
docker ps | Select-String qdrant
# If not running:
docker start qdrant

# 4. Run the app
streamlit run main.py
```

---

## Stopping the Application

```powershell
# Stop Streamlit
# Press Ctrl+C in the terminal where it's running

# Stop Qdrant container
docker stop qdrant

# Deactivate virtual environment
deactivate
```

---

## Managing Qdrant Container

```powershell
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
Remove-Item -Recurse -Force qdrant_storage
```

---

## Adding Your Own Incident Data

### Method 1: Create Text Files Manually

1. Create new `.txt` files in the `spark_incidents\` folder
2. Use this format:

```
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
```

3. Re-run ingestion:

```powershell
python ingestion_qdrant.py
```

---

## Updating Dependencies

```powershell
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade openai

# Save current versions
pip freeze > requirements.txt
```

---

## Checking System Status

```powershell
# Check Python version
python --version

# Check virtual environment is activated
Get-Command python
# Should show path inside myenv\Scripts\

# List installed packages
pip list

# Check Docker is running
docker info

# Check Qdrant status
Invoke-WebRequest http://localhost:6333/health

# View Qdrant collections
Invoke-WebRequest http://localhost:6333/collections

# Check specific collection
Invoke-WebRequest http://localhost:6333/collections/spark-incidents-openai
```

---

## Backup and Restore

### Backup Qdrant Data

```powershell
# Create backup folder
New-Item -ItemType Directory -Force -Path backups

# Copy qdrant_storage
Copy-Item -Recurse qdrant_storage backups\qdrant_backup_$(Get-Date -Format "yyyyMMdd")

# Or compress it
Compress-Archive -Path qdrant_storage -DestinationPath backups\qdrant_backup_$(Get-Date -Format "yyyyMMdd").zip
```

### Restore Qdrant Data

```powershell
# Stop Qdrant
docker stop qdrant

# Remove current data
Remove-Item -Recurse -Force qdrant_storage

# Restore from backup
Copy-Item -Recurse backups\qdrant_backup_20240315 qdrant_storage

# Or extract from zip
Expand-Archive -Path backups\qdrant_backup_20240315.zip -DestinationPath .

# Start Qdrant
docker start qdrant
```

---

## Performance Optimization

### Docker Desktop Settings

1. Open Docker Desktop
2. Go to Settings → Resources
3. Adjust:
   - **CPUs:** 4+ cores
   - **Memory:** 4GB+ RAM
   - **Swap:** 1GB+
   - **Disk image size:** 60GB+

### Enable WSL2 Backend (Faster)

1. Docker Desktop → Settings → General
2. ✅ Enable "Use the WSL 2 based engine"
3. Restart Docker Desktop

### Windows Defender Exclusions

Add project folder to exclusions for better performance:

1. Windows Security → Virus & threat protection
2. Manage settings → Exclusions
3. Add: `C:\path\to\spark_incident_analyser\myenv`
4. Add: `C:\path\to\spark_incident_analyser\qdrant_storage`

---

## Environment Variables Reference

Your `.env` file should contain:

```
# Required
OPENAI_API_KEY=sk-proj-your-key-here

# Local Qdrant (Docker)
QDRANT_URL=http://localhost:6333

# Note: QDRANT_API_KEY not needed for local setup

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

```powershell
# 1. Stop and remove Qdrant container
docker stop qdrant
docker rm qdrant

# 2. Remove Qdrant data
Remove-Item -Recurse -Force qdrant_storage

# 3. Remove virtual environment
Remove-Item -Recurse -Force myenv

# 4. Remove .env file (contains API key)
Remove-Item .env

# 5. (Optional) Remove cache files
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
```

---

## PowerShell Command Reference

Common Unix commands and their PowerShell equivalents:

| Unix | PowerShell |
|------|-----------|
| `ls` | `Get-ChildItem` or `dir` |
| `cat file.txt` | `Get-Content file.txt` |
| `grep text` | `Select-String text` |
| `rm -rf folder` | `Remove-Item -Recurse -Force folder` |
| `cp file dest` | `Copy-Item file dest` |
| `mv file dest` | `Move-Item file dest` |
| `export VAR=value` | `$env:VAR = "value"` |
| `echo $VAR` | `$env:VAR` |
| `which python` | `Get-Command python` |
| `curl url` | `Invoke-WebRequest url` |

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
👉 [TROUBLESHOOTING_WINDOWS.md](TROUBLESHOOTING_WINDOWS.md)

Common issues covered:
- PowerShell execution policy errors
- Docker Desktop problems
- Virtual environment activation
- Path and permission issues
- Port conflicts
- Line ending issues (CRLF vs LF)

---

## Need Help?

- **Troubleshooting:** [TROUBLESHOOTING_WINDOWS.md](TROUBLESHOOTING_WINDOWS.md)
- **Quick reference:** [QUICK_START.md](QUICK_START.md)
- **Architecture details:** [README.md](README.md)
- **macOS/Linux guide:** [SETUP_GUIDE_MACOS_LINUX.md](SETUP_GUIDE_MACOS_LINUX.md)

---

**Last Updated:** March 2026
**Tested on:** Windows 10 (22H2), Windows 11 (23H2)
**Recommended:** Use WSL2 for best experience
