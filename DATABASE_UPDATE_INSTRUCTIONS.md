# Database Update Instructions

## New Database Connection Details
```
postgresql://license_db_new_ntwx_user:zuDku3V3lGGsWFPJyXVYEbKcSbOV2TBL@dpg-d7qshavavr4c73f5nsdg-a/license_db_new_ntwx
```

## Steps to Update Your Render Database

### 1. Update Environment Variables in Render Dashboard

1. Go to your Render Dashboard: https://dashboard.render.com
2. Navigate to your `license-server` service
3. Go to the "Environment" tab
4. Update the `DATABASE_URL` environment variable with the new connection string:

**Key:** `DATABASE_URL`
**Value:** `postgresql://license_db_new_ntwx_user:zuDku3V3lGGsWFPJyXVYEbKcSbOV2TBL@dpg-d7qshavavr4c73f5nsdg-a/license_db_new_ntwx`

### 2. Redeploy Your Service

After updating the environment variable:
1. Go to the "Events" tab in your Render dashboard
2. Click "Manual Deploy" or "Push Changes" to trigger a new deployment
3. Wait for the deployment to complete

### 3. Verify Database Connection

Once deployed, you can verify the connection by:
1. Checking the logs in Render dashboard
2. Looking for the message "✅ Using PostgreSQL database"
3. Testing your API endpoints

## Current Configuration Analysis

Your current setup is correctly configured to:
- ✅ Read DATABASE_URL from environment variables
- ✅ Handle postgresql:// URLs (already correct format)
- ✅ Fall back to SQLite if no DATABASE_URL is provided
- ✅ Use proper connection pooling settings

## What Needs to Be Done

1. **Only update the DATABASE_URL environment variable** - no code changes needed
2. **Redeploy the service** to apply the new environment variable
3. **Test the connection** to ensure it works

## Important Notes

- Your new database is empty, so you'll need to run database migrations/initialization
- The old database data will not be transferred automatically
- Make sure to update any other services that might connect to this database

## Quick Copy-Paste for Render

```
postgresql://license_db_new_ntwx_user:zuDku3V3lGGsWFPJyXVYEbKcSbOV2TBL@dpg-d7qshavavr4c73f5nsdg-a/license_db_new_ntwx
```
