# Complete Auto-Discovery Migration System

## 🔍 **Overview**

The Bitbucket Migration System now includes **complete auto-discovery** capabilities that automatically detect ALL workspaces and repositories in your source account and intelligently migrate them to the destination account with full structure preservation.

## 🚀 **What Auto-Discovery Does**

### **Automatic Detection**
- **🏢 All Workspaces**: Discovers every workspace you have access to
- **📦 All Repositories**: Scans all repos in every discovered workspace
- **🔐 Permission-Aware**: Only processes workspaces/repos you can access
- **📊 Complete Cataloging**: Full inventory with metadata and statistics

### **Intelligent Migration**
- **🏗️ Workspace Creation**: Automatically creates destination workspaces
- **📂 Structure Preservation**: Maintains workspace organization
- **🎯 Smart Filtering**: Include/exclude patterns for selective migration
- **🛡️ Safety Limits**: Configurable limits to prevent runaway processes

### **Full Integration**
- **✅ Repository Migration**: Complete git history and metadata
- **🎫 Collaboration Data**: Issues, wikis, PRs (if enabled)
- **📋 Comprehensive Logging**: Detailed discovery and migration reports
- **📧 Email Notifications**: Complete migration summary with statistics

## ⚙️ **Configuration**

### **Enable Auto-Discovery**
```bash
# Enable complete auto-discovery mode
AUTO_DISCOVER_ALL=true

# Source and destination accounts
SOURCE_ATLASSIAN_EMAIL=source@company.com
SOURCE_BITBUCKET_API_TOKEN=source-api-token
DEST_ATLASSIAN_EMAIL=destination@newcompany.com  
DEST_BITBUCKET_API_TOKEN=destination-api-token
```

### **Filtering Options**
```bash
# Workspace filtering (include/exclude patterns)
WORKSPACE_INCLUDE_PATTERNS="company,prod"        # Only these patterns
WORKSPACE_EXCLUDE_PATTERNS="test,temp,archived"  # Skip these patterns

# Repository filtering  
REPO_INCLUDE_PATTERNS="api-,web-"               # Only repos matching patterns
REPO_EXCLUDE_PATTERNS="test-,demo-,temp"        # Skip repos matching patterns

# Safety limits
AUTO_DISCOVERY_MAX_REPOS=1000                   # Maximum repos to process
```

### **Workspace Management**
```bash
# Workspace creation and naming
CREATE_MISSING_WORKSPACES=true                  # Auto-create destination workspaces
WORKSPACE_NAME_PREFIX="migrated-"               # Optional prefix for dest workspaces
SKIP_EXISTING_WORKSPACES=false                  # Process existing workspaces
SKIP_EXISTING_REPOS=true                        # Skip repos that already exist
```

## 🎯 **Usage Scenarios**

### **Scenario 1: Complete Account Migration**
```bash
# Migrate EVERYTHING from one account to another
AUTO_DISCOVER_ALL=true
MIGRATION_MODE=true
CREATE_MISSING_WORKSPACES=true

# Result: Complete mirror of source account in destination
```

### **Scenario 2: Selective Company Migration**
```bash
# Only migrate company workspaces, skip personal/test ones
AUTO_DISCOVER_ALL=true
WORKSPACE_INCLUDE_PATTERNS="mycompany,prod"
WORKSPACE_EXCLUDE_PATTERNS="test,personal,temp"

# Result: Only business-related workspaces migrated
```

### **Scenario 3: Production Code Only**
```bash
# Only migrate production repositories
AUTO_DISCOVER_ALL=true
REPO_INCLUDE_PATTERNS="api-,web-,service-"
REPO_EXCLUDE_PATTERNS="test-,demo-,prototype-"

# Result: Only production-ready repositories migrated
```

### **Scenario 4: Large Organization with Limits**
```bash
# Large org with safety limits
AUTO_DISCOVER_ALL=true
AUTO_DISCOVERY_MAX_REPOS=500
WORKSPACE_EXCLUDE_PATTERNS="archived,legacy"

# Result: Controlled migration with safety limits
```

## 📊 **Discovery Process**

### **Phase 1: Workspace Discovery**
```
🔍 Auto-discovering all accessible workspaces...
   🏢 Found workspace: MyCompany (mycompany) - Permission: admin
   🏢 Found workspace: ProductTeam (product-team) - Permission: write  
   🏢 Found workspace: DevOps (devops-team) - Permission: admin
✅ Discovered 3 workspaces
```

### **Phase 2: Repository Scanning**
```
🔍 Auto-discovering repositories in 3 workspaces...
   📂 Scanning workspace: mycompany
      📦 Found 25 repositories in mycompany
         - web-frontend (JavaScript) - git
         - api-backend (Python) - git  
         - mobile-app (TypeScript) - git
         ... and 22 more repositories
   📂 Scanning workspace: product-team
      📦 Found 12 repositories in product-team
   📂 Scanning workspace: devops-team
      📦 Found 8 repositories in devops-team
✅ Total discovery complete: 45 repositories across 3 workspaces
```

### **Phase 3: Structure Analysis**
```
============================================================
📊 AUTO-DISCOVERY SUMMARY
============================================================
🏢 Total Workspaces: 3
📦 Total Repositories: 45

📂 mycompany (admin access)
   📦 Repositories: 25
   🔒 Private repos: 23/25
   🎫 With issues: 18/25
   📖 With wiki: 12/25
   💻 Languages: JavaScript: 10, Python: 8, TypeScript: 4

📂 product-team (write access)  
   📦 Repositories: 12
   🔒 Private repos: 12/12
   🎫 With issues: 8/12
   📖 With wiki: 5/12
   💻 Languages: Python: 6, JavaScript: 4, Go: 2

📂 devops-team (admin access)
   📦 Repositories: 8
   🔒 Private repos: 8/8
   🎫 With issues: 3/8
   📖 With wiki: 2/8
   💻 Languages: Shell: 4, Python: 2, YAML: 2
============================================================
🎯 Ready to migrate 45 repositories from 3 workspaces
============================================================
```

