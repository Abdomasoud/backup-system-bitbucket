# 🔧 Authentication Troubleshooting Guide

This guide helps you diagnose and fix authentication issues with your Bitbucket migration system.

## 🧪 Quick Configuration Test

Before running a full backup or migration, test your configuration:

```bash
python bitbucket-backup.py test
```

This will:
- ✅ Load your `.env` configuration
- ✅ Test API token authentication
- ✅ Verify workspace access permissions
- ✅ Check repository listing permissions
- ✅ Provide detailed error messages if anything fails

## 📋 Common Authentication Issues

### 1. Invalid API Token (401 Error)

**Symptoms:**
```
❌ SOURCE Authentication Failed:
   • Email: your@email.com
   • API Token: ********...xyz1
   • Error: Invalid credentials or API token
```

**Solutions:**
- Verify your Atlassian email is correct in `.env`
- Generate a new API token at: https://bitbucket.org/account/settings/app-passwords/
- Copy the token exactly (no extra spaces)

### 2. Insufficient Permissions (403 Error)

**Symptoms:**
```
❌ SOURCE Permission Denied:
   • Account: your@email.com
   • Error: API token lacks required permissions
   • Required permissions: Account: Read, Repositories: Read/Write
```

**Solutions:**
- Create new API token with required permissions:
  - ✅ **Account: Read** (Essential for authentication)
  - ✅ **Repositories: Read** (Required for source account)
  - ✅ **Repositories: Write** (Required for destination account)

### 3. Workspace Not Found (404 Error)

**Symptoms:**
```
❌ SOURCE Workspace Access Error:
   • Workspace: myworkspace
   • Error: Workspace not found or no access
```

**Solutions:**
- Check workspace name spelling in `.env`
- Verify you have access to the workspace
- Try the workspace UUID instead of the name

### 4. Repository Access Issues

**Symptoms:**
```
❌ SOURCE Repository Access Error:
   • Workspace: myworkspace
   • Error: No permission to list repositories
   • Fix: API token needs 'Repositories: Read' permission
```

**Solutions:**
- Update API token permissions
- Ensure you're a member of the workspace
- Check if repositories are private and you have access

## 🔑 Creating Proper API Tokens

### Step-by-Step Token Creation:

1. **Go to Bitbucket Settings:**
   - Visit: https://bitbucket.org/account/settings/app-passwords/

2. **Create New App Password:**
   - Click "Create app password"
   - Give it a descriptive name (e.g., "Migration Tool")

3. **Select Required Permissions:**
   ```
   ✅ Account: Read
   ✅ Repositories: Read    (for source account)
   ✅ Repositories: Write   (for destination account)
   ```

4. **Copy Token Safely:**
   - Copy the generated token immediately
   - Store it securely in your `.env` file
   - Token will only be shown once!

## 📊 Understanding Error Messages

The enhanced error reporting provides specific details:

### Source vs Destination Account Errors
- **SOURCE**: Issues with the account you're backing up FROM
- **DESTINATION**: Issues with the account you're migrating TO

### Error Categories:
- **Authentication Failed (401)**: Wrong email/token
- **Permission Denied (403)**: Token lacks required permissions
- **Workspace Access Error (404)**: Workspace doesn't exist or no access
- **Repository Access Error (403)**: Can't list/access repositories
- **Connection Timeout/Error**: Network issues

## 🛠️ Configuration Validation

### Required Variables for Backup Mode:
```env
SOURCE_ATLASSIAN_EMAIL=your@email.com
SOURCE_BITBUCKET_API_TOKEN=your_token_here
SOURCE_BITBUCKET_WORKSPACE=yourworkspace
```

### Required Variables for Migration Mode:
```env
# Source (FROM)
SOURCE_ATLASSIAN_EMAIL=source@email.com
SOURCE_BITBUCKET_API_TOKEN=source_token
SOURCE_BITBUCKET_WORKSPACE=sourceworkspace

# Destination (TO)
DEST_ATLASSIAN_EMAIL=dest@email.com
DEST_BITBUCKET_API_TOKEN=dest_token
DEST_BITBUCKET_WORKSPACE=destworkspace

# Enable migration
MIGRATION_MODE=true
```

## 🚀 Testing Workflow

1. **Create `.env` file** with your credentials
2. **Run configuration test**: `python bitbucket-backup.py test`
3. **Fix any reported issues**
4. **Re-run test until all checks pass**
5. **Proceed with actual backup/migration**

## 💡 Pro Tips

- **Test early and often**: Run the test command whenever you change configuration
- **Check permissions carefully**: Many issues stem from insufficient API token permissions
- **Use workspace UUIDs**: If workspace names cause issues, try UUIDs instead
- **Network issues**: If you get timeouts, check your internet connection and firewall
- **Multiple accounts**: Ensure both source and destination credentials are valid

## 🆘 Still Having Issues?

If you continue to experience problems after following this guide:

1. Run the configuration test for detailed error messages
2. Double-check all credentials in your `.env` file
3. Verify API token permissions at Bitbucket
4. Test with a simple workspace first
5. Check the console output for specific error details

The enhanced error reporting will guide you to the exact issue and provide specific fix instructions!