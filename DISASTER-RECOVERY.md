# 🚨 Disaster Recovery & Troubleshooting Guide

Emergency procedures, backup restoration, and comprehensive troubleshooting for the Bitbucket Migration & Backup System.

## 🔄 Backup Restoration

### Quick Restore Procedure

#### 1. Locate Backup Files
```bash
# List available backups
ls -la /opt/bitbucket-backup/backups/
ls -la /opt/bitbucket-backup/backups/workspace_name/repo_name/
```

#### 2. Extract Repository Backup
```bash
# Navigate to restore location
cd /tmp/restore

# Extract backup (replace with your backup file)
tar -xzf /opt/bitbucket-backup/backups/workspace/repo/20241004_120000.tar.gz

# The extracted folder contains:
# - Git repository (.git folder)
# - All files and history
# - Metadata (issues, wiki, etc.)
```

#### 3. Restore to Bitbucket
```bash
# Clone from extracted backup
cd extracted_repo_folder

# Add new remote repository
git remote add restore https://bitbucket.org/workspace/new-repo.git

# Push all branches and tags
git push restore --all
git push restore --tags
```

### Automated Restore Script

```bash
# Use the built-in restore script
sudo /opt/bitbucket-backup/scripts/quick-restore.sh

# Follow interactive prompts:
# 1. Select workspace
# 2. Select repository
# 3. Choose backup date
# 4. Specify destination
```

### Metadata Restoration

#### Issues and Pull Requests
```bash
# Extract metadata from backup
cd backup_folder/metadata/

# Contains JSON files:
ls -la
# issues.json         - All issues with comments
# pull_requests.json  - PR information and discussions
# wiki.json          - Wiki pages and content
# collaborators.json - Team members and permissions
```

#### Manual Metadata Import
```bash
# Use Python script for metadata restoration
cd /opt/bitbucket-backup
python3 -c "
from bitbucket_backup import BitbucketMigrationSystem
system = BitbucketMigrationSystem()
system.restore_repository_metadata('workspace', 'repository', '/path/to/metadata')
"
```

## 🚨 Emergency Procedures

### System Failure Recovery

#### 1. Service Not Running
```bash
# Check service status
sudo systemctl status bitbucket-backup.service

# If failed, restart service
sudo systemctl restart bitbucket-backup.service

# Check logs for errors
sudo journalctl -u bitbucket-backup.service --since="1 hour ago"
```

#### 2. Configuration Corruption
```bash
# Backup current config
sudo cp /opt/bitbucket-backup/config/.env /tmp/.env.backup

# Restore from template
sudo cp /opt/bitbucket-backup/config/.env.template /opt/bitbucket-backup/config/.env

# Edit with correct credentials
sudo nano /opt/bitbucket-backup/config/.env

# Test configuration
python3 bitbucket-backup.py test
```

#### 3. Disk Space Issues
```bash
# Check disk usage
df -h /opt/bitbucket-backup/

# Clean old logs (keeps last 10 files)
sudo find /opt/bitbucket-backup/logs/ -name "*.log" -type f | sort | head -n -10 | xargs sudo rm -f

# Clean old backups (manual cleanup)
sudo find /opt/bitbucket-backup/backups/ -name "*.tar.gz" -mtime +30 -delete
```

### Network/API Issues

#### 1. API Rate Limiting
```bash
# Check for rate limit errors in logs
sudo grep -i "rate limit" /opt/bitbucket-backup/logs/*.log

# Wait and retry (automatic backoff implemented)
# Or increase delays in configuration:
CLONE_TIMEOUT=3600
PUSH_TIMEOUT=7200
```

#### 2. Network Connectivity Problems
```bash
# Test basic connectivity
curl -v https://api.bitbucket.org/2.0/user

# Test with authentication
curl -u "email:api_token" https://api.bitbucket.org/2.0/user

# Check DNS resolution
nslookup bitbucket.org

# Test from script
python3 bitbucket-backup.py test
```

## 🔧 Troubleshooting Guide

### Authentication Issues

#### Problem: Invalid API Token
```
❌ SOURCE Authentication Failed:
   • Error: Invalid credentials or API token
```

**Diagnosis:**
```bash
# Test token manually
curl -u "your@email.com:your_token" https://api.bitbucket.org/2.0/user
```

**Solutions:**
1. **Create new token:** https://bitbucket.org/account/settings/app-passwords/
2. **Check permissions:** Ensure "Account: Read" and "Repositories: Read/Write"
3. **Verify email:** Must match Atlassian account email exactly

#### Problem: Insufficient Permissions
```
❌ DESTINATION Permission Denied:
   • Error: API token lacks required permissions
```

**Required Permissions:**
- ✅ **Account: Read** (Essential)
- ✅ **Repositories: Read** (Source account)
- ✅ **Repositories: Write** (Destination account)
- ✅ **Issues: Write** (For issue restoration)

### Workspace Access Issues

#### Problem: Workspace Not Found
```
❌ SOURCE Workspace Access Error:
   • Workspace: myworkspace
   • Error: Workspace not found or no access
```

**Diagnosis:**
```bash
# List accessible workspaces
curl -u "email:token" "https://api.bitbucket.org/2.0/workspaces" | jq '.values[].slug'
```

