# 🚀 Bitbucket Backup System - Ultra Simple & Reliable

**No virtual environments. No complex setup. Just works.**

A bulletproof Bitbucket backup solution that automatically discovers ALL your repositories, creates mirrors, and generates organized compressed backups with retention management.

## ✨ What It Does

- 🔍 **Auto-discovers ALL repositories** in your Bitbucket workspace
- 🪞 **Creates mirror repositories** in your backup workspace
- 📦 **Generates .tar.gz backups** every 3 days (configurable)
- 🗂️ **Organizes each repo in its own folder**
- 🔄 **Maintains 5 backups per repo** (15-day retention)
- 📊 **Saves metadata** (issues, PRs, repository info)
- 🤖 **Fully automated** with cron integration

## 🎯 Super Simple Setup

### 1. **Clone & Run Setup**
```bash
# On Ubuntu 22+ server (as root)
sudo -i
git clone https://github.com/Abdomasoud/backup-system-bitbucket.git
cd backup-system-bitbucket
bash setup.sh
```

### 2. **Configure Credentials**
```bash
nano /opt/bitbucket-backup/config/.env
```
Set your Bitbucket API token and workspace info.

### 3. **Test & Run**
```bash
cd /opt/bitbucket-backup
./scripts/bitbucket-backup.sh --test-only  # Test connection
./scripts/bitbucket-backup.sh --force      # First backup
```

## 📁 Perfect Organization

Creates this structure automatically:
```
/opt/bitbucket-backup/repositories/
├── project-alpha/
│   ├── project-alpha_20251002_140000.tar.gz
│   └── project-alpha_20251005_140000.tar.gz
├── project-beta/
│   └── project-beta_20251002_140000.tar.gz
└── website/
    └── website_20251002_140000.tar.gz
```

## 🔧 Requirements

- Ubuntu 22+ (or similar)
- Root access
- Bitbucket API token ([Get one here](https://bitbucket.org/account/settings/app-passwords/))

**That's it!** No Python virtual environments, no complex dependencies.

## 📋 Configuration

Edit `/opt/bitbucket-backup/config/.env`:
```bash
ATLASSIAN_EMAIL=your-email@domain.com
BITBUCKET_API_TOKEN=your-api-token
BITBUCKET_WORKSPACE=your-source-workspace  
BACKUP_WORKSPACE=your-backup-workspace
```

## 🧪 Commands

```bash
# Test connection
./scripts/bitbucket-backup.sh --test-only

# Force backup (ignore 3-day schedule)  
./scripts/bitbucket-backup.sh --force

# Normal scheduled run
./scripts/bitbucket-backup.sh

# Show help
./scripts/bitbucket-backup.sh --help
```

## ⏰ Automation

Add to cron for automatic backups every 3 days:
```bash
crontab -e
# Add: 0 2 */3 * * /opt/bitbucket-backup/scripts/cron-wrapper.sh >> /opt/bitbucket-backup/logs/cron.log 2>&1
```

## 📖 Full Documentation

- **[SIMPLE-DEPLOYMENT.md](SIMPLE-DEPLOYMENT.md)** - Complete step-by-step guide
- **[COMPLETION-SUMMARY.md](COMPLETION-SUMMARY.md)** - Technical overview

---

## 🎉 Ready to Deploy!

Your backup system will:
1. **Find all repositories** in your workspace automatically
2. **Create organized backups** in separate folders per repository  
3. **Maintain retention** (5 backups per repo, 15-day history)
4. **Run automatically** every 3 days via cron
5. **Create mirror repos** in your backup workspace for disaster recovery

**No more manual repository lists. No more complex setup. Just reliable, automated backups.** 🚀