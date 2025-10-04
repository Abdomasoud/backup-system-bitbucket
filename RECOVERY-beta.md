# 🔄 Repository Recovery Guide

## 📋 **Overview**

This guide explains how to recover your repositories when disaster strikes. Your backup system creates multiple recovery options:

1. **📦 Local .tar.gz Archives** - Complete repository backups with metadata
2. **🔄 Mirror Repositories** - Live backup repositories in another workspace
3. **📊 Metadata Files** - Pull requests, issues, settings, permissions

---

## 🚨 **Recovery Scenarios**

### **Scenario 1: Repository Accidentally Deleted**
### **Scenario 2: Repository Corrupted** 
### **Scenario 3: Workspace Compromised**
### **Scenario 4: Complete Bitbucket Account Loss**

---

## 🔧 **Recovery Methods**

## **Method 1: Quick Recovery from Mirror Repository** ⚡

**Best for:** Fast recovery when main repo is deleted but workspace is intact

```bash
# 1. Check available mirror repositories
curl -u "your-email@domain.com:your-api-token" \
  "https://api.bitbucket.org/2.0/repositories/your-backup-workspace" | jq '.values[].name'

# 2. Clone the mirror repository
git clone https://your-username:your-api-token@bitbucket.org/your-backup-workspace/repo-name.git

# 3. Push to recreated original repository
cd repo-name
git remote add original https://your-username:your-api-token@bitbucket.org/original-workspace/repo-name.git
git push original --all
git push original --tags
```

---

## **Method 2: Full Recovery from .tar.gz Archive** 📦

**Best for:** Complete disaster recovery with all metadata

### **Step 1: Extract the Backup**

```bash
# Navigate to backup location
cd /opt/bitbucket-backup/repositories/your-repo-name

# List available backups (newest first)
ls -lt *.tar.gz

# Extract the latest backup
LATEST_BACKUP=$(ls -t *.tar.gz | head -1)
echo "Restoring from: $LATEST_BACKUP"

# Create recovery workspace
mkdir -p /tmp/recovery
cd /tmp/recovery
tar -xzf "/opt/bitbucket-backup/repositories/your-repo-name/$LATEST_BACKUP"
```

### **Step 2: Recover Git Repository**

```bash
# Navigate to extracted backup
cd /tmp/recovery

# Option A: From mirror repository
if [ -d "repo.git" ]; then
    echo "🔄 Recovering from mirror repository..."
    git clone --bare repo.git recovered-repo.git
    cd recovered-repo.git
    
    # Push to new repository
    git remote add origin https://username:token@bitbucket.org/workspace/new-repo-name.git
    git push --mirror origin
fi

# Option B: From working copy
if [ -d "working" ]; then
    echo "📁 Recovering from working copy..."
    cd working
    
    # Add new remote and push
    git remote add new-origin https://username:token@bitbucket.org/workspace/new-repo-name.git
    git push new-origin --all
    git push new-origin --tags
fi
```

### **Step 3: Recover Metadata** 

```bash
# Check what metadata was backed up
if [ -f "metadata.json" ]; then
    echo "📊 Available metadata:"
    cat metadata.json | jq '{
        pull_requests: .total_prs,
        issues: .total_issues,
        branches: .total_branches,
        wiki_pages: .wiki_pages_count,
        webhooks: .total_webhooks
    }'
fi

# Extract key information for manual recreation
echo "🔍 Pull Requests to recreate:"
cat metadata.json | jq -r '.pull_requests[]? | "- \(.title) (\(.source.branch.name) → \(.destination.branch.name)) - \(.state)"'

echo "🐛 Issues to recreate:"
cat metadata.json | jq -r '.issues[]? | "- \(.title) - \(.state) - Priority: \(.priority // "Normal")"'
```

---

## **Method 3: Emergency Recovery Script** 🆘

Create an automated recovery script:

```bash
#!/bin/bash
# Emergency Repository Recovery Script

REPO_NAME="$1"
TARGET_WORKSPACE="$2"
BACKUP_DATE="${3:-latest}"

if [[ -z "$REPO_NAME" || -z "$TARGET_WORKSPACE" ]]; then
    echo "Usage: $0 <repo_name> <target_workspace> [backup_date]"
    echo "Example: $0 payment-repo hospital-backend-restored"
    echo "         $0 payment-repo hospital-backend-restored 20251002_114538"
    exit 1
fi

echo "🚨 EMERGENCY RECOVERY STARTED"
echo "Repository: $REPO_NAME"
echo "Target Workspace: $TARGET_WORKSPACE"
echo "=================================="

# Set paths
BACKUP_BASE="/opt/bitbucket-backup"
RECOVERY_DIR="/tmp/emergency-recovery-$$"

# Find backup
if [[ "$BACKUP_DATE" == "latest" ]]; then
    BACKUP_FILE=$(ls -t "$BACKUP_BASE/repositories/$REPO_NAME"/*.tar.gz | head -1)
else
    BACKUP_FILE="$BACKUP_BASE/repositories/$REPO_NAME/${REPO_NAME}_${BACKUP_DATE}.tar.gz"
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    echo "Available backups:"
    ls -la "$BACKUP_BASE/repositories/$REPO_NAME"/*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

echo "📦 Using backup: $BACKUP_FILE"

# Extract backup
mkdir -p "$RECOVERY_DIR"
cd "$RECOVERY_DIR"
echo "📤 Extracting backup..."
tar -xzf "$BACKUP_FILE"

# Create new repository (you need to do this manually in Bitbucket first)
echo "⚠️  MANUAL STEP REQUIRED:"
echo "1. Go to https://bitbucket.org/$TARGET_WORKSPACE"
echo "2. Create new repository named: $REPO_NAME"
echo "3. Press ENTER when done..."
read -p "Continue? "

# Push repository data
echo "🔄 Pushing repository data..."
if [[ -d "repo.git" ]]; then
    cd repo.git
    git remote add recovery "https://$BITBUCKET_USERNAME:$BITBUCKET_API_TOKEN@bitbucket.org/$TARGET_WORKSPACE/$REPO_NAME.git"
    git push --mirror recovery
    echo "✅ Repository code restored!"
else
    echo "❌ No repository data found in backup"
fi

# Show metadata summary
if [[ -f "$RECOVERY_DIR/metadata.json" ]]; then
    echo ""
    echo "📊 METADATA SUMMARY:"
    echo "===================="
    cat "$RECOVERY_DIR/metadata.json" | jq -r '
        "Pull Requests: " + (.total_prs // 0 | tostring),
        "Issues: " + (.total_issues // 0 | tostring),
        "Branches: " + (.total_branches // 0 | tostring),
        "Wiki Pages: " + (.wiki_pages_count // 0 | tostring)
    '
    
    echo ""
    echo "📋 MANUAL RECREATION NEEDED:"
    echo "============================"
    echo "Pull Requests, Issues, and Wiki pages need manual recreation."
    echo "Detailed data available in: $RECOVERY_DIR/metadata.json"
fi

echo ""
echo "✅ RECOVERY COMPLETED!"
echo "Cleanup: rm -rf $RECOVERY_DIR"
```

