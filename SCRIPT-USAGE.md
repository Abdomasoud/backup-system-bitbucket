# 📜 Script Usage & Commands Guide

Complete reference for using the Bitbucket Migration & Backup System scripts and commands.

## 🐍 Python Script (Recommended)

The Python script provides full feature support and enhanced error reporting.

### Basic Commands

```bash
# Test configuration (recommended first step)
python3 bitbucket-backup.py test

# Run full backup/migration
python3 bitbucket-backup.py

# Run with specific log level
LOG_LEVEL=DEBUG python3 bitbucket-backup.py
```

### Configuration Modes

#### Auto-Discovery Mode (Default)
Automatically discovers ALL accessible workspaces and repositories:

```env
AUTO_DISCOVER_ALL=true
SOURCE_ATLASSIAN_EMAIL=your@email.com
SOURCE_BITBUCKET_API_TOKEN=your_token
```

**Features:**
- ✅ Finds all workspaces you have access to
- ✅ Discovers all repositories in each workspace
- ✅ Intelligent filtering based on exclude patterns
- ✅ No manual workspace/repository configuration needed

#### Manual Workspace Mode
Specify exact workspaces to process:

```env
AUTO_DISCOVER_ALL=false
SOURCE_BITBUCKET_WORKSPACES=workspace1,workspace2,workspace3
DEST_BITBUCKET_WORKSPACES=new-ws1,new-ws2,new-ws3
```

#### Single Repository Mode
Target specific repositories:

```env
AUTO_DISCOVER_ALL=false
SOURCE_BITBUCKET_WORKSPACE=myworkspace
TARGET_REPOSITORIES=repo1,repo2,repo3
```

### Migration vs Backup Modes

#### Backup Mode (Single Account)
```env
# Only source credentials needed
SOURCE_ATLASSIAN_EMAIL=your@email.com
SOURCE_BITBUCKET_API_TOKEN=your_token
MIGRATION_MODE=false
```

**Output:** Local backups with metadata preservation

#### Migration Mode (Dual Account)
```env
# Both source and destination credentials
SOURCE_ATLASSIAN_EMAIL=source@email.com
SOURCE_BITBUCKET_API_TOKEN=source_token
DEST_ATLASSIAN_EMAIL=dest@email.com
DEST_BITBUCKET_API_TOKEN=dest_token
MIGRATION_MODE=true
```

**Output:** Cross-account migration with collaboration data

### Command Examples

#### Quick Configuration Test
```bash
cd /opt/bitbucket-backup
python3 bitbucket-backup.py test
```

#### Backup All Accessible Repositories
```bash
# Auto-discover and backup everything
AUTO_DISCOVER_ALL=true python3 bitbucket-backup.py
```

#### Migrate Specific Workspaces
```bash
# Set in .env file:
# SOURCE_BITBUCKET_WORKSPACES=old-workspace1,old-workspace2
# DEST_BITBUCKET_WORKSPACES=new-workspace1,new-workspace2
python3 bitbucket-backup.py
```

#### Debug Mode with Verbose Logging
```bash
LOG_LEVEL=DEBUG python3 bitbucket-backup.py
```

## 🐚 Shell Script (Basic Features)

The shell script provides simple backup functionality for basic use cases.

### Basic Commands

```bash
# Run backup with current configuration
./bitbucket-backup.sh

# Force backup (ignore schedule)
./bitbucket-backup.sh --force

# Test connection only
./bitbucket-backup.sh --test

# Show help
./bitbucket-backup.sh --help
```

### Shell Script Limitations

**⚠️ Limited Support:**
- ❌ Only processes **first workspace** from multi-workspace lists
- ❌ No auto-discovery of ALL workspaces
- ❌ No collaboration data restoration
- ❌ No cross-account migration features
- ❌ Basic error reporting only

**✅ Good For:**
- Simple single-workspace backups
- Legacy system compatibility
- Minimal dependency environments

### Shell Script Configuration

The shell script automatically detects your configuration format:

#### New Format Support (Limited)
```env
# Uses first workspace only
SOURCE_BITBUCKET_WORKSPACES=workspace1,workspace2  # Uses: workspace1
DEST_BITBUCKET_WORKSPACES=new-ws1,new-ws2         # Uses: new-ws1
```

#### Legacy Format Support (Full)
```env
ATLASSIAN_EMAIL=your@email.com
BITBUCKET_API_TOKEN=your_token
BITBUCKET_WORKSPACE=source_workspace
BACKUP_WORKSPACE=backup_workspace
```

## 🔧 Management Commands

### System Management Scripts

Located in `/opt/bitbucket-backup/scripts/`:

#### Status and Health Checks
```bash
# Overall system status
sudo /opt/bitbucket-backup/scripts/status.sh

# Comprehensive health check
sudo /opt/bitbucket-backup/scripts/health-check.sh

# Test API connectivity
sudo /opt/bitbucket-backup/scripts/test-connection.sh
```

