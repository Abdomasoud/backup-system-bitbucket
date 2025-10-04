# 🔄 Bitbucket Migration & Backup System

Complete automated solution for Bitbucket repository backup and cross-account migration with collaboration data restoration.

## ✨ Key Features

- 🔍 **Auto-Discovery**: Automatically finds ALL accessible workspaces and repositories
- 🔄 **Cross-Account Migration**: Migrate entire organizations between Bitbucket accounts
- 📊 **Collaboration Data**: Restore issues, pull requests, and wiki content
- 🏗️ **Multi-Workspace**: Process multiple workspaces with intelligent mapping
- 🛡️ **Production Ready**: Ubuntu deployment with systemd automation
- 📧 **Email Notifications**: SMTP alerts for backup completion and failures

## 🎯 Use Cases

### Repository Backup
- Complete backup of all repositories with metadata
- Automated scheduled backups with retention
- Compressed archives with timestamps

### Organization Migration  
- Move entire Bitbucket organizations between accounts
- Preserve collaboration data (issues, PRs, wikis)
- Automatic workspace creation and repository mapping

### Disaster Recovery
- Full restoration capabilities
- Metadata verification and validation
- Quick recovery procedures

## 🚀 Quick Start

### 1. Clone and Deploy
```bash
git clone https://github.com/Abdomasoud/backup-system-bitbucket.git
cd backup-system-bitbucket/final

# Ubuntu production deployment
sudo ./deploy-ubuntu.sh
```

### 2. Configure Credentials
```bash
sudo nano /opt/bitbucket-backup/config/.env
```

Set your Bitbucket API credentials:
```env
# Source Account (backup from)
SOURCE_ATLASSIAN_EMAIL=your@email.com
SOURCE_BITBUCKET_API_TOKEN=your_api_token

# Destination Account (migrate to) 
DEST_ATLASSIAN_EMAIL=dest@email.com
DEST_BITBUCKET_API_TOKEN=dest_api_token

# Features
AUTO_DISCOVER_ALL=true
MIGRATION_MODE=true
```

### 3. Test Configuration
```bash
cd /opt/bitbucket-backup
python3 bitbucket-backup.py test
```

### 4. Run Migration
```bash
python3 bitbucket-backup.py
```

## 📋 System Requirements

- **OS**: Ubuntu 18.04+ (recommended) or any Linux distribution
- **Python**: 3.6+ with requests, python-dotenv
- **Tools**: git, curl, jq
- **Access**: Root privileges for system installation
- **API**: Bitbucket API tokens with appropriate permissions

## 📖 Documentation

- **[SETUP.md](SETUP.md)** - Installation, configuration, and deployment
- **[SCRIPT-USAGE.md](SCRIPT-USAGE.md)** - Script usage, options, and examples  
- **[DISASTER-RECOVERY.md](DISASTER-RECOVERY.md)** - Backup restoration and troubleshooting

## 🔧 Support

**Configuration Issues:**
```bash
python3 bitbucket-backup.py test  # Enhanced error reporting
```

**System Status:**
```bash
sudo /opt/bitbucket-backup/scripts/status.sh
```

**Live Monitoring:**
```bash
sudo journalctl -u bitbucket-backup.service -f
```

## 🏆 Production Features

- ✅ Automated scheduling (systemd timers)
- ✅ Comprehensive logging and monitoring  
- ✅ Email notifications and alerts
- ✅ Backup retention and cleanup
- ✅ Enhanced error reporting and troubleshooting
- ✅ Security-focused configuration management

---

**Perfect for**: Enterprise Bitbucket migrations, automated backup systems, disaster recovery planning, and organization consolidation.