### **Phase 4: Destination Setup**
```
🏗️  Creating destination workspace structure...
   ✅ mycompany → mycompany
   ✅ product-team → product-team
   ✅ devops-team → devops-team
🏗️  Workspace creation complete: 3/3 successful
```

## 🎛️ **Advanced Features**

### **Smart Filtering**
- **Pattern Matching**: Include/exclude based on name patterns
- **Permission Awareness**: Only process accessible resources
- **Safety Limits**: Prevent processing too many repositories
- **Selective Processing**: Choose exactly what to migrate

### **Intelligent Workspace Management**
- **Auto-Creation**: Create missing workspaces in destination
- **Name Mapping**: Custom workspace name transformations
- **Conflict Resolution**: Handle existing workspaces gracefully
- **Permission Preservation**: Maintain access levels where possible

### **Repository Organization**
- **Structure Preservation**: Maintain workspace/repo relationships
- **Metadata Enhancement**: Add auto-discovery flags and information
- **Filtering Integration**: Apply repo-level filters per workspace
- **Batch Processing**: Efficient handling of large repository sets

## 📈 **Performance & Scalability**

### **Optimized Discovery**
- **Paginated API Calls**: Efficient handling of large datasets
- **Parallel Processing**: Multiple workspace scanning
- **Rate Limit Awareness**: Respectful API usage
- **Memory Efficient**: Streaming processing for large organizations

### **Configurable Limits**
```bash
AUTO_DISCOVERY_MAX_REPOS=1000      # Maximum repositories to process
PARALLEL_JOBS=3                    # Concurrent processing jobs
CLONE_TIMEOUT=1800                 # 30 minutes per repository
PUSH_TIMEOUT=3600                  # 60 minutes per push
```

## 🛡️ **Safety Features**

### **Built-in Protections**
- **Max Repository Limits**: Prevent runaway processing
- **Pattern Validation**: Validate include/exclude patterns
- **Permission Checking**: Verify access before processing
- **Dry-Run Mode**: Preview what would be discovered/migrated

### **Error Handling**
- **Graceful Failures**: Individual failures don't stop the process
- **Detailed Logging**: Complete audit trail of all operations
- **Recovery Options**: Resume failed migrations
- **Rollback Information**: Complete backup for recovery

## 📧 **Reporting & Notifications**

### **Discovery Report**
```
📧 Subject: Auto-Discovery Complete - 45 Repositories Found

🔍 DISCOVERY SUMMARY
• Workspaces Found: 3
• Repositories Discovered: 45
• Total Size: 2.3 GB
• Languages: JavaScript (20), Python (16), TypeScript (6), Others (3)

📂 WORKSPACE BREAKDOWN
• mycompany: 25 repos (1.2 GB)
• product-team: 12 repos (800 MB)  
• devops-team: 8 repos (300 MB)

🎯 READY FOR MIGRATION
All workspaces and repositories cataloged successfully.
Migration can proceed with full structure preservation.
```

### **Migration Report**
```
📧 Subject: Complete Migration Successful - 45 Repositories Migrated

✅ MIGRATION COMPLETE
• Repositories Migrated: 45/45 (100%)
• Workspaces Created: 3
• Issues Restored: 127
• Wiki Pages Restored: 89
• Total Processing Time: 2h 15m

🏆 PERFECT SUCCESS RATE
All repositories, collaboration data, and workspace structure
successfully migrated to destination account.
```

## 🚀 **Getting Started**

### **1. Basic Setup**
```bash
# Enable auto-discovery
export AUTO_DISCOVER_ALL=true
export MIGRATION_MODE=true

# Configure accounts
export SOURCE_ATLASSIAN_EMAIL=old@company.com
export SOURCE_BITBUCKET_API_TOKEN=old-token
export DEST_ATLASSIAN_EMAIL=new@company.com  
export DEST_BITBUCKET_API_TOKEN=new-token

# Run migration
python bitbucket-backup.py
```

### **2. With Filtering**
```bash
# Only migrate production workspaces
export WORKSPACE_INCLUDE_PATTERNS="prod,main,company"
export WORKSPACE_EXCLUDE_PATTERNS="test,temp,personal"

# Only migrate important repositories
export REPO_INCLUDE_PATTERNS="api-,web-,service-"
export REPO_EXCLUDE_PATTERNS="test-,demo-,prototype-"

# Run filtered migration
python bitbucket-backup.py
```

### **3. With Safety Limits**
```bash
# Large organization with limits
export AUTO_DISCOVERY_MAX_REPOS=100
export WORKSPACE_EXCLUDE_PATTERNS="archived,legacy,old"

# Run controlled migration
python bitbucket-backup.py
```

## ⚡ **Benefits**

1. **Complete Automation**: No manual workspace/repo configuration needed
2. **Perfect Structure Preservation**: Maintains exact organizational structure
3. **Intelligent Filtering**: Migrate only what you need
4. **Safety First**: Built-in limits and protections
5. **Full Visibility**: Complete discovery and migration reporting
6. **Scalable**: Handles small teams to large enterprise organizations
7. **Flexible**: Use with any combination of other features

The auto-discovery system makes migrating entire Bitbucket organizations as simple as setting a few environment variables and running the script. No more manual configuration files or missing repositories - just complete, intelligent migration with full control and visibility.