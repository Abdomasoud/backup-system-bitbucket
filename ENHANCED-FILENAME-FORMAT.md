# Enhanced Tar.gz Filename Format

## 🎯 Overview

The Bitbucket Migration System now creates tar.gz backup files with a comprehensive and obvious naming format that provides instant visibility into backup contents, creation time, and metadata.

## 📁 New Filename Format

```
WORKSPACE_REPO-NAME_YYYY-MM-DD_HH-MM-SS_metaCOUNT_SIZE.tar.gz
```

### Format Components:
- **WORKSPACE**: Source Bitbucket workspace name
- **REPO-NAME**: Repository name 
- **YYYY-MM-DD**: Creation date (ISO format)
- **HH-MM-SS**: Creation time (24-hour format)
- **metaCOUNT**: Number of metadata items (PRs, issues, branches, tags, permissions, webhooks, deploy keys, restrictions)
- **SIZE**: Repository size in MB

## ✨ Example Filenames

```
my-company_web-frontend_2024-01-15_14-30-22_meta47_15.7MB.tar.gz
client-projects_mobile-app-backend_2024-01-15_14-31-08_meta123_89.4MB.tar.gz
opensource_python-utils_2024-01-15_14-32-45_meta28_2.1MB.tar.gz
data-science_ml-models_2024-01-15_14-33-12_meta95_256.8MB.tar.gz
```

## 📋 Archive Contents

Each tar.gz file contains:

1. **`repository-{repo_name}/`** - Complete repository clone with full git history
2. **`metadata-{repo_name}.json`** - Comprehensive metadata including:
   - Pull requests and issues
   - Branch and tag information  
   - User permissions and access
   - Webhooks and deploy keys
   - Branch restrictions and policies
3. **`backup-info.json`** - Backup creation metadata:
   - Creation timestamp (ISO format)
   - Repository and workspace details
   - Metadata item count
   - Repository size information
   - Backup system version
   - Migration mode flags

## 🎯 Benefits

### Instant Recognition
- **Workspace Identity**: Immediately see which workspace the backup belongs to
- **Repository Name**: Clear repository identification
- **Creation Time**: Precise timestamp for chronological organization
- **Metadata Count**: Quick assessment of backup complexity
- **Size Information**: Storage and transfer planning

### Improved Organization
- **Chronological Sorting**: Natural sort by date/time
- **Workspace Grouping**: Easy to organize by workspace
- **Size Planning**: Understand storage requirements at a glance
- **Metadata Assessment**: Know backup completeness before extraction

### Migration Ready
- **Source Identification**: Clear workspace and repo identification
- **Complete Metadata**: All necessary data for reconstruction
- **Version Tracking**: Timestamp-based version management
- **Storage Planning**: Size information for migration planning

## 🔧 Technical Implementation

### Enhanced Backup Creation
```python
def create_compressed_backup(self, repo_name, repo_path, metadata_path, repo=None):
    # Calculate metadata count from JSON
    # Determine repository size
    # Extract workspace information
    # Generate comprehensive filename
    # Create backup info metadata
```

### Improved Cleanup
- Sorts by file modification time (most robust)
- Provides detailed logging of cleanup operations
- Shows file sizes during removal
- Handles both old and new filename formats

### Smart Workspace Detection
1. Uses `source_workspace` if in migration mode
2. Falls back to `workspace` for regular backups  
3. Extracts from repository `full_name` if available
4. Uses "unknown" as safe fallback

## 📊 Migration Workflow Integration

The enhanced format integrates seamlessly with the existing migration system:

- **Multi-Workspace Mode**: Each workspace clearly identified in filename
- **Dual-Account Migration**: Source workspace always preserved
- **Enterprise Scenarios**: Comprehensive metadata for complex migrations
- **Batch Operations**: Easy identification and processing of backups

## 🚀 Usage Examples

### Single Repository Backup
```bash
my-company_web-app_2024-01-15_14-30-22_meta47_15.7MB.tar.gz
```

### Multi-Workspace Migration
```bash
source-ws_repo-a_2024-01-15_14-30-22_meta12_5.2MB.tar.gz
source-ws_repo-b_2024-01-15_14-31-15_meta8_2.1MB.tar.gz
dest-ws_repo-c_2024-01-15_14-32-08_meta24_12.8MB.tar.gz
```

### Enterprise Migration Batch
```bash
enterprise_main-app_2024-01-15_10-00-00_meta156_450.2MB.tar.gz
enterprise_api-service_2024-01-15_10-05-30_meta89_125.7MB.tar.gz
enterprise_frontend_2024-01-15_10-10-15_meta67_78.3MB.tar.gz
```

## 💡 Best Practices

1. **File Organization**: Group backups by workspace in separate directories
2. **Retention Management**: Use metadata count and size for cleanup decisions
3. **Migration Planning**: Sort by timestamp for chronological processing
4. **Storage Monitoring**: Track total size across all backups
5. **Metadata Validation**: Use metadata count to verify backup completeness

This enhanced naming format provides comprehensive, obvious, and immediately useful information about each backup, making the system more professional and easier to manage in enterprise environments.