**Solutions:**
1. **Check spelling:** Workspace names are case-sensitive
2. **Verify access:** Ensure account is member of workspace
3. **Use UUID:** Try workspace UUID instead of name
4. **Check permissions:** Account may have limited access

### Repository Issues

#### Problem: Repository Clone Failures
```bash
# Check git configuration
git config --global user.name
git config --global user.email

# Test clone manually
git clone https://username:token@bitbucket.org/workspace/repo.git

# Check SSH keys (if using SSH)
ssh -T git@bitbucket.org
```

#### Problem: Large Repository Timeouts
```env
# Increase timeouts in .env
CLONE_TIMEOUT=3600    # 1 hour
PUSH_TIMEOUT=7200     # 2 hours
```

### Migration-Specific Issues

#### Problem: Destination Repository Creation Failed
```bash
# Check workspace permissions
curl -u "dest_email:dest_token" \
  "https://api.bitbucket.org/2.0/workspaces/dest_workspace/permissions"

# Manual repository creation test
curl -X POST -u "email:token" \
  "https://api.bitbucket.org/2.0/repositories/workspace/test-repo" \
  -H "Content-Type: application/json" \
  -d '{"scm": "git", "is_private": true}'
```

#### Problem: Collaboration Data Restoration Failed
```bash
# Check restoration settings
grep -E "RESTORE_|CREATE_" /opt/bitbucket-backup/config/.env

# Test with minimal restoration
RESTORE_ISSUES=false
RESTORE_WIKI=false
RESTORE_PRS=false
```

### Performance Issues

#### Problem: Slow Backup Performance
```bash
# Check system resources
htop
df -h
iostat 1

# Optimize settings
PARALLEL_JOBS=1      # Reduce concurrent jobs
MAX_BACKUPS=3        # Reduce backup retention
```

#### Problem: High Memory Usage
```bash
# Monitor memory during backup
sudo systemctl start bitbucket-backup.service &
watch -n 1 'ps aux | grep python3.*bitbucket'

# Reduce parallelism if needed
PARALLEL_JOBS=1
AUTO_DISCOVERY_MAX_REPOS=500
```

## 📊 Health Monitoring

### System Health Checks

#### Automated Health Check
```bash
sudo /opt/bitbucket-backup/scripts/health-check.sh
```

**Checks performed:**
- ✅ Service status and timer
- ✅ Configuration validity
- ✅ API connectivity
- ✅ Disk space availability
- ✅ Recent backup success
- ✅ Log file integrity

#### Manual Verification
```bash
# Check service status
systemctl is-active bitbucket-backup.timer

# Verify recent backups
find /opt/bitbucket-backup/backups/ -name "*.tar.gz" -mtime -7

# Check log for errors
sudo grep -i error /opt/bitbucket-backup/logs/*.log

# Test configuration
python3 bitbucket-backup.py test
```

### Monitoring Scripts

#### Daily Health Report
```bash
#!/bin/bash
# Add to cron: 0 8 * * * /path/to/daily-health.sh

echo "=== Bitbucket Backup System Health Report ===" > /tmp/health-report.txt
date >> /tmp/health-report.txt

# Service status
systemctl is-active bitbucket-backup.timer >> /tmp/health-report.txt

# Recent backups count
echo "Recent backups: $(find /opt/bitbucket-backup/backups/ -name "*.tar.gz" -mtime -1 | wc -l)" >> /tmp/health-report.txt

# Disk usage
echo "Disk usage:" >> /tmp/health-report.txt
df -h /opt/bitbucket-backup/ >> /tmp/health-report.txt

# Send report via email (if configured)
if [[ "$EMAIL_NOTIFICATIONS" == "true" ]]; then
    mail -s "Backup System Health Report" "$NOTIFICATION_EMAIL" < /tmp/health-report.txt
fi
```

## 🚀 Recovery Best Practices

### Preventive Measures

1. **Regular Testing**
   ```bash
   # Weekly configuration test
   python3 bitbucket-backup.py test
   
   # Monthly restore test
   sudo /opt/bitbucket-backup/scripts/verify-backups.sh
   ```

2. **Monitoring Setup**
   ```bash
   # Enable email notifications
   EMAIL_NOTIFICATIONS=true
   NOTIFICATION_EMAIL=admin@company.com
   
   # Monitor service logs
   sudo journalctl -u bitbucket-backup.service --since="24 hours ago"
   ```

3. **Backup Validation**
   ```bash
   # Verify backup integrity
   find /opt/bitbucket-backup/backups/ -name "*.tar.gz" -exec tar -tzf {} \; > /dev/null
   
   # Check backup sizes
   find /opt/bitbucket-backup/backups/ -name "*.tar.gz" -exec ls -lh {} \;
   ```

### Emergency Contacts

```bash
# System administrator commands
sudo systemctl stop bitbucket-backup.timer     # Stop scheduled backups
sudo systemctl disable bitbucket-backup.timer  # Disable permanently
sudo systemctl start bitbucket-backup.service  # Force immediate backup
```

### Documentation Update

Keep this emergency information updated:
- ✅ Current API tokens and expiration dates
- ✅ Workspace access permissions
- ✅ Emergency contact information
- ✅ Recovery procedures verification dates

---

🆘 **Emergency Contact:** Keep administrator contact information and API token recovery procedures readily available for critical failures.