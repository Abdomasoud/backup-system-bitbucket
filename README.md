# Simple Bitbucket Backup System

A straightforward backup solution for ALL Bitbucket repositories.

## 📁 What's in the `final/` folder:

```
final/
├── setup.sh                    # Simple environment setup (no venv)
├── bitbucket-backup.sh         # Main backup script with scheduling
├── bitbucket-backup.py         # Full Python backup engine
└── .env.example               # Configuration template
```

## 🚀 Quick Setup

### 1. Upload to your Ubuntu EC2:
```bash
# From your local machine
scp -i "your-key.pem" -r final/ ubuntu@your-ec2-ip:/home/ubuntu/bitbucket-backup
```

### 2. Run setup on EC2:
```bash
ssh -i "your-key.pem" ubuntu@your-ec2-ip
cd bitbucket-backup
sudo ./setup.sh
```

### 3. Install Python dependencies manually:
```bash
pip3 install requests python-dotenv
```

### 4. Configure your credentials:
```bash
sudo nano /opt/bitbucket-backup/config/.env
```

Set these values:
- `ATLASSIAN_EMAIL=your-email@domain.com`
- `BITBUCKET_API_TOKEN=your-api-token`
- `BITBUCKET_WORKSPACE=source-workspace`
- `BACKUP_WORKSPACE=backup-workspace`

### 5. Test and run:
```bash
cd /opt/bitbucket-backup
source config/.env
./scripts/bitbucket-backup.sh --test-only
./scripts/bitbucket-backup.sh --force
```

### 6. Add to cron for automation:
```bash
crontab -e
# Add this line for backup every 3 days at 2 AM:
0 2 */3 * * /opt/bitbucket-backup/scripts/cron-wrapper.sh >> /opt/bitbucket-backup/logs/cron.log 2>&1
```

## ✅ What it does:

- **Discovers ALL repositories** automatically in your workspace
- **Creates mirror repositories** in backup workspace (repo-name-backup-mirror)
- **Generates .tar.gz files** every 3 days with perfect retention (5 backups per repo)
- **Organized folders** - each repository gets its own folder
- **Full metadata backup** - PRs, issues, branches, tags
- **Simple scheduling** with standard cron

## 📋 No complex features:

- ❌ No systemd services
- ❌ No virtual environments (you handle Python deps)
- ❌ No automatic user creation
- ❌ No firewall configuration
- ✅ Just pure backup automation

Perfect for when you want the full backup functionality without deployment complexity!