Save this script as `/opt/bitbucket-backup/scripts/emergency-recovery.sh` and make it executable:

```bash
chmod +x /opt/bitbucket-backup/scripts/emergency-recovery.sh
```

---

## **Method 4: Cross-Platform Recovery** 🌍

**For recovering on different systems:**

### **Download Backups from Server**

```bash
# From your local machine, download backups
scp -r root@your-server:/opt/bitbucket-backup/repositories/ ./local-backups/

# Or create a downloadable archive
ssh root@your-server "cd /opt/bitbucket-backup && tar -czf bitbucket-backups.tar.gz repositories/ metadata/"
scp root@your-server:/opt/bitbucket-backup/bitbucket-backups.tar.gz ./
```

### **Recovery on Local Machine**

```bash
# Extract backups locally
tar -xzf bitbucket-backups.tar.gz

# Use any git client to push to new repositories
cd repositories/your-repo-name/latest-timestamp/working
git remote add new-repo https://username:token@bitbucket.org/new-workspace/repo-name.git
git push new-repo --all
git push new-repo --tags
```

---

## **Method 5: Metadata Recreation Guide** 📊

### **Pull Request Recreation**

```bash
# Extract PR information for manual recreation
cat metadata.json | jq -r '.pull_requests[]? | 
"Title: \(.title)
Description: \(.description // "No description")
Source: \(.source.branch.name) → \(.destination.branch.name)  
Author: \(.author.display_name)
State: \(.state)
Created: \(.created_on)
---"'
```

### **Issues Recreation**

```bash
# Extract issue information
cat metadata.json | jq -r '.issues[]? |
"Title: \(.title)
Content: \(.content.raw // "No content")
Priority: \(.priority // "normal")
State: \(.state)
Reporter: \(.reporter.display_name)
---"'
```

### **Branch Recreation**

```bash
# List all branches that should exist
cat metadata.json | jq -r '.branches[]? | .name'

# Check if branches exist in recovered repo
git branch -a
```

---

## ⚡ **Quick Recovery Commands**

### **Emergency One-Liners**

```bash
# Quick mirror recovery
git clone https://user:token@bitbucket.org/backup-workspace/repo-name.git && cd repo-name && git remote add original https://user:token@bitbucket.org/original-workspace/repo-name.git && git push original --mirror

# Quick archive recovery
cd /tmp && tar -xzf /opt/bitbucket-backup/repositories/repo-name/repo-name_*.tar.gz && cd working && git remote add recovered https://user:token@bitbucket.org/workspace/repo-name.git && git push recovered --all

# List all available backups
find /opt/bitbucket-backup/repositories -name "*.tar.gz" | sort
```

---

## 🔍 **Recovery Verification**

After recovery, verify completeness:

```bash
# Check repository
git log --oneline | head -10
git branch -a
git tag

# Compare with metadata
echo "Expected branches: $(cat metadata.json | jq '.total_branches')"
echo "Actual branches: $(git branch -a | wc -l)"

echo "Expected tags: $(cat metadata.json | jq '.total_tags')"  
echo "Actual tags: $(git tag | wc -l)"
```

---

## 🚨 **Emergency Contacts & Information**

### **Backup Locations**
- **Primary**: `/opt/bitbucket-backup/repositories/`
- **Metadata**: `/opt/bitbucket-backup/metadata/`
- **Logs**: `/opt/bitbucket-backup/logs/`

### **Key Files**
- **Configuration**: `/opt/bitbucket-backup/config/.env`
- **Scripts**: `/opt/bitbucket-backup/scripts/`
- **Recovery Script**: `/opt/bitbucket-backup/scripts/emergency-recovery.sh`

### **Backup Schedule**
- **Frequency**: Every 3 days
- **Retention**: 5 backups per repository
- **Mirror Sync**: Real-time with each backup

---

## 📞 **Need Help?**

1. **Check logs**: `tail -f /opt/bitbucket-backup/logs/*.log`
2. **Test connection**: `/opt/bitbucket-backup/scripts/bitbucket-backup.sh --test-only`
3. **Force backup**: `/opt/bitbucket-backup/scripts/bitbucket-backup.sh --force`

---

**Remember**: Mirror repositories provide the fastest recovery, but .tar.gz archives contain complete metadata including pull requests and issues! 🛡️