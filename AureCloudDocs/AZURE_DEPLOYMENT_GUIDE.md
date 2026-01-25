




# 🚀 Azure Deployment Guide - Step by Step

This guide will walk you through deploying your LLMOps project to Azure using Jenkins CI/CD pipeline.

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Azure CLI installed (`az --version`)
- [ ] Azure account with active subscription
- [ ] Docker Desktop installed and running
- [ ] Git repository set up on GitHub
- [ ] API keys ready (GROQ_API_KEY, GOOGLE_API_KEY)




**Installing Azure CLI:**

- **macOS**: 
  ```bash
  brew update && brew install azure-cli
  ```

- **Linux**: 
  ```bash
  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
  ```

- **Windows**: 
  Download and run the [Azure CLI MSI installer](https://aka.ms/installazurecliwindows)
  
  Or using PowerShell:
  ```powershell
  Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi; Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'; rm .\AzureCLI.msi
  ```

## 🎯 Deployment Steps

### Step 1: Login to Azure & Set Environment Variables

```bash
# Login to Azure
az login

# Set your API keys (required for Jenkins deployment)
export GROQ_API_KEY="your-groq-api-key-here"
export GOOGLE_API_KEY="your-google-api-key-here"

# Verify they're set
echo $GROQ_API_KEY
echo $GOOGLE_API_KEY
```

### Step 2: Deploy Jenkins Infrastructure

This will create Jenkins on Azure with Python and Azure CLI pre-installed.

```bash
# Run the Jenkins deployment script
 1. chmod +x azure-deploy-jenkins.sh

 2. ./azure-deploy-jenkins.sh
```

**What this creates:**
- Resource Group: `llmops-jenkins-rg`
- Storage Account: `llmopsjenkinsstore` (for Jenkins data persistence)
- Container Registry: `llmopsjenkinsacr`
- Container Instance: `jenkins-llmops`

**Wait time:** ~5-7 minutes for complete deployment

**Expected output:**
```
=== Deployment Complete! ===
Jenkins URL: http://jenkins-llmops-12345.eastus.azurecontainer.io:8080
```

### Step 3: Configure Jenkins

**3.1. Access Jenkins**
- Open the Jenkins URL from the previous step
- Wait 2-3 minutes for Jenkins to fully start

**3.2. Get Initial Admin Password**
```bash
az container exec \
  --resource-group llmops-jenkins-rg \
  --name jenkins-llmops \
  --exec-command "cat /var/jenkins_home/secrets/initialAdminPassword"
```

**3.3. Complete Jenkins Setup**
1. Enter the admin password
2. Click "Install suggested plugins"
3. **IMPORTANT:** Ensure "GitHub Plugin" is installed
4. Create your admin user account
5. Confirm Jenkins URL

**3.4. Create Azure Service Principal**

Here we are giving the access to jenkins on deploy the application.

Jenkins needs credentials to deploy to Azure:

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "jenkins-llmops-sp" \
  --role Contributor \
  --scopes /subscriptions/<subscriptionID>

# This will output:
# {
#   "appId": "xxx",
#   "displayName": "jenkins-llmops-sp",
#   "password": "xxx",
#   "tenant": "xxx"
# }

# Get your subscription ID
az account show --query id -o tsv
```

**3.5. Add Credentials to Jenkins**

Go to: **Jenkins → Manage Jenkins → Manage Credentials → System → Global credentials → Add Credentials**

Add the following credentials (all as "Secret text"):

**Note:** If you get 403 error during adding the below secrets then follow below steps:

**Jenkins → Manage Jenkins → Security → CSRF Protection → Enable proxy compatibility (Enable this)**


| Credential ID | Value | Description |
|--------------|-------|-------------|
| `azure-client-id` | appId from service principal | Azure App ID |
| `azure-client-secret` | password from service principal | Azure Password |
| `azure-tenant-id` | tenant from service principal | Azure Tenant ID |
| `azure-subscription-id` | from `az account show` | Azure Subscription ID |

**Note:** We'll add `acr-username` and `acr-password` in Step 5.

### Step 4: Setup Application Infrastructure

This creates the infrastructure for your application (separate from Jenkins):

```bash
1. chmod +x scripts/azure/setup-app-infrastructure.sh

2. ./setup-app-infrastructure.sh
```

**What this creates:**
- Resource Group: `llmops-app-rg`
- Container Registry: `llmopsappacr`
- Container Apps Environment: `llmops-env`

**Expected output:**
```
╔════════════════════════════════════════════════════╗
║   Setup Complete!                                  ║
╚════════════════════════════════════════════════════╝

⚠️  IMPORTANT: Add these credentials to Jenkins:

Credential ID: acr-username
Value: llmopsappacr

Credential ID: acr-password
Value: <long-password-here>
```

**Save these credentials!** You'll need them in the next step.

### Step 5: Add ACR Credentials to Jenkins

Go back to Jenkins credentials page and add two more credentials:

| Credential ID | Value | Description |
|--------------|-------|-------------|
| `acr-username` | From setup output | App ACR Username |
| `acr-password` | From setup output | App ACR Password |

### Step 6: Build and Push Docker Image

**IMPORTANT:** Due to Azure free tier limitations, we build images locally instead of in Jenkins.

```bash
# Build and push with latest tag
1. chmod +x build-and-push-docker-image.sh

2. ./build-and-push-docker-image.sh

# Or with a specific version tag
2. ./build-and-push-docker-image.sh v1.0.0
```

**Expected output:**
```
🐳 Building Docker image locally...
📤 Pushing to ACR...
✅ Build and push complete!
Now run your Jenkins pipeline to deploy.
```

### Step 7: Create Jenkins Pipeline Job

**7.1. Create New Pipeline**
1. In Jenkins, click **"New Item"**
2. Enter name: `LLMOps-Azure-Pipeline`
3. Select **"Pipeline"**
4. Click **OK**

**7.2. Configure Pipeline**

**General Section:**
- ✅ Check "GitHub project"
- Project url: `https://github.com/YOUR-USERNAME/YOUR-REPO/`

**Build Triggers:**
- ✅ Check "GitHub hook trigger for GITScm polling"

**Pipeline Section:**
- Definition: **"Pipeline script from SCM"**
- SCM: **Git**
- Repository URL: `https://github.com/YOUR-USERNAME/YOUR-REPO.git`
- Credentials: None (for public repos)
- Branch Specifier: `*/AddingJenkins` (or your branch name)
- Script Path: `Jenkinsfile`

Click **Save**

### Step 8: Configure GitHub Webhook (Auto-Trigger Builds)

**8.1. Get your Jenkins URL:**
```bash
az container show \
  -g llmops-jenkins-rg \
  -n jenkins-llmops \
  --query "ipAddress.fqdn" -o tsv
```

**8.2. Add Webhook in GitHub:**
1. Go to your GitHub repository
2. Click **Settings** → **Webhooks** → **Add webhook**
3. Configure:
   - **Payload URL:** `http://<jenkins-url>:8080/github-webhook/`
     - Example: `http://jenkins-llmops-31002.eastus.azurecontainer.io:8080/github-webhook/`
     - ⚠️ **Note the trailing `/` after `github-webhook/`**
   - **Content type:** `application/json`
   - **Which events:** Just the push event
   - **Active:** ✅ Checked
4. Click **Add webhook**

**8.3. Verify Webhook:**
- GitHub will send a test ping
- Look for green ✅ checkmark
- If red ❌, see `JENKINS_WEBHOOK_TROUBLESHOOTING.md`

### Step 9: Run the Pipeline

**9.1. Manual Build (First Time)**
1. Go to your pipeline job: `LLMOps-Azure-Pipeline`
2. Click **"Build Now"**
3. Watch the build progress in **"Console Output"**

**9.2. Pipeline Stages:**
The pipeline will:
1. ✅ Checkout code from Git
2. ✅ Setup Python environment
3. ✅ Install dependencies
4. ✅ Run tests with coverage
5. ✅ Login to Azure
6. ✅ Verify Docker image exists in ACR
7. ✅ Deploy to Azure Container Apps
8. ✅ Verify deployment health

**9.3. Expected Duration:** ~5-8 minutes

### Step 10: Verify Deployment

**10.1. Check Build Status**
- Green ✅ = Success
- Red ❌ = Failure (check console output)

**10.2. Get Application URL**
```bash
az containerapp show \
  --name llmops-app \
  --resource-group llmops-app-rg \
  --query properties.configuration.ingress.fqdn -o tsv
```

**10.3. Test Your Application**
```bash
# Get the URL
APP_URL=$(az containerapp show \
  --name llmops-app \
  --resource-group llmops-app-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

# Test it
curl -I https://$APP_URL

# Or open in browser
echo "https://$APP_URL"
```

### Step 11: Test Automatic Deployment

Now test that pushing to Git automatically triggers deployment:

```bash
# Make a small change
echo "# Test webhook" >> test.txt

# Commit and push
git add test.txt
git commit -m "Test: webhook trigger"
git push

# Jenkins should automatically start a build!
# Check Jenkins dashboard to see new build
```

## 🎉 Success!

You now have a fully automated CI/CD pipeline!

**Your workflow:**
1. Make code changes locally
2. Run `./build-and-push-docker-image.sh` to build new Docker image
3. Push code to GitHub
4. Jenkins automatically deploys to Azure

## 📊 Monitor Your Deployment

### Check Jenkins Status
```bash
az container show \
  -g llmops-jenkins-rg \
  -n jenkins-llmops \
  --query "{Name:name, Status:containers[0].instanceView.currentState.state, URL:ipAddress.fqdn}" \
  -o table
```

### Check App Status
```bash
az containerapp show \
  -n llmops-app \
  -g llmops-app-rg \
  --query "{Name:name, Status:properties.runningStatus, URL:properties.configuration.ingress.fqdn}" \
  -o table
```

### View App Logs
```bash
az containerapp logs show \
  -n llmops-app \
  -g llmops-app-rg \
  --tail 100
```

### View Jenkins Logs
```bash
az container logs \
  -g llmops-jenkins-rg \
  -n jenkins-llmops \
  --tail 100
```

## 💰 Cost Management

### Current Monthly Costs (Approximate)

| Service | Status | Cost/Month |
|---------|--------|------------|
| Jenkins Container Instance | Running | ~$30 |
| Jenkins ACR (Basic) | Running | $5 |
| Jenkins Storage Account | Running | <$1 |
| App Container Apps | Running | ~$30 |
| App ACR (Basic) | Running | $5 |
| **Total** | **Running** | **~$71/mo** |

### Pause Services (Minimize Costs)

To minimize costs when not in use:

```bash
# Stop Jenkins (data preserved in storage)
az container delete \
  -g llmops-jenkins-rg \
  -n jenkins-llmops \
  --yes

# Stop App
az containerapp delete \
  -n llmops-app \
  -g llmops-app-rg \
  --yes

# Cost after stopping: ~$11/month (just storage and ACRs)
```

### Resume Services

```bash
# Resume everything
./resume-services.sh
```

### Complete Cleanup (Zero Charges)

⚠️ **WARNING:** This deletes everything including Jenkins configuration and data!

```bash
./complete-deep-cleanup.sh
```

## 🔧 Maintenance Tasks

### Update Application Code

```bash
# 1. Make your code changes
# 2. Build new Docker image
./build-and-push-docker-image.sh v1.1.0

# 3. Push to Git (triggers Jenkins)
git add .
git commit -m "Update: new feature"
git push

# Jenkins will automatically deploy the new version
```

### Update Jenkins Configuration

If you need to update Jenkins settings, they persist in Azure File Storage, so:
1. Make changes in Jenkins UI
2. Changes are automatically saved
3. Even if you delete and recreate the container, settings remain

### Scale Application

```bash
# Scale to more replicas
az containerapp update \
  --name llmops-app \
  --resource-group llmops-app-rg \
  --min-replicas 2 \
  --max-replicas 5
```

## 🐛 Troubleshooting

### Pipeline Fails: "Image not found in ACR"

**Solution:** Build and push the image first:
```bash
./build-and-push-docker-image.sh
```

### GitHub Webhook Not Triggering

**Solution:** See detailed guide: `JENKINS_WEBHOOK_TROUBLESHOOTING.md`

Quick checks:
```bash
# 1. Verify Jenkins is accessible
curl -I http://<jenkins-url>:8080/github-webhook/

# 2. Check webhook status in GitHub
# Settings → Webhooks → Click your webhook → Recent Deliveries
```

### Pipeline Fails: Authentication Error

**Solution:** Verify Jenkins credentials:
1. Jenkins → Manage Jenkins → Manage Credentials
2. Check all 6 credentials exist:
   - azure-client-id
   - azure-client-secret
   - azure-tenant-id
   - azure-subscription-id
   - acr-username
   - acr-password

### Application Not Responding

```bash
# Check app status
az containerapp show \
  -n llmops-app \
  -g llmops-app-rg \
  --query properties.runningStatus

# Check logs
az containerapp logs show \
  -n llmops-app \
  -g llmops-app-rg \
  --tail 100
```

### Jenkins Won't Start

```bash
# Check logs
az container logs \
  -g llmops-jenkins-rg \
  -n jenkins-llmops \
  --tail 100

# Check events
az container show \
  -g llmops-jenkins-rg \
  -n jenkins-llmops \
  --query "containers[0].instanceView.events" \
  -o table
```

## 📚 Additional Resources

- **Complete Reference:** `AZURE_LLMOPS_COMPLETE_GUIDE.md`
- **Webhook Troubleshooting:** `JENKINS_WEBHOOK_TROUBLESHOOTING.md`
- **Jenkins Dashboard:** Your Jenkins URL (from Step 2)
- **Azure Portal:** https://portal.azure.com

## 🎯 Quick Command Reference

```bash
# Deploy Jenkins
./azure-deploy-jenkins.sh

# Setup app infrastructure
./setup-app-infrastructure.sh

# Build and push image
./build-and-push-docker-image.sh

# Resume services
./resume-services.sh

# Cleanup app only
./cleanup-app-deployment.sh

# Cleanup everything
./complete-deep-cleanup.sh

# Get Jenkins URL
az container show -g llmops-jenkins-rg -n jenkins-llmops --query ipAddress.fqdn -o tsv

# Get App URL
az containerapp show -n llmops-app -g llmops-app-rg --query properties.configuration.ingress.fqdn -o tsv

# View Jenkins logs
az container logs -g llmops-jenkins-rg -n jenkins-llmops --tail 100

# View App logs
az containerapp logs show -n llmops-app -g llmops-app-rg --tail 100
```

---

**Need Help?** Check the troubleshooting section or review the console output for specific error messages.

**Last Updated:** October 2025

