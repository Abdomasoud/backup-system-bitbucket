# 🔄 Bitbucket Account Migration Guide

## 📋 **Overview**

This system now supports **complete repository migration** from one Bitbucket account to another. Perfect for:

- Company account migrations
- Moving repositories to new organization
- Account consolidation
- Workspace transfers

---

## ⚙️ **Configuration for Migration**

### **Required Environment Variables**

```bash
# MIGRATION MODE
MIGRATION_MODE=true                     # Enable migration mode

# SOURCE ACCOUNT (Account to migrate FROM)
SOURCE_ATLASSIAN_EMAIL=source@company.com
SOURCE_BITBUCKET_API_TOKEN=source-api-token
SOURCE_BITBUCKET_USERNAME=source-username
SOURCE_BITBUCKET_WORKSPACE=source-workspace

# DESTINATION ACCOUNT (Account to migrate TO)
DEST_ATLASSIAN_EMAIL=destination@newcompany.com
DEST_BITBUCKET_API_TOKEN=destination-api-token
DEST_BITBUCKET_USERNAME=destination-username
DEST_BITBUCKET_WORKSPACE=destination-workspace

# MIGRATION SETTINGS
PRESERVE_REPO_NAMES=true               # Keep original names (true) or add prefix (false)
REPO_NAME_PREFIX=""                    # Optional prefix for migrated repos
SKIP_EXISTING_REPOS=true              # Skip repos that already exist in destination
MIGRATION_BATCH_SIZE=5                # Number of repos to process simultaneously

# PERFORMANCE SETTINGS (Optimized for Migration)
PARALLEL_JOBS=3                       # Concurrent operations
CLONE_TIMEOUT=1800                    # 30 minutes for large repos
PUSH_TIMEOUT=3600                     # 60 minutes for large pushes
```

---

## 🚀 **Migration Process**

### **Step 1: Preparation**

1. **Create API Tokens for Both Accounts**
   ```bash
   # For SOURCE account:
   # Go to https://bitbucket.org/account/settings/app-passwords/
   # Create token with: Repositories (Read, Write, Admin)
   
   # For DESTINATION account:  
   # Go to https://bitbucket.org/account/settings/app-passwords/
   # Create token with: Repositories (Read, Write, Admin)
   ```

2. **Verify Access**
   ```bash
   # Test SOURCE account access
   curl -u "source@company.com:source-token" \
     "https://api.bitbucket.org/2.0/repositories/source-workspace"
   
   # Test DESTINATION account access
   curl -u "destination@company.com:dest-token" \
     "https://api.bitbucket.org/2.0/repositories/destination-workspace"
   ```

### **Step 2: Configure Migration**

```bash
# Copy and configure
cd /opt/bitbucket-backup
cp config/.env.example config/.env
nano config/.env
```

**Example Configuration:**
```bash
# Migration Configuration
MIGRATION_MODE=true

# Source Account (OLD)
SOURCE_ATLASSIAN_EMAIL=old-admin@oldcompany.com
SOURCE_BITBUCKET_API_TOKEN=ATBBxxxxxxxxxxxxxxxx
SOURCE_BITBUCKET_USERNAME=oldcompany-admin
SOURCE_BITBUCKET_WORKSPACE=oldcompany-workspace

# Destination Account (NEW)
DEST_ATLASSIAN_EMAIL=new-admin@newcompany.com
DEST_BITBUCKET_API_TOKEN=ATBByyyyyyyyyyyyyyyy
DEST_BITBUCKET_USERNAME=newcompany-admin
DEST_BITBUCKET_WORKSPACE=newcompany-workspace

# Migration Settings
PRESERVE_REPO_NAMES=true              # Keep same repo names
SKIP_EXISTING_REPOS=true              # Don't overwrite existing repos
MIGRATION_BATCH_SIZE=3                # Process 3 repos at once

# Performance (Optimized for large repos)
CLONE_TIMEOUT=1800                    # 30 min timeout
PUSH_TIMEOUT=3600                     # 60 min timeout
```

### **Step 3: Run Migration**

```bash
# Dry run first (test configuration)
./scripts/bitbucket-backup.sh --test-config

# Start migration
./scripts/bitbucket-backup.sh --force

# Monitor progress
tail -f logs/backup_*.log
```

---

## 📊 **Migration Features**

### **✅ What Gets Migrated**

1. **Complete Git History**
   - All commits, branches, tags
   - Full repository structure
   - Git metadata and refs

2. **Repository Settings**
   - Description and visibility
   - Language detection
   - Fork policies
   - Issue/Wiki enabled status