#### Manual Operations
```bash
# Force immediate backup (ignores schedule)
sudo /opt/bitbucket-backup/scripts/manual-backup.sh

# Verify backup integrity
sudo /opt/bitbucket-backup/scripts/verify-backups.sh

# Quick restore test
sudo /opt/bitbucket-backup/scripts/quick-restore.sh
```

### Service Management

#### Systemd Service Commands
```bash
# Check service status
sudo systemctl status bitbucket-backup.service

# Start backup immediately
sudo systemctl start bitbucket-backup.service

# Check timer status (scheduled backups)
sudo systemctl status bitbucket-backup.timer

# Enable/disable automatic scheduling
sudo systemctl enable bitbucket-backup.timer
sudo systemctl disable bitbucket-backup.timer
```

#### Log Monitoring
```bash
# Live log monitoring
sudo journalctl -u bitbucket-backup.service -f

# Recent logs only
sudo journalctl -u bitbucket-backup.service --since="1 hour ago"

# All logs for today
sudo journalctl -u bitbucket-backup.service --since=today
```

## 📊 Output and Results

### Backup Structure
```
/opt/bitbucket-backup/
├── backups/
│   ├── workspace1/
│   │   ├── repo1/
│   │   │   ├── 20241004_120000.tar.gz
│   │   │   ├── 20241001_120000.tar.gz
│   │   │   └── metadata/
│   │   └── repo2/
│   └── workspace2/
├── logs/
│   ├── backup_20241004_120000.log
│   └── migration_20241004_120000.log
└── config/
    └── .env
```

### Migration Output
```
📤 SOURCE: old-workspace (source@email.com)
📥 DESTINATION: new-workspace (dest@email.com)

✅ Repository Migration: old-repo → new-repo
✅ Issues Restoration: 45 issues migrated
✅ Wiki Restoration: 12 pages migrated
✅ Backup Created: /backups/new-workspace/new-repo/20241004_120000.tar.gz
```

### Test Command Output
```bash
$ python3 bitbucket-backup.py test

🧪 BITBUCKET CONFIGURATION TEST
==================================================
📋 Configuration loaded:
   • Migration Mode: Yes
   • Auto-Discovery: Yes
   • Source Email: source@email.com
   • Dest Email: dest@email.com

🔍 Testing API connections...
   Testing SOURCE account connection...
   ✅ SOURCE account connection successful
   Testing DESTINATION account connection...
   ✅ DESTINATION account connection successful

==================================================
✅ CONFIGURATION TEST PASSED
```

## 🎯 Use Case Examples

### Scenario 1: Complete Organization Migration
```bash
# .env configuration
MIGRATION_MODE=true
AUTO_DISCOVER_ALL=true
SOURCE_ATLASSIAN_EMAIL=old-org@company.com
DEST_ATLASSIAN_EMAIL=new-org@company.com
CREATE_MISSING_WORKSPACES=true
RESTORE_ISSUES=true
RESTORE_WIKI=true

# Execute migration
python3 bitbucket-backup.py
```

### Scenario 2: Selective Workspace Backup
```bash
# .env configuration
AUTO_DISCOVER_ALL=false
SOURCE_BITBUCKET_WORKSPACES=production,staging
WORKSPACE_EXCLUDE_PATTERNS=test,demo
MIGRATION_MODE=false

# Execute backup
python3 bitbucket-backup.py
```

### Scenario 3: Emergency Backup
```bash
# Quick backup of specific workspace
SOURCE_BITBUCKET_WORKSPACE=critical-workspace python3 bitbucket-backup.py

# Or using shell script for simple backup
BITBUCKET_WORKSPACE=critical-workspace ./bitbucket-backup.sh --force
```

## 🚨 Error Handling

### Common Error Messages

#### Authentication Errors
```
❌ SOURCE Authentication Failed:
   • Email: source@email.com
   • Error: Invalid credentials or API token
   • Fix: Check your Atlassian email and API token
```

**Solution:** Verify API token and permissions at bitbucket.org/account/settings/app-passwords/

#### Workspace Access Errors
```
❌ DESTINATION Workspace Access Error:
   • Workspace: new-workspace
   • Error: Workspace not found or no access
   • Fix: Check workspace name and verify account has access
```

**Solution:** Verify workspace name and account permissions

#### Network Errors
```
❌ SOURCE Connection Timeout:
   • Error: Request timed out after 30 seconds
   • Fix: Check internet connection and try again
```

**Solution:** Check network connectivity and firewall settings

### Debug Mode
```bash
# Enable verbose logging for troubleshooting
LOG_LEVEL=DEBUG python3 bitbucket-backup.py test
```

---

📚 **More Help:** See [SETUP.md](SETUP-NEW.md) for installation and [DISASTER-RECOVERY.md](DISASTER-RECOVERY-NEW.md) for troubleshooting.