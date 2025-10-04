# 🛠️ Setup & Configuration Guide

Complete installation and configuration guide for the Bitbucket Migration & Backup System.

## 📦 Installation

### Ubuntu Production Deployment (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/Abdomasoud/backup-system-bitbucket.git
cd backup-system-bitbucket/final

# 2. Run automated deployment
sudo ./deploy-ubuntu.sh
```

**What the deployment script does:**
- ✅ Creates system directories `/opt/bitbucket-backup/`
- ✅ Installs Python dependencies (requests, python-dotenv)
- ✅ Sets up systemd service and timer for automation
- ✅ Creates management scripts in `/opt/bitbucket-backup/scripts/`
- ✅ Configures proper permissions and security

### Manual Installation

```bash
# Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip git curl jq

# Install Python packages
pip3 install requests python-dotenv

# Create directories
sudo mkdir -p /opt/bitbucket-backup/{config,scripts,logs,backups}

# Copy scripts
sudo cp bitbucket-backup.py /opt/bitbucket-backup/
sudo cp bitbucket-backup.sh /opt/bitbucket-backup/scripts/
```

## 🔐 API Token Configuration

### 1. Create Bitbucket API Tokens

**For each account (source and destination):**

1. Go to: `https://bitbucket.org/account/settings/app-passwords/`
2. Click "Create app password"
3. Set permissions:
   - ✅ **Account: Read** (essential)
   - ✅ **Repositories: Read** (source account)
   - ✅ **Repositories: Write** (destination account)
4. Copy the generated token immediately (shown only once)

### 2. Configure Environment Variables

Create or edit `/opt/bitbucket-backup/config/.env`:

```bash
sudo nano /opt/bitbucket-backup/config/.env
```

### Basic Backup Configuration

```env
# Single-account backup
SOURCE_ATLASSIAN_EMAIL=your@email.com
SOURCE_BITBUCKET_API_TOKEN=your_token_here
SOURCE_BITBUCKET_WORKSPACE=your_workspace
AUTO_DISCOVER_ALL=true
```

### Migration Configuration (Dual Account)

```env
# Source Account (migrate FROM)
SOURCE_ATLASSIAN_EMAIL=source@email.com
SOURCE_BITBUCKET_API_TOKEN=source_token_here
SOURCE_BITBUCKET_WORKSPACES=workspace1,workspace2

# Destination Account (migrate TO)
DEST_ATLASSIAN_EMAIL=dest@email.com
DEST_BITBUCKET_API_TOKEN=dest_token_here
DEST_BITBUCKET_WORKSPACES=new-workspace1,new-workspace2

# Enable migration features
MIGRATION_MODE=true
AUTO_DISCOVER_ALL=true
CREATE_MISSING_WORKSPACES=true

# Collaboration data restoration
RESTORE_ISSUES=true
RESTORE_WIKI=true
RESTORE_PRS=false
```

### Advanced Configuration Options

```env
# ========== PERFORMANCE ==========
MAX_BACKUPS=5                    # Backup retention count
PARALLEL_JOBS=3                  # Concurrent processing
CLONE_TIMEOUT=1800              # 30 minutes per repo
PUSH_TIMEOUT=3600               # 60 minutes per push

# ========== FILTERING ==========
WORKSPACE_EXCLUDE_PATTERNS=test,demo,temp
REPO_EXCLUDE_PATTERNS=old-,test-,demo-

# ========== WORKSPACE MAPPING ==========
# Format: source1:dest1,source2:dest2
WORKSPACE_MAPPING=old-workspace:new-workspace

# ========== EMAIL NOTIFICATIONS ==========
EMAIL_NOTIFICATIONS=true
NOTIFICATION_EMAIL=admin@company.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=notifications@company.com
EMAIL_PASSWORD=smtp_app_password

# ========== LOGGING ==========
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
MIGRATION_LOG_ENABLED=true
```

## 🧪 Testing Configuration

### Quick Test
```bash
cd /opt/bitbucket-backup
python3 bitbucket-backup.py test
```

**This validates:**
- ✅ API token authentication
- ✅ Workspace access permissions
- ✅ Repository listing permissions
- ✅ Network connectivity

