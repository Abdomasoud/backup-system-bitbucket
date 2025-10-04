# Collaboration Data Restoration Guide

## 🎯 Overview

The Bitbucket Migration System now includes **comprehensive collaboration data restoration** capabilities. This means when you migrate repositories to a destination account, you don't just get the git repository - you also get **issues, wikis, pull request documentation, and more** recreated in the destination account.

## ✅ What Gets Restored

### 📝 **Issues & Comments**
- **Issues**: Recreated with original titles, descriptions, and metadata
- **Comments**: All issue comments preserved with author attribution
- **Status**: Issue states (open/resolved) maintained where possible
- **Migration Info**: Clear attribution showing original author and migration date

### 📖 **Wiki Pages** 
- **Content**: All wiki pages recreated with original content
- **Structure**: Page hierarchy and navigation maintained
- **Attribution**: Original author and update timestamps preserved
- **Auto-Enable**: Wiki feature automatically enabled in destination repo

### 🔀 **Pull Requests (Documentation)**
- **Complete History**: All PRs documented with full details
- **Comments**: PR discussions and code review comments preserved
- **Metadata**: Branch info, merge status, approval history
- **Format**: Created as wiki pages or documentation issues

### 🔐 **Repository Settings** *(Optional)*
- **Permissions**: User and team access levels (requires user mapping)
- **Branch Restrictions**: Protection rules and merge requirements
- **Webhooks**: Endpoint URLs and event triggers
- **Deploy Keys**: Documentation (keys must be manually added for security)

## ⚙️ Configuration

### Environment Variables

```bash
# ========== COLLABORATION DATA RESTORATION ==========

# Issues & Comments
RESTORE_ISSUES=true                    # Recreate issues with comments
RESTORE_PRS=false                      # Create PR documentation  
RESTORE_WIKI=true                      # Recreate wiki pages

# Repository Settings (requires admin permissions)
RESTORE_PERMISSIONS=false              # Restore user permissions
RESTORE_BRANCH_RESTRICTIONS=false     # Restore branch protection
RESTORE_WEBHOOKS=false                 # Recreate webhooks
RESTORE_DEPLOY_KEYS=false             # Create deploy key documentation

# User Account Mapping
USER_MAPPING={"old_user": "new_user", "john.doe": "j.doe"}
```

### Default Settings Explained

- **Issues/Wiki**: `true` by default (safe and very useful)
- **PRs**: `false` by default (creates documentation, not actual PRs)
- **Settings**: `false` by default (requires admin permissions and careful setup)

## 🔄 How It Works

### 1. **Backup Phase** (Source Account)
```
Source Repo → API Calls → Complete Metadata JSON
├── Pull all issues + comments
├── Fetch all PR data + discussions  
├── Download wiki pages + content
├── Capture permissions & settings
└── Store as comprehensive JSON backup
```

### 2. **Migration Phase** (Git Repository)
```
Source Repo → Clone → Push → Destination Repo
```

### 3. **Restoration Phase** (Destination Account)
```
Metadata JSON → API Calls → Recreated Collaboration Data
├── Create issues with comments
├── Generate PR documentation
├── Restore wiki pages
├── Apply permissions (if configured)
└── Set up webhooks (if configured)
```

## 👥 User Account Mapping

### Cross-Account Migration Challenge
When migrating between different Bitbucket accounts, **users from the source account don't exist in the destination account**. The system handles this intelligently:

### Automatic Handling
- **Attribution Preserved**: Original authors shown in migration headers
- **Safe Defaults**: Unmatched users handled gracefully
- **Clear Documentation**: Migration info added to all restored content

### Manual Mapping (Optional)
```bash
USER_MAPPING={"source_username": "dest_username", "old_team_lead": "new_lead"}
```

### Example Migration Header
```markdown
---
🔄 MIGRATED CONTENT
- Original Author: John Doe (@john.doe)  
- Original Date: 2024-01-15 10:30:00
- Migration Date: 2024-10-04 14:25:30
- Type: Issue Comment
---
Original comment content here...
```

## 📊 Restoration Results

### Success Tracking
The system provides detailed feedback on restoration:

```
✅ Restored 47 collaboration items for web-frontend
   - Issues: 12
   - Wiki Pages: 8  
   - Pull Requests Documentation: 15
   - Permissions: 5
   - Branch Restrictions: 3
   - Webhooks: 2
   - Deploy Keys Documentation: 2
```

### Error Handling
- **Partial Success**: Individual failures don't stop the process
- **Detailed Logging**: Clear error messages for troubleshooting
- **Graceful Degradation**: System continues with available data

## 🚀 Migration Examples

### Example 1: Complete Issue Migration
**Source Repository:**
- 25 open issues
- 150 issue comments
- Multiple assignees and labels

