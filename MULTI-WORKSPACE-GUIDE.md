# 🏢 Multi-Workspace Bitbucket Migration Guide

## 📋 **Overview**

For clients with **multiple Bitbucket workspaces**, the system now supports comprehensive multi-workspace migration scenarios:

- **Scenario 1**: Migrate all workspaces with same names
- **Scenario 2**: Migrate with workspace name prefixes  
- **Scenario 3**: Custom workspace mapping
- **Scenario 4**: Consolidate multiple workspaces into one

---

## 🔧 **Multi-Workspace Configuration**

### **Scenario 1: Direct Workspace Migration**
*Migrate all workspaces keeping the same names*

```bash
# Multi-workspace mode
MULTI_WORKSPACE_MODE=true
MIGRATION_MODE=true

# Source Account (has multiple workspaces)
SOURCE_ATLASSIAN_EMAIL=admin@oldcompany.com
SOURCE_BITBUCKET_API_TOKEN=old-account-token
SOURCE_BITBUCKET_WORKSPACES=oldcompany-main,oldcompany-dev,oldcompany-staging

# Destination Account (will create matching workspaces)
DEST_ATLASSIAN_EMAIL=admin@newcompany.com
DEST_BITBUCKET_API_TOKEN=new-account-token
DEST_BITBUCKET_WORKSPACES=newcompany-main,newcompany-dev,newcompany-staging

# Settings
CREATE_MISSING_WORKSPACES=true
PRESERVE_REPO_NAMES=true
SKIP_EXISTING_REPOS=true
```

### **Scenario 2: Workspace with Prefixes**
*Add prefix to destination workspace names*

```bash
MULTI_WORKSPACE_MODE=true
MIGRATION_MODE=true

# Source workspaces
SOURCE_BITBUCKET_WORKSPACES=company-main,company-dev,company-test

# Auto-generate destination names with prefix
WORKSPACE_NAME_PREFIX=new-
# This creates: new-company-main, new-company-dev, new-company-test

# Destination account
DEST_ATLASSIAN_EMAIL=admin@newcompany.com
DEST_BITBUCKET_API_TOKEN=new-token
```

### **Scenario 3: Custom Workspace Mapping**
*Map specific source workspaces to specific destination workspaces*

```bash
MULTI_WORKSPACE_MODE=true
MIGRATION_MODE=true

# Custom mapping (source:destination pairs)
WORKSPACE_MAPPING=oldcompany-main:newcompany-production,oldcompany-dev:newcompany-development,oldcompany-staging:newcompany-testing

# Source and destination accounts
SOURCE_ATLASSIAN_EMAIL=old-admin@oldcompany.com
SOURCE_BITBUCKET_API_TOKEN=old-token

DEST_ATLASSIAN_EMAIL=new-admin@newcompany.com  
DEST_BITBUCKET_API_TOKEN=new-token
```

### **Scenario 4: Consolidation Migration**
*Migrate multiple source workspaces into one destination workspace*

```bash
MULTI_WORKSPACE_MODE=true
MIGRATION_MODE=true

# Multiple source workspaces
SOURCE_BITBUCKET_WORKSPACES=team-frontend,team-backend,team-mobile

# Single destination workspace (with repo prefixes to avoid conflicts)
WORKSPACE_MAPPING=team-frontend:consolidated-company,team-backend:consolidated-company,team-mobile:consolidated-company

# Add prefixes to distinguish repos from different teams
REPO_NAME_PREFIX="migrated-"
# This creates: migrated-frontend-repo, migrated-backend-api, etc.
```

---

## 🚀 **Migration Examples**

### **Example 1: Company Acquisition**
*OldCorp acquired by NewCorp - migrate all workspaces*

```bash
# Source: OldCorp (3 workspaces)
SOURCE_BITBUCKET_WORKSPACES=oldcorp-production,oldcorp-development,oldcorp-research

# Destination: NewCorp (matching structure)
DEST_BITBUCKET_WORKSPACES=newcorp-oldteam-prod,newcorp-oldteam-dev,newcorp-oldteam-research

# Or use mapping for clarity
WORKSPACE_MAPPING=oldcorp-production:newcorp-oldteam-prod,oldcorp-development:newcorp-oldteam-dev,oldcorp-research:newcorp-oldteam-research
```

### **Example 2: Department Restructure**
*Reorganize multiple department workspaces*

```bash
# Source: Separate department workspaces  
SOURCE_BITBUCKET_WORKSPACES=marketing-team,sales-team,support-team

# Destination: Consolidated under new structure
WORKSPACE_MAPPING=marketing-team:customer-success,sales-team:customer-success,support-team:customer-success

# Use repo prefixes to maintain identity
PRESERVE_REPO_NAMES=false
REPO_NAME_PREFIX="dept-"
```

### **Example 3: Multi-Client Agency**
*Migrate client workspaces to new agency account*