### Expected Test Output
```
🧪 BITBUCKET CONFIGURATION TEST
==================================================
📋 Configuration loaded:
   • Migration Mode: Yes
   • Auto-Discovery: Yes
   • Source Email: source@email.com
   • Source Workspace: workspace1
   • Dest Email: dest@email.com
   • Dest Workspace: new-workspace1

🔍 Testing API connections...
   Testing SOURCE account connection...
   ✅ SOURCE account connection successful
   Testing DESTINATION account connection...
   ✅ DESTINATION account connection successful

==================================================
✅ CONFIGURATION TEST PASSED
🚀 Your configuration is ready for backup/migration!
```

## ⚙️ Service Configuration

### Enable Automated Backups

```bash
# Start and enable systemd timer
sudo systemctl start bitbucket-backup.timer
sudo systemctl enable bitbucket-backup.timer

# Check status
sudo systemctl status bitbucket-backup.timer
```

### Custom Schedule Configuration

Edit `/etc/systemd/system/bitbucket-backup.timer`:

```ini
[Unit]
Description=Bitbucket Backup Timer

[Timer]
OnCalendar=daily           # Run daily
Persistent=true
RandomizedDelaySec=3600    # Random 1-hour delay

[Install]
WantedBy=timers.target
```

Common schedules:
- `daily` - Every day at midnight
- `weekly` - Every Sunday at midnight  
- `*-*-* 02:00:00` - Every day at 2 AM
- `Mon,Wed,Fri 03:00` - Monday, Wednesday, Friday at 3 AM

## 🔧 Management Scripts

The system includes management scripts in `/opt/bitbucket-backup/scripts/`:

### Status and Monitoring
```bash
sudo /opt/bitbucket-backup/scripts/status.sh           # System status
sudo /opt/bitbucket-backup/scripts/health-check.sh     # Health check
```

### Manual Operations  
```bash
sudo /opt/bitbucket-backup/scripts/manual-backup.sh    # Force backup now
sudo /opt/bitbucket-backup/scripts/test-connection.sh  # Test API connection
```

### Service Management
```bash
sudo systemctl status bitbucket-backup.service         # Service status
sudo systemctl start bitbucket-backup.service          # Start backup now
sudo journalctl -u bitbucket-backup.service -f         # Live logs
```

## 🔒 Security Configuration

### File Permissions
```bash
# Secure configuration files
sudo chmod 600 /opt/bitbucket-backup/config/.env
sudo chown root:root /opt/bitbucket-backup/config/.env

# Secure backup directory
sudo chmod 750 /opt/bitbucket-backup/backups
sudo chown root:root /opt/bitbucket-backup/backups
```

### Environment Security
- ✅ Never commit `.env` files to version control
- ✅ Use dedicated API tokens with minimal permissions
- ✅ Rotate API tokens regularly
- ✅ Monitor access logs for unauthorized usage

## 📊 Verification

### Successful Setup Indicators

1. **Configuration Test Passes**
   ```bash
   python3 bitbucket-backup.py test
   # Should show: ✅ CONFIGURATION TEST PASSED
   ```

2. **Service is Active**
   ```bash
   sudo systemctl is-active bitbucket-backup.timer
   # Should show: active
   ```

3. **Manual Backup Works**
   ```bash
   sudo /opt/bitbucket-backup/scripts/manual-backup.sh
   # Should complete without errors
   ```

4. **Logs are Generated**
   ```bash
   ls -la /opt/bitbucket-backup/logs/
   # Should show recent log files
   ```

## 🐛 Troubleshooting

### Common Setup Issues

**Permission Denied Errors:**
```bash
sudo chown -R root:root /opt/bitbucket-backup/
sudo chmod +x /opt/bitbucket-backup/scripts/*.sh
```

**Python Dependencies Missing:**
```bash
sudo apt install -y python3-pip
pip3 install --upgrade requests python-dotenv
```

**Service Not Starting:**
```bash
sudo systemctl daemon-reload
sudo systemctl reset-failed bitbucket-backup.service
```

**API Token Issues:**
- Verify token permissions include "Account: Read" and "Repositories: Read/Write"
- Check token hasn't expired
- Ensure correct email address associated with token

---

✅ **Setup Complete!** Your Bitbucket backup system is ready for production use.