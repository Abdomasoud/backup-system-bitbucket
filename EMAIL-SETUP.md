# Email Notification Setup Guide

This guide explains how to configure email notifications for the Bitbucket Backup System.

## Quick Setup

1. **Enable Email Notifications**
   ```bash
   EMAIL_NOTIFICATIONS=true
   ```

2. **Configure SMTP Settings**
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_USERNAME=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   NOTIFICATION_EMAIL=admin@your-domain.com
   ```

## Email Provider Configurations

### Gmail
```bash
EMAIL_NOTIFICATIONS=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
NOTIFICATION_EMAIL=recipient@domain.com
```

**Gmail Setup Steps:**
1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password: Google Account → Security → App passwords
3. Use the 16-character app password (not your regular password)

### Outlook/Hotmail
```bash
EMAIL_NOTIFICATIONS=true
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@outlook.com
EMAIL_PASSWORD=your-password
NOTIFICATION_EMAIL=recipient@domain.com
```

### Yahoo Mail
```bash
EMAIL_NOTIFICATIONS=true
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@yahoo.com
EMAIL_PASSWORD=your-app-password
NOTIFICATION_EMAIL=recipient@domain.com
```

### Custom SMTP Server
```bash
EMAIL_NOTIFICATIONS=true
SMTP_SERVER=mail.your-domain.com
SMTP_PORT=587
EMAIL_USERNAME=noreply@your-domain.com
EMAIL_PASSWORD=your-smtp-password
NOTIFICATION_EMAIL=admin@your-domain.com
EMAIL_FROM=backup-system@your-domain.com
```

## Email Report Features

The email notifications include:

### ✅ Success Reports
- **Summary Statistics**: Total repos, success rate, backup duration
- **Repository Details**: Status, size, and metadata count for each repo
- **Configuration Info**: Backup settings and retention policy
- **Log Attachment**: Complete backup log file attached

### ❌ Failure Reports
- **Error Summary**: List of all errors encountered
- **Failed Repositories**: Which repos failed and why
- **Partial Success**: Details of any repos that did succeed
- **Troubleshooting**: Log file attached for debugging

### 📊 Report Contents
- Backup timestamp and duration
- Success/failure status for each repository
- Backup file sizes
- Metadata statistics (PRs, issues, branches, etc.)
- Error details and troubleshooting information
- Configuration summary

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMAIL_NOTIFICATIONS` | No | `false` | Enable/disable email notifications |
| `SMTP_SERVER` | Yes* | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT` | Yes* | `587` | SMTP server port (usually 587 or 465) |
| `EMAIL_USERNAME` | Yes* | - | SMTP authentication username |
| `EMAIL_PASSWORD` | Yes* | - | SMTP authentication password |
| `NOTIFICATION_EMAIL` | Yes* | - | Email address to receive reports |
| `EMAIL_FROM` | No | Same as `EMAIL_USERNAME` | Sender email address |

*Required only if `EMAIL_NOTIFICATIONS=true`

## Testing Email Configuration

To test your email setup, you can run a quick test:

```bash
# Create a simple test script
cat > test-email.py << 'EOF'
#!/usr/bin/env python3
import os
import smtplib
from email.mime.text import MIMEText

# Load your .env file first
from dotenv import load_dotenv
load_dotenv()

smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
smtp_port = int(os.environ.get('SMTP_PORT', '587'))
email_username = os.environ.get('EMAIL_USERNAME', '')
email_password = os.environ.get('EMAIL_PASSWORD', '')
notification_email = os.environ.get('NOTIFICATION_EMAIL', '')
email_from = os.environ.get('EMAIL_FROM', email_username)

try:
    msg = MIMEText("This is a test email from Bitbucket Backup System")
    msg['Subject'] = "🧪 Test Email - Bitbucket Backup System"
    msg['From'] = email_from
    msg['To'] = notification_email

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(email_username, email_password)
    server.sendmail(email_from, notification_email, msg.as_string())
    server.quit()
    
    print("✅ Test email sent successfully!")
except Exception as e:
    print(f"❌ Email test failed: {e}")
EOF

python3 test-email.py
```

## Security Considerations

1. **Use App Passwords**: For Gmail, Yahoo, and other providers that support 2FA
2. **Secure Storage**: Store email credentials securely, never in version control
3. **Firewall Rules**: Ensure outbound SMTP ports (587/465) are open
4. **Log Sanitization**: Email logs may contain sensitive information

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify username and password/app password
   - Check if 2FA is required (Gmail, Yahoo)
   - Ensure "Less secure app access" is enabled (if applicable)

2. **Connection Timeout**
   - Check SMTP server and port settings
   - Verify firewall allows outbound SMTP traffic
   - Try different ports (587, 465, 25)

3. **SSL/TLS Errors**
   - Most providers require STARTTLS (port 587)
   - Some require SSL (port 465)

4. **Emails Not Received**
   - Check spam/junk folders
   - Verify recipient email address
   - Check email provider limits

### Testing Commands

```bash
# Test SMTP connectivity
telnet smtp.gmail.com 587

# Test with openssl
openssl s_client -connect smtp.gmail.com:587 -starttls smtp

# Check email logs
tail -f /opt/bitbucket-backup/logs/backup_*.log | grep -i email
```

## Example Configuration

Here's a complete working example:

```bash
# .env file
EMAIL_NOTIFICATIONS=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=backup@mycompany.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
NOTIFICATION_EMAIL=admin@mycompany.com
EMAIL_FROM=Bitbucket Backup System <backup@mycompany.com>
```

This will send professional HTML emails with complete backup reports and logs attached.