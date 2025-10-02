# 🚀 Ultra-Simple Ubuntu 22+ Deployment Guide

## 🎯 **What This Creates**

Your **complete Bitbucket backup system** that:
- ✅ **Auto-discovers ALL repositories** in your workspace
- ✅ **Creates mirror repositories** in backup workspace 
- ✅ **Generates .tar.gz backups** every 3 days
- ✅ **Maintains 5 backups per repo** (15-day retention)
- ✅ **Organizes each repo in its own folder**
- ✅ **No virtual environment complexity** - works directly with system Python

---

## 🛠 **Step-by-Step Deployment**

### **Step 1: Fresh Ubuntu Server**
```bash
# Connect to your Ubuntu 22+ server
ssh ubuntu@your-server-ip

# Become root user (recommended)
sudo -i
```

### **Step 2: Clone & Setup**
```bash
# Clone the backup system
git clone https://github.com/Abdomasoud/backup-system-bitbucket.git
cd backup-system-bitbucket

# Run the automated setup (installs everything)
bash setup.sh
```

**What setup.sh does:**
- ✅ Installs system dependencies (git, python3, curl, jq)
- ✅ Installs Python packages (requests, python-dotenv)
- ✅ Creates `/opt/bitbucket-backup/` structure
- ✅ Copies all backup scripts
- ✅ Creates cron wrapper for automation

### **Step 3: Configure Credentials**
```bash
# Edit configuration file
nano /opt/bitbucket-backup/config/.env
```

**Set these values:**
```bash
ATLASSIAN_EMAIL=your-email@domain.com
BITBUCKET_API_TOKEN=your-api-token-here
BITBUCKET_WORKSPACE=your-source-workspace
BACKUP_WORKSPACE=your-backup-workspace
```

### **Step 4: Test Your Setup**
```bash
# Change to backup directory
cd /opt/bitbucket-backup

# Test API connection
./scripts/bitbucket-backup.sh --test-only
```

**Expected output:**
```
✅ All dependencies are available
✅ Configuration validation passed  
✅ Bitbucket API connection successful
ℹ️  Found 3 repositories in workspace
✅ Connection test completed successfully!
```

### **Step 5: Run Your First Backup**
```bash
# Force first backup (ignores 3-day schedule)
./scripts/bitbucket-backup.sh --force
```

**What happens:**
1. **Discovers all repositories** in your workspace
2. **Creates mirror repositories** in backup workspace
3. **Clones each repository locally**
4. **Creates compressed .tar.gz backups**
5. **Organizes backups by repository name**
6. **Saves metadata** (repository info, backup history)

---

## 📁 **Result: Perfect Organization**

After backup, you'll have:
```
/opt/bitbucket-backup/
├── repositories/
│   ├── project-alpha/
│   │   ├── project-alpha_20251002_140000.tar.gz
│   │   └── project-alpha_20251005_140000.tar.gz
│   ├── project-beta/
│   │   ├── project-beta_20251002_140000.tar.gz
│   │   └── project-beta_20251005_140000.tar.gz
│   └── website/
│       └── website_20251002_140000.tar.gz
├── metadata/
│   ├── project-alpha_metadata.json
│   ├── project-beta_metadata.json
│   └── backup_history.json
└── logs/
    └── backup_20251002_140000.log
```

---

## ⏰ **Enable Automation (Optional)**

```bash
# Add to root's cron
crontab -e

# Add this line for backup every 3 days at 2 AM
0 2 */3 * * /opt/bitbucket-backup/scripts/cron-wrapper.sh >> /opt/bitbucket-backup/logs/cron.log 2>&1
```

---

## 🔑 **Getting Your Bitbucket API Token**

1. **Go to:** https://bitbucket.org/account/settings/app-passwords/
2. **Click:** "Create app password" 
3. **Name:** `backup-system`
4. **Permissions:** 
   - ✅ **Repositories: Read**
   - ✅ **Account: Read**
5. **Copy the generated token** (save it immediately!)
6. **Use this token** as `BITBUCKET_API_TOKEN` in your `.env` file

---

## 💡 **Backup Workspace Explained**

**BACKUP_WORKSPACE** is where your **mirror repositories** will be created:

### Example:
```bash
# Your source workspace (original repos)
BITBUCKET_WORKSPACE=mycompany

# Your backup workspace (mirrors)  
BACKUP_WORKSPACE=mycompany-backups
```

### Results in:
- **Original:** `https://bitbucket.org/mycompany/project-alpha`
- **Mirror:** `https://bitbucket.org/mycompany-backups/project-alpha-backup-mirror`

**Options for BACKUP_WORKSPACE:**
1. **Create new workspace:** `mycompany-backups` (recommended)
2. **Use same workspace:** `mycompany` (mirrors alongside originals)
3. **Use personal account:** `your-username`

---

## 🧪 **Testing Commands**

```bash
# Test API connection
./scripts/bitbucket-backup.sh --test-only

# Force backup (ignore schedule)
./scripts/bitbucket-backup.sh --force  

# Normal run (follows 3-day schedule)
./scripts/bitbucket-backup.sh

# Show help
./scripts/bitbucket-backup.sh --help
```

---

## 🐛 **Troubleshooting**

### **Problem: API Authentication Failed**
```bash
# Check your credentials
cat /opt/bitbucket-backup/config/.env

# Test manually
curl -u "email@domain.com:your-token" https://api.bitbucket.org/2.0/user
```

### **Problem: Workspace Not Found**  
- ✅ Check `BITBUCKET_WORKSPACE` spelling
- ✅ Ensure you have access to the workspace
- ✅ Use workspace **slug** (URL name), not display name

### **Problem: Permission Denied**
```bash
# Make sure you're root user
whoami  # Should show 'root'

# Fix permissions if needed
chmod +x /opt/bitbucket-backup/scripts/*.sh
```

### **Problem: Python Import Errors**
```bash
# Verify Python packages
python3 -c "import requests, dotenv; print('✅ All good!')"

# Reinstall if needed
pip3 install --break-system-packages requests python-dotenv
```

---

## 🎉 **You're Done!**

Your system is now:
- ✅ **Fully automated** - backs up every 3 days
- ✅ **Organized** - each repo gets its own folder  
- ✅ **Retention managed** - keeps 5 backups per repo
- ✅ **Mirror protected** - copies stored in backup workspace
- ✅ **Logged** - comprehensive backup logs
- ✅ **Simple** - no virtual environments or complex dependencies

**Next backup:** Runs automatically in 3 days, or run `--force` anytime! 🚀