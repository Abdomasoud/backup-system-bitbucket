# 🚀 Ubuntu 24 Deployment Guide - Bitbucket Backup System

## Quick Start (Root User Method)

This guide is specifically designed for **Ubuntu 24.04 LTS** which has externally-managed Python environments. The setup script handles all the virtual environment complexity automatically.

### 1. Prerequisites

- Ubuntu 24.04 LTS server (EC2 or any server)
- Root access (`sudo su` or direct root login)
- Internet connection for package installation

### 2. One-Command Deployment

```bash
# Become root user
sudo su

# Run the automated setup
bash setup.sh
```

That's it! The script will:

- ✅ Install all system dependencies (git, python3-venv, etc.)
- ✅ Create Python virtual environment automatically  
- ✅ Install Python packages (requests, python-dotenv)
- ✅ Set up directory structure in `/opt/bitbucket-backup`
- ✅ Copy all backup scripts
- ✅ Create cron job template

### 3. Configure Your Credentials

```bash
cd /opt/bitbucket-backup
cp config/.env.example config/.env
nano config/.env
```

Add your credentials:
```bash
ATLASSIAN_EMAIL="your-email@domain.com"
BITBUCKET_API_TOKEN="your-api-token-here"
BITBUCKET_WORKSPACE="your-workspace-name"
BACKUP_WORKSPACE="/opt/bitbucket-backup"
```

### 4. Test the Setup

```bash
# Test Python environment
source venv/bin/activate
python3 -c "import requests, dotenv; print('✅ Environment ready!')"
deactivate

# Run your first backup
./scripts/bitbucket-backup.sh --force
```

### 5. Enable Automatic Backups (Optional)

```bash
crontab -e
```

Add this line for backups every 3 days at 2 AM:
```bash
0 2 */3 * * /opt/bitbucket-backup/scripts/cron-wrapper.sh >> /opt/bitbucket-backup/logs/cron.log 2>&1
```

## 🔧 What This Setup Creates

```
/opt/bitbucket-backup/
├── venv/                        # Python virtual environment
├── scripts/
│   ├── bitbucket-backup.py      # Core backup engine
│   ├── bitbucket-backup.sh      # Main backup script
│   └── cron-wrapper.sh         # Cron helper
├── config/
│   ├── .env                     # Your credentials
│   └── .env.example            # Template
├── logs/                        # Backup logs
├── repositories/                # Individual repo backups
│   ├── repo1/
│   │   ├── repo1_20241215_140000.tar.gz
│   │   └── repo1_20241218_140000.tar.gz
│   └── repo2/
│       └── repo2_20241215_140000.tar.gz
└── metadata/                    # Repository metadata
```

## 🐛 Troubleshooting Ubuntu 24 Issues

### Problem: "externally-managed-environment" Error
**Solution**: The setup script creates a virtual environment automatically. This is already handled.

### Problem: Permission Denied
**Solution**: Run as root user (`sudo su` first). The script is designed for root execution.

### Problem: Virtual Environment Not Found
```bash
# Manual fix if needed
cd /opt/bitbucket-backup
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install requests python-dotenv
```

### Problem: Backup Script Fails
```bash
# Check logs
tail -f /opt/bitbucket-backup/logs/backup.log

# Test manually
cd /opt/bitbucket-backup
source venv/bin/activate
python3 scripts/bitbucket-backup.py
```

## 🔑 Getting Your Bitbucket API Token

1. Go to https://bitbucket.org/account/settings/app-passwords/
2. Click "Create app password"
3. Name: `backup-system`
4. Permissions needed:
   - **Repositories**: Read
   - **Account**: Read
5. Copy the generated token (you won't see it again!)
6. Use this token as `BITBUCKET_API_TOKEN` in your `.env` file

## 📊 Backup Features

- **Auto-Discovery**: Finds ALL repositories in your workspace
- **Mirror Creation**: Creates local git mirrors of each repo
- **Compression**: Creates .tar.gz archives for easy storage
- **Retention**: Keeps 5 backups per repository (15-day retention)
- **Organization**: Each repository gets its own folder
- **Metadata**: Saves repository information and backup history
- **Logging**: Comprehensive logs for troubleshooting

## ⏰ Backup Schedule

- **Frequency**: Every 3 days (configurable)
- **Time**: 2:00 AM (configurable)
- **Retention**: 5 backups per repo (15 days total)
- **Location**: `/opt/bitbucket-backup/repositories/`

## 🚀 Next Steps

After successful setup:

1. **Monitor First Few Backups**: Check logs to ensure everything works
2. **Adjust Retention**: Modify backup count in `bitbucket-backup.py` if needed
3. **Add Monitoring**: Set up alerts for backup failures
4. **Test Restores**: Periodically test that backups can be restored

## 📞 Support

If you encounter issues:

1. Check the logs: `tail -f /opt/bitbucket-backup/logs/backup.log`
2. Verify credentials: Test API token manually
3. Check Python environment: Ensure virtual environment works
4. Review cron logs: Check `/opt/bitbucket-backup/logs/cron.log`

The setup script is designed to handle Ubuntu 24's Python environment restrictions automatically. If you still have issues, the script provides detailed logging to help diagnose problems.