```bash
# Source: Multiple client workspaces
SOURCE_BITBUCKET_WORKSPACES=client-acme,client-globex,client-stark

# Destination: Agency account with client prefixes  
WORKSPACE_NAME_PREFIX=agency-
# Creates: agency-client-acme, agency-client-globex, agency-client-stark

PRESERVE_REPO_NAMES=true
CREATE_MISSING_WORKSPACES=true
```

---

## 📊 **Migration Process**

### **Step 1: Discovery Phase**
```bash
🔍 Scanning 3 workspace pairs for repositories...
📂 Scanning workspace: oldcompany-main
   Found 25 repositories in oldcompany-main
📂 Scanning workspace: oldcompany-dev  
   Found 18 repositories in oldcompany-dev
📂 Scanning workspace: oldcompany-staging
   Found 12 repositories in oldcompany-staging
📊 Total repositories found: 55 across 3 workspaces
```

### **Step 2: Workspace Creation**
```bash
🏗️  Checking if workspace 'newcompany-main' exists in destination...
🏗️  Creating workspace 'newcompany-main'...
✅ Successfully created workspace: newcompany-main

🏗️  Checking if workspace 'newcompany-dev' exists in destination...
✅ Workspace 'newcompany-dev' already exists
```

### **Step 3: Repository Migration**
```bash
📦 Processing workspace: oldcompany-main (25 repositories)
📦 Processing repository: payment-service
🔄 Migration target: payment-service
✅ Successfully migrated: payment-service

📦 Processing workspace: oldcompany-dev (18 repositories)  
📦 Processing repository: api-gateway
🔄 Migration target: api-gateway
✅ Successfully migrated: api-gateway
```

---

## ⚙️ **Advanced Configuration**

### **Performance Optimization for Multiple Workspaces**
```bash
# Increase parallel processing
PARALLEL_JOBS=5
MIGRATION_BATCH_SIZE=3

# Extended timeouts for large workspaces  
CLONE_TIMEOUT=2700    # 45 minutes
PUSH_TIMEOUT=5400     # 90 minutes

# Workspace creation settings
CREATE_MISSING_WORKSPACES=true
SKIP_EXISTING_WORKSPACES=true
SKIP_EXISTING_REPOS=true
```

### **Selective Workspace Migration**
```bash
# Only migrate specific workspaces
SOURCE_BITBUCKET_WORKSPACES=production,staging
WORKSPACE_MAPPING=production:new-prod,staging:new-staging

# Skip development workspaces for now
# Can run separate migration later for: development,testing,sandbox
```

### **Staging Migration Strategy**  
```bash
# Phase 1: Test with single workspace
MULTI_WORKSPACE_MODE=false
SOURCE_BITBUCKET_WORKSPACE=test-workspace
DEST_BITBUCKET_WORKSPACE=new-test-workspace

# Phase 2: Production workspaces
MULTI_WORKSPACE_MODE=true
SOURCE_BITBUCKET_WORKSPACES=production,staging
DEST_BITBUCKET_WORKSPACES=new-production,new-staging

# Phase 3: All remaining workspaces
SOURCE_BITBUCKET_WORKSPACES=development,testing,sandbox
```

---

## 📈 **Monitoring Multi-Workspace Migration**

### **Progress Tracking**
```bash
# Monitor overall progress
tail -f logs/backup_*.log | grep -E "(Processing workspace|Successfully migrated|❌)"

# Track workspace completion
grep "📊 Total repositories found" logs/backup_*.log
grep "🎉 Workspace migration completed" logs/backup_*.log

# Check for errors
grep -i error logs/backup_*.log | grep -v "No repositories"
```

### **Validation Commands**
```bash
# Verify all destination workspaces created
curl -u "dest-email:dest-token" "https://api.bitbucket.org/2.0/workspaces" | jq '.values[].slug'

# Count repositories in each destination workspace  
for ws in newcompany-main newcompany-dev newcompany-staging; do
  echo "=== $ws ==="
  curl -u "dest-email:dest-token" "https://api.bitbucket.org/2.0/repositories/$ws" | jq '.values | length'
done
```

---

## 📋 **Multi-Workspace Migration Checklist**

### **Pre-Migration**
- [ ] Document all source workspaces and repository counts
- [ ] Plan destination workspace structure  
- [ ] Decide on naming conventions (prefixes, mapping)
- [ ] Test with single workspace first
- [ ] Ensure destination account has sufficient permissions
- [ ] Notify all teams about workspace changes

### **During Migration**
- [ ] Monitor each workspace migration completion
- [ ] Track any failed repositories per workspace
- [ ] Verify workspace creation in destination
- [ ] Check repository counts match between source and destination
- [ ] Monitor server storage space for local backups

### **Post-Migration**
- [ ] Verify all workspaces migrated successfully
- [ ] Update team access permissions for new workspaces
- [ ] Migrate webhook configurations
- [ ] Update CI/CD pipelines with new workspace URLs
- [ ] Test critical workflows in each workspace
- [ ] Update documentation with new workspace structure

---

This multi-workspace system handles **complex enterprise scenarios** where clients have multiple Bitbucket workspaces that need organized migration to new accounts! 🏢✨