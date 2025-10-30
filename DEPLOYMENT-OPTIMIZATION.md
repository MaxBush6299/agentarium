# Deployment Optimization: Faster Container App Updates

## Problem
Previously, frontend code changes required manual Container App restart or took a long time to propagate. Every deployment would cache-hit and not force a new revision.

## Solution: Timestamp-Based Revision Forcing

Updated the GitHub Actions deployment workflow to add a unique timestamp environment variable on each deployment, forcing Azure Container Apps to create a new revision immediately.

### How It Works

1. **Timestamp Generation** - Each deployment generates a Unix timestamp: `date +%s`
2. **Environment Variable Injection** - Timestamp is set via `--set-env-vars DEPLOY_TIMESTAMP=$TIMESTAMP`
3. **Force Revision Creation** - Any environment variable change forces a new revision
4. **No Manual Restart Needed** - Container app automatically recycles with new code

### Changes Made

**File: `.github/workflows/deploy.yml`**

**For Backend:**
```yaml
- name: Generate timestamp for revision
  id: timestamp
  run: |
    TIMESTAMP=$(date +%s)
    echo "value=$TIMESTAMP" >> $GITHUB_OUTPUT

- name: Deploy backend to Azure Container Apps
  run: |
    az containerapp update \
      --name ${{ env.BACKEND_APP_NAME }} \
      --resource-group ${{ env.RESOURCE_GROUP }} \
      --image ${{ steps.acr.outputs.login_server }}/${{ env.BACKEND_IMAGE_NAME }}:${{ steps.version.outputs.tag }} \
      --set-env-vars DEPLOY_TIMESTAMP=${{ steps.timestamp.outputs.value }}  # ← Forces revision
```

**For Frontend:**
```yaml
- name: Deploy frontend to Azure Container Apps
  run: |
    az containerapp update \
      --name ${{ env.FRONTEND_APP_NAME }} \
      --resource-group ${{ env.RESOURCE_GROUP }} \
      --image ${{ steps.acr.outputs.login_server }}/${{ env.FRONTEND_IMAGE_NAME }}:${{ steps.version.outputs.tag }} \
      --set-env-vars DEPLOY_TIMESTAMP=${{ steps.timestamp.outputs.value }}  # ← Forces revision
```

## Benefits

✅ **Faster Updates** - No more manual restarts needed  
✅ **Guaranteed Rollout** - Every commit creates a new revision  
✅ **Blue-Green Ready** - Container Apps can now traffic-split between revisions if configured  
✅ **Zero Downtime** - New revision starts before old one is stopped  
✅ **Automatic** - No manual intervention required  

## Deployment Flow (Updated)

1. Developer pushes code with `[frontend]`, `[backend]`, or `[all]` prefix
2. GitHub Actions workflow triggers automatically
3. Workflow generates timestamp and builds new container image
4. During deployment, `--set-env-vars DEPLOY_TIMESTAMP=<timestamp>` forces new revision
5. Container Apps creates new revision, routes traffic, old revision scales down
6. **Total time: ~3-5 minutes from push to live**

## Testing the Improvement

1. Make a frontend change (e.g., modify a component)
2. Commit with `[frontend]` prefix
3. Push to main
4. Watch GitHub Actions build and deploy
5. New frontend code is live within 3-5 minutes automatically
6. No manual restart needed!

## Future Enhancements

- Add traffic splitting for canary deployments (90/10 or 80/20 traffic split)
- Implement health checks to auto-rollback on failures
- Add deployment notifications to Slack/Teams
- Implement multi-region deployments for global availability
