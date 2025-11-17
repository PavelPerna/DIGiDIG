# JIRA Integration Guide

## Overview

DIGiDIG project uses Atlassian JIRA for task management and issue tracking. This guide explains how JIRA integrates with the development workflow.

---

## JIRA Configuration

### JIRA Instance
- **URL:** https://pavelperna.atlassian.net
- **Project Key:** DIGIDIG

### Environment Variables

For automated JIRA operations, set these environment variables:

```bash
export JIRA_EMAIL="your@email.com"
export JIRA_API_TOKEN="your_api_token"
```

**Getting an API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name it (e.g., "DIGiDIG Development")
4. Copy the token and store it securely

---

## Automated JIRA Comments

### Using jira-comment.sh Script

The project includes a script to automatically post comments to JIRA issues:

```bash
# Post automatic comment to DIGIDIG-8
./scripts/jira-comment.sh DIGIDIG-8

# Post custom comment
./scripts/jira-comment.sh DIGIDIG-10 "Completed delegation documentation"
```

**Script Features:**
- Automatically includes branch name and commit hash
- Uses git metadata for context
- Posts formatted comments to JIRA issues

**Example Output:**
```
Automaticky koment: repo DIGiDIG, branch copilot/explore-delegation-concepts, commit a87be56
```

---

## JIRA Workflow

### Issue States
1. **To Do** - New issues waiting to be started
2. **In Progress** - Currently being worked on
3. **In Review** - Code review in progress
4. **Done** - Completed and verified

### Issue Types
- **Story** - New features or enhancements
- **Task** - Regular development tasks
- **Bug** - Issues and defects
- **Epic** - Large features spanning multiple stories

---

## GitHub Copilot & JIRA Integration

### Working with JIRA Issues

When GitHub Copilot works on JIRA issues:

1. **Issue Reference in Commits**
   ```bash
   git commit -m "Add delegation docs (DIGIDIG-10)"
   ```

2. **Branch Naming Convention**
   ```bash
   copilot/DIGIDIG-10-delegation-docs
   feature/DIGIDIG-15-new-api
   bugfix/DIGIDIG-20-auth-fix
   ```

3. **Automatic Documentation**
   - Copilot can read JIRA issue descriptions
   - Work is tracked via commit messages
   - Progress updates via scripts

### Delegation and JIRA

When asking about JIRA issue delegation:
- **JIRA Delegation** = Assigning issue to team member
- **Copilot Delegation** = Passing task to specialized AI agent

**See:** [DELEGATION-INDEX.md](DELEGATION-INDEX.md) for GitHub Copilot delegation details.

---

## Example JIRA Issues

### DIGIDIG-8
- **Type:** Task
- **Summary:** Authentication and logout improvements
- **Status:** Done
- **Documentation:** [DIGIDIG-8-SUMMARY.md](DIGIDIG-8-SUMMARY.md)

### DIGIDIG-10
- **Type:** Task
- **Summary:** Understanding delegation functionality
- **Status:** In Progress → Done
- **Documentation:** [DELEGATION-INDEX.md](DELEGATION-INDEX.md)

---

## Best Practices

### 1. Always Reference JIRA Issues
```bash
# Good commit messages
git commit -m "Fix authentication bug (DIGIDIG-15)"
git commit -m "Add API endpoint for users (DIGIDIG-20)"

# Poor commit messages
git commit -m "Fix bug"
git commit -m "Update code"
```

### 2. Update JIRA Status
- Move issues to "In Progress" when starting
- Comment with progress updates
- Move to "Done" when completed and verified

### 3. Link Related Issues
- Use JIRA's linking feature to connect related issues
- Reference blocking/blocked-by relationships
- Link to duplicate issues

### 4. Use JIRA for Communication
- Add comments for important decisions
- Tag team members with @mentions
- Attach relevant screenshots or logs

---

## Automation Scripts

### Post Comment on Commit
```bash
#!/bin/bash
# Post commit info to JIRA on successful push

git push && \
./scripts/jira-comment.sh DIGIDIG-10 "Pushed commit $(git rev-parse --short HEAD)"
```

### Daily Standup Report
```bash
# Get your recent JIRA activity
curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "https://pavelperna.atlassian.net/rest/api/3/search?jql=assignee=currentUser()+AND+updated>=startOfDay()"
```

---

## Troubleshooting

### "Authentication Failed"
- Check JIRA_EMAIL is correct
- Verify JIRA_API_TOKEN is valid
- Token might have expired - generate new one

### "Issue Not Found"
- Verify issue key is correct (e.g., DIGIDIG-10, not DIGIDIG10)
- Check you have permission to access the issue
- Issue might be in different project

### "Permission Denied"
- Contact JIRA administrator
- Verify your account has required permissions
- Check project access settings

---

## Related Documentation

- [TODO.md](TODO.md) - Project roadmap and tasks
- [DELEGATION-INDEX.md](DELEGATION-INDEX.md) - GitHub Copilot delegation
- [CI-CD.md](CI-CD.md) - Continuous integration setup

---

## Resources

- [JIRA REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [JIRA Best Practices](https://www.atlassian.com/software/jira/guides)
- [Creating API Tokens](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)

---

*Last Updated: 2025-11-10*
*Version: 1.0*
