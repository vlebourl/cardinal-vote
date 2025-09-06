# Branch Protection Rules for Generalized Platform Development

## Recommended GitHub Settings

### 1. Main Branch Protection (Already in place)

- ✅ Require pull request before merging
- ✅ Require approvals: 1
- ✅ Dismiss stale PR approvals when new commits are pushed
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Include administrators
- ❌ Allow force pushes: NEVER
- ❌ Allow deletions: NEVER

### 2. develop/generalized-platform Branch Protection (NEW)

**Navigate to**: Settings → Branches → Add rule

**Branch name pattern**: `develop/generalized-platform`

**Protect matching branches**:

- [x] Require pull request before merging
  - [x] Required approving reviews: 1
  - [x] Dismiss stale pull request approvals when new commits are pushed
  - [ ] Require review from CODEOWNERS
  - [x] Restrict who can dismiss pull request reviews
  - [ ] Allow specified actors to bypass required pull requests

- [x] Require status checks to pass before merging
  - [x] Require branches to be up to date before merging
  - **Required status checks**:
    - `Test Suite`
    - `Security Scan`
    - `Docker Build Test`
    - `Integration Tests`

- [x] Require conversation resolution before merging

- [x] Require signed commits (optional but recommended)

- [x] Require linear history (helps maintain clean history)

- [ ] Include administrators (uncheck to enforce even for admins)

- [x] Restrict who can push to matching branches
  - Add yourself and any trusted collaborators

- [ ] Allow force pushes
  - [ ] Everyone
  - [x] Specify who can force push: Only yourself for emergency fixes

- [ ] Allow deletions (NEVER enable this)

### 3. Feature Branch Pattern Protection (Optional)

**Branch name pattern**: `feature/gp-*`

**Light protection for feature branches**:

- [x] Require pull request before merging
  - [x] Required approving reviews: 1
- [x] Require status checks to pass
  - `Test Suite`
  - `Security Scan`
- [ ] Include administrators (allow admin override for quick fixes)

## Manual Configuration Steps

1. **Go to repository settings**:

   ```
   https://github.com/vlebourl/cardinal-vote/settings/branches
   ```

2. **Add branch protection for develop/generalized-platform**:
   - Click "Add rule"
   - Enter branch name pattern: `develop/generalized-platform`
   - Configure settings as listed above
   - Click "Create" or "Save changes"

3. **Verify protection is active**:
   - Try to push directly to `develop/generalized-platform` (should fail)
   - Create a test PR to confirm checks are required

## CI/CD Integration

The following GitHub Actions workflows will run on PRs to `develop/generalized-platform`:

```yaml
# .github/workflows/ci.yml already configured to run on:
on:
  pull_request:
    branches: [main, develop/generalized-platform]
  push:
    branches: [main, develop/generalized-platform]
```

## Bypass Procedures (Emergency Only)

If you need to bypass protection in an emergency:

1. **Temporary Admin Override**:
   - Uncheck "Include administrators" in branch protection
   - Make the emergency fix
   - Re-enable "Include administrators"
   - Document the bypass in the commit message

2. **Force Push (Last Resort)**:
   ```bash
   # Only if absolutely necessary and protection allows
   git push --force-with-lease origin develop/generalized-platform
   ```
   **WARNING**: This should never be needed if workflow is followed

## Monitoring & Compliance

**Weekly Review Checklist**:

- [ ] All PRs to develop/generalized-platform went through review
- [ ] No direct pushes to protected branches
- [ ] All required status checks passed before merge
- [ ] No force pushes were necessary
- [ ] Branch protection rules were not modified

**Monthly Audit**:

- Review GitHub Audit log for any protection rule changes
- Verify all team members understand the workflow
- Update protection rules if new requirements emerge

## Troubleshooting

**Issue**: Cannot push to develop/generalized-platform
**Solution**: Create a feature branch and PR

**Issue**: PR checks are failing
**Solution**: Fix issues locally, push to feature branch

**Issue**: Emergency fix needed
**Solution**: Follow emergency procedures, document thoroughly

**Issue**: Accidentally pushed to wrong branch
**Solution**: Revert commit via PR, do not force push

## Contact

For questions about branch protection or workflow:

1. Check this document first
2. Review WORKFLOW-GENERALIZED.md
3. Open a GitHub Discussion for team input

---

**Last Updated**: [Current Date]  
**Policy Owner**: Repository Administrator  
**Review Schedule**: Monthly during generalized platform development
