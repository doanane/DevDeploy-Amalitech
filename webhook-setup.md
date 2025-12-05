# GitHub Webhook Setup Guide

## 1. Get Your Webhook Configuration

1. Go to your project in DevDeploy
2. Navigate to: `GET /webhooks/config/{project_id}`
3. You'll receive:
   ```json
   {
     "webhook_url": "https://your-devdeploy.com/webhooks/github",
     "secret": "your_webhook_secret_here",
     "events": ["push", "workflow_run", "check_run"]
   }