3. **Local Backup Copy**
   - .tar.gz archives on server
   - Comprehensive metadata (PRs, issues, etc.)
   - 5-backup retention per repo

### **⚠️ Manual Recreation Needed**

Some items require manual recreation in destination:
- Pull Requests (exported in metadata.json)
- Issues and comments (exported in metadata.json)
- Repository permissions/access
- Webhooks and integrations
- Deploy keys

---

## 🔧 **Migration Modes**

### **Mode 1: Complete Account Migration**
```bash
MIGRATION_MODE=true
PRESERVE_REPO_NAMES=true
SKIP_EXISTING_REPOS=true
```
- Migrates ALL repositories
- Keeps original names
- Skips if already exists

### **Mode 2: Selective Migration with Prefix**
```bash
MIGRATION_MODE=true
PRESERVE_REPO_NAMES=false
REPO_NAME_PREFIX="migrated-"
```
- Adds prefix to all repo names
- Useful for gradual migration
- Avoids naming conflicts

### **Mode 3: Backup + Migration**
```bash
MIGRATION_MODE=true
PRESERVE_REPO_NAMES=true
MAX_BACKUPS=10
```
- Full migration to new account
- Enhanced local backup retention
- Complete disaster recovery setup

---

## 📈 **Progress Monitoring**

### **Real-time Monitoring**
```bash
# Monitor main process
tail -f /opt/bitbucket-backup/logs/backup_*.log

# Monitor specific operations
grep -i "migrat" /opt/bitbucket-backup/logs/backup_*.log
grep -i "success" /opt/bitbucket-backup/logs/backup_*.log
grep -i "error" /opt/bitbucket-backup/logs/backup_*.log
```

### **Migration Statistics**
```bash
# Check completed migrations
ls -la /opt/bitbucket-backup/repositories/

# Verify destination workspace
curl -u "dest-email:dest-token" \
  "https://api.bitbucket.org/2.0/repositories/destination-workspace" | \
  jq '.values[] | .name'
```

---

## 🚨 **Migration Checklist**

### **Before Migration**
- [ ] API tokens created for both accounts
- [ ] Both workspaces accessible
- [ ] Sufficient storage space available
- [ ] Team members notified
- [ ] Backup of current setup

### **During Migration**
- [ ] Monitor log files for errors
- [ ] Check destination workspace periodically
- [ ] Verify large repositories migrate completely
- [ ] Note any failed repositories for retry

### **After Migration**
- [ ] Verify all repositories migrated successfully
- [ ] Check repository settings in destination
- [ ] Update team access permissions
- [ ] Recreate webhooks and integrations
- [ ] Update CI/CD pipelines to new URLs
- [ ] Test critical workflows

---

## 🔄 **Advanced Migration Scenarios**

### **Large Repository Optimization**
```bash
# For repositories > 1GB
CLONE_TIMEOUT=7200                    # 2 hours
PUSH_TIMEOUT=10800                    # 3 hours
PARALLEL_JOBS=1                       # Sequential processing
```

### **Incremental Migration**
```bash
# Migrate in batches using workspace filtering
# First batch: critical repositories
# Second batch: development repositories  
# Third batch: archived repositories
```

### **Cross-Cloud Migration**
```bash
# Source: Bitbucket Cloud Account A
# Destination: Bitbucket Cloud Account B
# Backup: Local server for disaster recovery
```

---

## 🛠️ **Troubleshooting Migration**

### **Common Issues**

1. **Authentication Errors**
   ```bash
   # Verify API tokens
   curl -u "email:token" "https://api.bitbucket.org/2.0/user"
   ```

2. **Repository Already Exists**
   ```bash
   # Check SKIP_EXISTING_REPOS setting
   # Or manually rename conflicting repos
   ```

3. **Large Repository Timeouts**
   ```bash
   # Increase timeout values
   CLONE_TIMEOUT=7200
   PUSH_TIMEOUT=10800
   ```

4. **Permission Denied**
   ```bash
   # Verify API token permissions
   # Ensure workspace admin access
   ```

### **Recovery Commands**

```bash
# Retry failed migration for specific repo
./scripts/bitbucket-backup.sh --repo-name "failed-repo-name" --force

# Check migration status
grep -A 5 -B 5 "failed-repo-name" /opt/bitbucket-backup/logs/backup_*.log

# Manual repository push
cd /opt/bitbucket-backup/repositories/repo-name/latest-timestamp/repo.git
git remote add destination https://username:token@bitbucket.org/dest-workspace/repo-name.git
git push --mirror destination
```

---

This migration system provides a **complete, automated solution** for moving ALL your repositories from one Bitbucket account to another, while maintaining local backups for disaster recovery! 🚀