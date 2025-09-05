# Branch Protection Rules Configuration

This document describes the required branch protection rules for this repository to enforce GitHub Flow best practices.

## Main Branch Protection

Configure the following settings for the `main` branch:

### General Settings
- ✅ **Restrict pushes that create files larger than 100MB**
- ✅ **Require a pull request before merging**
- ✅ **Require approvals**: 1 approval required
- ✅ **Dismiss stale PR approvals when new commits are pushed**
- ✅ **Require review from code owners** (if CODEOWNERS file exists)

### Status Checks
- ✅ **Require status checks to pass before merging**
- ✅ **Require branches to be up to date before merging**

**Required status checks:**
- `test (Test Suite)`
- `security (Security Scan)`  
- `docker-build (Docker Build Test)`
- `integration (Integration Tests)`
- `pr-quality-gate (PR Quality Gate)`

### Additional Restrictions
- ✅ **Restrict pushes to matching branches**
- ✅ **Allow force pushes**: ❌ Disabled
- ✅ **Allow deletions**: ❌ Disabled
- ✅ **Do not allow bypassing the above settings**

## GitHub CLI Commands

To configure these rules via GitHub CLI:

```bash
# Enable branch protection for main
gh api repos/$GITHUB_REPOSITORY/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test","security","docker-build","integration","pr-quality-gate"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null

# Require signed commits (optional but recommended)
gh api repos/$GITHUB_REPOSITORY/branches/main/protection/required_signatures \
  --method POST
```

## Repository Settings

Additional repository settings to configure:

### General
- ✅ **Default branch**: `main`
- ✅ **Allow merge commits**: ❌ Disabled  
- ✅ **Allow squash merging**: ✅ Enabled (default)
- ✅ **Allow rebase merging**: ✅ Enabled
- ✅ **Always suggest updating pull request branches**: ✅ Enabled
- ✅ **Allow auto-merge**: ✅ Enabled
- ✅ **Automatically delete head branches**: ✅ Enabled

### Pull Requests
- ✅ **Allow merge commits**: ❌ Disabled
- ✅ **Allow squash merging**: ✅ Enabled (default for PRs)
- ✅ **Allow rebase merging**: ✅ Enabled

### Security
- ✅ **Enable vulnerability alerts**: ✅ Enabled
- ✅ **Enable Dependabot security updates**: ✅ Enabled
- ✅ **Enable Dependabot version updates**: ✅ Enabled

## Enforcement Notes

1. **No direct pushes to main**: All changes must go through pull requests
2. **All CI checks must pass**: No merging with failed tests or security issues
3. **Require approval**: At least one team member must approve changes
4. **Keep branches up to date**: PRs must be rebased/merged with latest main
5. **Automatic cleanup**: Feature branches are automatically deleted after merge

These settings ensure:
- Code quality through automated testing
- Security through vulnerability scanning  
- Collaboration through required reviews
- Clean git history through squash merges
- Automated deployment through release workflows