**Destination Result:**
- ✅ 25 issues recreated with full content
- ✅ 150 comments preserved with original attribution
- ✅ Migration headers show original authors
- ✅ Issue states maintained (open/resolved)

### Example 2: Wiki Documentation
**Source Repository:**
- 15 wiki pages
- Complex page hierarchy
- Images and markdown formatting

**Destination Result:**  
- ✅ All 15 pages recreated
- ✅ Content formatting preserved
- ✅ Navigation structure maintained
- ✅ Original author attribution included

### Example 3: Pull Request Documentation
**Source Repository:**
- 45 merged PRs
- Extensive code review discussions
- Multiple approval workflows

**Destination Result:**
- ✅ Comprehensive PR documentation wiki
- ✅ All discussions and comments preserved
- ✅ Branch and merge information included
- ✅ Easy-to-navigate format for reference

## 🔧 Advanced Configuration

### Selective Restoration
Choose exactly what to restore:

```bash
# Conservative approach - only restore safe content
RESTORE_ISSUES=true
RESTORE_WIKI=true
RESTORE_PRS=false
RESTORE_PERMISSIONS=false

# Aggressive approach - restore everything  
RESTORE_ISSUES=true
RESTORE_WIKI=true
RESTORE_PRS=true
RESTORE_PERMISSIONS=true
RESTORE_BRANCH_RESTRICTIONS=true
RESTORE_WEBHOOKS=true
```

### Permission Requirements
- **Issues/Wiki**: Standard repository access
- **Permissions**: Admin access to destination repos
- **Webhooks**: Admin access + webhook management permissions
- **Branch Restrictions**: Admin access + branch management permissions

## ⚠️ Important Considerations

### 1. **Pull Requests Limitation**
- **Cannot recreate actual PRs** (branches may not exist)
- **Creates comprehensive documentation** instead
- **All PR data preserved** for reference and audit

### 2. **User Account Differences**
- **Source users may not exist** in destination account
- **Safe attribution system** preserves original author info
- **Manual user mapping** available for known transitions

### 3. **API Rate Limits**
- **Large repositories** may take time to restore
- **Built-in rate limiting** prevents API throttling
- **Batch processing** optimized for efficiency

### 4. **Security Considerations**
- **Deploy keys** documented but not transferred (security)
- **Webhook URLs** may need updating for new environment
- **Access tokens** and secrets not migrated (security)

## 🎯 Best Practices

### 1. **Start Conservative**
```bash
RESTORE_ISSUES=true
RESTORE_WIKI=true
RESTORE_PRS=false
```

### 2. **Test First**
- Run migration on a test repository
- Verify restoration results
- Adjust settings as needed

### 3. **Plan User Mapping**
- Identify key users to map
- Set up USER_MAPPING before migration
- Document unmapped users for manual assignment

### 4. **Monitor Progress**
- Watch restoration logs
- Verify critical issues/wikis restored
- Address any failures promptly

## 🚀 Complete Example

### Migration Command
```bash
# Set restoration preferences
export RESTORE_ISSUES=true
export RESTORE_WIKI=true  
export RESTORE_PRS=true
export USER_MAPPING='{"john.doe": "j.doe", "team.lead": "new.lead"}'

# Run migration with collaboration data restoration
python bitbucket-backup.py
```

### Expected Results
```
🚀 Starting Bitbucket MIGRATION process...
📤 SOURCE: old-company (old@company.com)  
📥 DESTINATION: new-company (new@company.com)

Processing repository: web-frontend
==========================================
📝 Backing up comprehensive metadata for web-frontend...
  - Fetched 25 issues
  - Fetched 45 pull requests  
  - Fetched 12 wiki pages
✅ Created mirror repository: web-frontend
🔄 Restoring collaboration data for web-frontend...
🎫 Restoring 25 issues to web-frontend...
   ✅ Created issue: Login form validation bug (ID: 1234)
   💬 Restored comment from John Doe
📖 Restoring 12 wiki pages to web-frontend...
   📄 Restored wiki page: API Documentation
🔀 Documenting 45 pull requests for web-frontend...  
   📝 Created pull requests documentation issue
✅ Restored 82 collaboration items for web-frontend
   - Issues: 25
   - Wiki Pages: 12
   - Pull Requests Documentation: 45
```

This comprehensive restoration ensures your migrated repositories aren't just empty shells - they're **complete, functional repositories** with all the collaborative history and documentation your team needs to continue working seamlessly.

## 🔮 Future Enhancements

- **Advanced user mapping** with automatic detection
- **Custom field migration** for enterprise Bitbucket instances  
- **Attachment and file restoration** for issues and wikis
- **Advanced PR reconstruction** with branch matching algorithms