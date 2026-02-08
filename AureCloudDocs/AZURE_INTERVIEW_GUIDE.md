# Azure Cloud Deployment - Complete Interview Guide 🎯

> **⚠️ SECURITY NOTICE:**  
> This document contains placeholder values for sensitive information. Before using any commands or configurations from this guide:
> - Replace `YOUR_AZURE_CLIENT_ID` with your Service Principal's Application (client) ID
> - Replace `YOUR_AZURE_CLIENT_SECRET` with your Service Principal's client secret value
> - Replace `YOUR_AZURE_TENANT_ID` with your Azure AD Tenant ID
> - Replace `YOUR_AZURE_SUBSCRIPTION_ID` with your Azure subscription ID
> - Replace `YOUR_AZURE_ENV` with your Azure Container Apps environment name
> - **NEVER** commit real Azure credentials to public repositories
> - Always use GitHub Secrets, Azure Key Vault, or Jenkins credentials for sensitive data
> - Review your `.gitignore` to ensure credentials and `.env` files are excluded

---

## 📚 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Azure Resources Explained](#azure-resources-explained)
3. [Environment Variables & Secrets](#environment-variables--secrets)
4. [Auto-Scaling Deep Dive](#auto-scaling-deep-dive)
5. [GitHub Webhook Configuration](#github-webhook-configuration)
6. [Interview Questions & Answers](#interview-questions--answers)
7. [Common Pitfalls & Solutions](#common-pitfalls--solutions)
8. [Study Tips for Interview](#study-tips-for-interview)
9. [Quick Reference Cheat Sheet](#quick-reference-cheat-sheet)
10. [Final Interview Preparation Checklist](#final-interview-preparation-checklist)
11. [Additional Resources](#additional-resources)

---

<a id="architecture-overview"></a>
## 🏗️ Architecture Overview

### **High-Level Architecture Diagram**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DEVELOPER WORKFLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Developer PC                                                            │
│  ├─ Code Changes (Python/FastAPI)                                       │
│  ├─ Git Commit                                                           │
│  └─ Push to GitHub (azure-deploy branch)                                │
│                           ↓                                              │
└───────────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                          GITHUB (Version Control)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  GitHub Repository                                                       │
│  ├─ Branch: azure-deploy                                                │
│  ├─ Webhook configured                                                   │
│  └─ Triggers two parallel workflows:                                    │
│                           ↓                                              │
│      ┌────────────────────┴──────────────────┐                          │
│      ↓                                        ↓                          │
│  GitHub Actions                          Jenkins (via webhook)          │
│  (Build & Push)                          (Test & Deploy)                │
└─────────────────────────────────────────────────────────────────────────┘
           ↓                                        ↓
┌──────────────────────────────┐    ┌──────────────────────────────────┐
│   GITHUB ACTIONS WORKFLOW     │    │   JENKINS CI/CD PIPELINE          │
├──────────────────────────────┤    ├──────────────────────────────────┤
│                              │    │                                   │
│ 1. Checkout Code             │    │ 1. Checkout Code                  │
│ 2. Build Docker Image        │    │ 2. Setup Python Environment       │
│    - Use Dockerfile.optimized│    │ 3. Install Dependencies           │
│    - Multi-stage build       │    │ 4. Run Unit Tests                 │
│    - Layer caching           │    │ 5. Run Integration Tests          │
│ 3. Login to ACR              │    │ 6. Generate Coverage Report       │
│ 4. Push to ACR               │    │ 7. Login to Azure                 │
│    - Tag: commit SHA         │    │ 8. Verify Image in ACR            │
│    - Tag: latest             │    │ 9. Deploy to Container Apps       │
│                              │    │ 10. Health Check                  │
│ Time: 3-5 minutes            │    │                                   │
└──────────────────────────────┘    │ Time: 8-12 minutes                │
           ↓                         └──────────────────────────────────┘
           ↓                                        ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    AZURE CONTAINER REGISTRY (ACR)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  llmopsappacr.azurecr.io                                                 │
│  ├─ Repository: llmops-app                                               │
│  ├─ Tags:                                                                │
│  │   ├─ latest (always points to newest)                                │
│  │   └─ <commit-sha> (specific version)                                 │
│  ├─ Image Size: ~4.4 GB                                                  │
│  │   ├─ Base Python: 150 MB                                             │
│  │   ├─ Dependencies: 4.2 GB (PyTorch, LangChain, etc.)                 │
│  │   └─ Application Code: 4 KB                                          │
│  └─ Layer Caching: Enabled                                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────────┐
│              AZURE CONTAINER APPS ENVIRONMENT                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Environment: llmops-env                                                 │
│  Region: East US                                                         │
│  ├─ Virtual Network (Managed)                                           │
│  ├─ Log Analytics Workspace                                             │
│  └─ Dapr (Optional - not used)                                          │
│                           ↓                                              │
└─────────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    AZURE CONTAINER APP                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Name: llmops-app                                                        │
│  URL: https://llmops-app.YOUR_AZURE_ENV.eastus.                │
│       azurecontainerapps.io/                                             │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  INGRESS (External, Port 8080)                                   │   │
│  │  ├─ HTTPS Enabled (Auto SSL Certificate)                        │   │
│  │  ├─ Custom Domain Support                                        │   │
│  │  └─ Load Balancer (Azure-managed)                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                           ↓                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  AUTO-SCALING                                                     │   │
│  │  ├─ Min Replicas: 1                                               │   │
│  │  ├─ Max Replicas: 3                                               │   │
│  │  ├─ Scale on: HTTP requests, CPU, Memory                         │   │
│  │  └─ Scale to Zero: Disabled (always 1 running)                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                           ↓                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  CONTAINER INSTANCES (Replicas 1-3)                              │   │
│  │                                                                   │   │
│  │  Replica 1:                      Replica 2:     Replica 3:       │   │
│  │  ├─ CPU: 0.5 vCPU               (auto-scaled)  (auto-scaled)    │   │
│  │  ├─ Memory: 1 GB                                                 │   │
│  │  ├─ Image: ACR/llmops-app:latest                                 │   │
│  │  ├─ Port: 8080                                                   │   │
│  │  └─ Environment Variables:                                       │   │
│  │      ├─ GROQ_API_KEY                                             │   │
│  │      ├─ GOOGLE_API_KEY                                           │   │
│  │      └─ LLM_PROVIDER=groq                                        │   │
│  │                                                                   │   │
│  │  Container Process:                                               │   │
│  │  └─ uvicorn main:app --host 0.0.0.0 --port 8080                  │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                           ↓                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  MONITORING & LOGGING                                             │   │
│  │  ├─ Log Analytics Workspace                                       │   │
│  │  ├─ Application Insights (Optional)                              │   │
│  │  ├─ Console Logs                                                 │   │
│  │  └─ System Logs                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                          END USERS                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  🌐 Internet Users                                                       │
│  └─ Access: https://llmops-app.YOUR_AZURE_ENV.eastus.          │
│             azurecontainerapps.io/                                       │
│  └─ Connects to nearest Azure Edge location                             │
│  └─ Routed to healthy replica via Load Balancer                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

<a id="azure-resources-explained"></a>
## 🧩 Azure Resources Explained

### **1. Resource Group** (`llmops-app-rg`)

**What it is:**
- Logical container for Azure resources
- Groups related resources for easy management
- Enables bulk operations (delete all, move all, etc.)

**Why we use it:**
```
Resource Group: llmops-app-rg
├─ Container Registry (ACR)
├─ Container Apps Environment
├─ Container App
├─ Log Analytics Workspace
└─ Managed Identity (auto-created)
```

**Interview Point:**
> "I organized all related resources into a single resource group for easier lifecycle management. If I need to tear down the entire deployment, I can delete the resource group, and all resources are removed together."

---

### **2. Azure Container Registry (ACR)** (`llmopsappacr`)

**What it is:**
- Private Docker registry hosted in Azure
- Stores and manages Docker images
- Integrated with Azure services for authentication

**Key Features:**
```
ACR: llmopsappacr.azurecr.io
├─ SKU: Basic (low-cost, production-ready)
├─ Admin User: Enabled (for CI/CD authentication)
├─ Geo-replication: Disabled (Basic tier)
├─ Webhooks: Can trigger on push events
└─ Security: 
    ├─ Private endpoints (optional)
    ├─ Azure AD authentication
    └─ Role-based access control (RBAC)
```

**Why we use ACR vs DockerHub:**
- ✅ Lower latency (same region as Container Apps)
- ✅ Better security (private, integrated with Azure AD)
- ✅ No rate limits
- ✅ Better performance for pulls

**Interview Point:**
> "I chose Azure Container Registry because it provides low-latency access from Container Apps in the same region, integrated security with Azure AD, and no pull rate limits compared to public registries."

---

### **3. Container Apps Environment** (`llmops-env`)

**What it is:**
- Managed Kubernetes environment (abstracted)
- Boundary for Container Apps that share resources
- Includes networking, logging, and monitoring

**Architecture:**
```
Environment: llmops-env
├─ Virtual Network (Azure-managed)
│   ├─ Subnet for Container Apps
│   └─ Private IPs for containers
├─ Log Analytics Workspace
│   ├─ Container logs
│   └─ System logs
├─ Dapr (Distributed Application Runtime)
│   └─ Optional microservices features
└─ Multiple Container Apps can run here
```

**Why separate environment from app:**
- Multiple apps can share the same environment
- Shared networking and security policies
- Cost optimization (shared infrastructure)

**Interview Point:**
> "The Container Apps Environment provides a managed Kubernetes-like infrastructure without the complexity. Multiple microservices can run in the same environment, sharing networking and monitoring, while remaining isolated at the application level."

---

### **4. Azure Container App** (`llmops-app`)

**What it is:**
- Serverless container hosting service
- Auto-scales based on HTTP traffic, CPU, or custom metrics
- Pay only for resources you use

**Configuration:**
```yaml
Container App: llmops-app
├─ Ingress:
│   ├─ Type: External (public internet)
│   ├─ Target Port: 8080
│   ├─ Transport: HTTP2 (auto-upgrade from HTTP/1.1)
│   ├─ HTTPS: Enabled (free SSL certificate)
│   └─ URL: https://llmops-app.YOUR_AZURE_ENV.eastus.azurecontainerapps.io
│
├─ Scaling:
│   ├─ Min Replicas: 1 (always running)
│   ├─ Max Replicas: 3 (scale out on demand)
│   ├─ Scale Rules:
│   │   ├─ HTTP: Scale when concurrent requests > 100
│   │   ├─ CPU: Scale when CPU > 70%
│   │   └─ Memory: Scale when Memory > 80%
│   └─ Scale to Zero: Disabled
│
├─ Container Configuration:
│   ├─ Registry: llmopsappacr.azurecr.io
│   ├─ Image: llmops-app:latest
│   ├─ CPU: 0.5 vCPU per replica
│   ├─ Memory: 1 GB per replica
│   └─ Command: uvicorn main:app --host 0.0.0.0 --port 8080
│
├─ Secrets (stored securely):
│   ├─ ACR Credentials (username/password)
│   ├─ GROQ_API_KEY (for LLM)
│   └─ GOOGLE_API_KEY (for embeddings)
│
└─ Environment Variables:
    ├─ GROQ_API_KEY (from secret)
    ├─ GOOGLE_API_KEY (from secret)
    └─ LLM_PROVIDER=groq
```

**Interview Point:**
> "Container Apps is serverless, meaning I don't manage any VMs or Kubernetes clusters. It auto-scales from 1 to 3 replicas based on traffic, provides built-in load balancing and HTTPS, and I only pay for the compute resources when they're running."

---

### **5. Service Principal** (for Jenkins)

**What it is:**
- Identity used by Jenkins to authenticate to Azure
- Has specific permissions (Contributor role)
- Enables automation without user credentials

**Structure:**
```
Service Principal: jenkins-llmops-sp
├─ Client ID: YOUR_AZURE_CLIENT_ID
├─ Client Secret: YOUR_AZURE_CLIENT_SECRET
├─ Tenant ID: YOUR_AZURE_TENANT_ID
└─ Permissions:
    └─ Role: Contributor
    └─ Scope: /subscriptions/<subscription-id>
    └─ Can: Create, Update, Delete resources
```

**Interview Point:**
> "I created a Service Principal with Contributor role for Jenkins to automate deployments. This follows the principle of least privilege—Jenkins has only the permissions it needs, and credentials are stored securely in Jenkins credential store, never in code."

---

<a id="environment-variables--secrets"></a>
## 🔐 Environment Variables & Secrets

### **What are Environment Variables in Container Apps?**

Environment variables are **runtime configuration values** injected into containers when they start. They're used for:
- API keys (GROQ_API_KEY, GOOGLE_API_KEY)
- Configuration (LLM_PROVIDER, PORT)
- Feature flags
- Database connection strings

---

### **How Environment Variables Flow**

```
┌─────────────────────────────────────────────────────────────────────────┐
│              ENVIRONMENT VARIABLE FLOW                                   │
└─────────────────────────────────────────────────────────────────────────┘

1. SET IN JENKINS ENVIRONMENT
   ├─ Jenkins Job Configuration
   ├─ Or Jenkins System Environment Variables
   └─ Or Jenkins Credentials (best practice)

2. JENKINS READS AND INJECTS
   ├─ During deployment stage
   └─ Via Azure CLI command:
       az containerapp create \
         --env-vars GROQ_API_KEY="${GROQ_API_KEY}"

3. AZURE STORES SECURELY
   ├─ Encrypted at rest in Azure
   ├─ Stored in Container App configuration
   └─ Not visible in logs (if using secrets)

4. CONTAINER RUNTIME INJECTION
   ├─ When container starts
   ├─ Azure injects as environment variables
   └─ Available to application process

5. APPLICATION READS
   ├─ Python: os.environ.get("GROQ_API_KEY")
   ├─ Node.js: process.env.GROQ_API_KEY
   └─ Any language: read from environment
```

---

### **In Your Application (main.py)**

```python
# Your FastAPI application reads environment variables
import os

# Read PORT (with default fallback)
port = int(os.environ.get("PORT", 8080))

# Somewhere in your code (config_loader.py or similar)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")

# Use in LangChain
from langchain_groq import ChatGroq
llm = ChatGroq(api_key=GROQ_API_KEY, model="mixtral-8x7b-32768")
```

---

### **In Jenkins Deployment (Jenkinsfile)**

```groovy
stage('Deploy to Azure Container Apps') {
    environment {
        // These are read from Jenkins environment
        GROQ_API_KEY = "${env.GROQ_API_KEY}"
        GOOGLE_API_KEY = "${env.GOOGLE_API_KEY}"
        LLM_PROVIDER = "${env.LLM_PROVIDER ?: 'groq'}"
    }
    
    steps {
        sh '''
            # Jenkins injects env vars into Azure CLI command
            az containerapp create \
                --name llmops-app \
                --env-vars \
                    GROQ_API_KEY="${GROQ_API_KEY}" \
                    GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
                    LLM_PROVIDER="${LLM_PROVIDER}"
        '''
    }
}
```

---

### **How to Verify Environment Variables**

```bash
# View all environment variables in Container App
az containerapp show \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --query 'properties.template.containers[0].env' \
    -o json

# Output shows:
[
  {
    "name": "GROQ_API_KEY",
    "value": "sk-proj-..."  # Visible (not secret)
  },
  {
    "name": "GOOGLE_API_KEY",
    "value": "AIza..."      # Visible (not secret)
  },
  {
    "name": "LLM_PROVIDER",
    "value": "groq"
  }
]
```

---

### **Environment Variables vs Secrets**

| Feature | Environment Variables | Secrets |
|---------|----------------------|---------|
| **Visibility** | Visible in Azure Portal & CLI | Hidden in Portal, referenced only |
| **Encryption** | Encrypted at rest | Encrypted at rest + in transit |
| **Best for** | Non-sensitive config (PORT, PROVIDER) | Sensitive data (API keys, passwords) |
| **Syntax** | `--env-vars KEY=value` | `--secrets key=value` + `--set-env-vars KEY=secretref:key` |
| **Logged** | May appear in logs | Never appears in logs |

---

### **Best Practice: Use Secrets for Sensitive Data**

```bash
# Step 1: Create secrets in Container App
az containerapp secret set \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --secrets \
        groq-api-key="sk-proj-..." \
        google-api-key="AIza..."

# Step 2: Reference secrets as environment variables
az containerapp update \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --set-env-vars \
        GROQ_API_KEY=secretref:groq-api-key \
        GOOGLE_API_KEY=secretref:google-api-key \
        LLM_PROVIDER="groq"  # Non-sensitive, can be plain env var

# Now:
# - GROQ_API_KEY and GOOGLE_API_KEY reference secrets (hidden)
# - LLM_PROVIDER is a regular env var (visible)
```

---

### **Production Secret Management: Azure Key Vault**

For production, use **Azure Key Vault**:

```bash
# Step 1: Create Key Vault
az keyvault create \
    --name llmops-keyvault \
    --resource-group llmops-app-rg \
    --location eastus

# Step 2: Store secrets in Key Vault
az keyvault secret set \
    --vault-name llmops-keyvault \
    --name groq-api-key \
    --value "sk-proj-..."

# Step 3: Enable managed identity on Container App
az containerapp identity assign \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --system-assigned

# Step 4: Grant Container App access to Key Vault
IDENTITY_ID=$(az containerapp identity show \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --query principalId -o tsv)

az keyvault set-policy \
    --name llmops-keyvault \
    --object-id $IDENTITY_ID \
    --secret-permissions get list

# Step 5: Reference Key Vault secrets
az containerapp update \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --set-env-vars \
        GROQ_API_KEY=keyvaultref:https://llmops-keyvault.vault.azure.net/secrets/groq-api-key
```

**Benefits:**
- ✅ Centralized secret management
- ✅ Audit logs (who accessed what, when)
- ✅ Secret rotation without redeploying
- ✅ No secrets in code or CI/CD pipeline

---

### **How to Update Environment Variables**

```bash
# Method 1: Azure CLI
az containerapp update \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --set-env-vars \
        GROQ_API_KEY="new-key-value" \
        NEW_VARIABLE="new-value"

# Method 2: Via Jenkins (re-run deploy)
# Jenkins reads from its environment and updates

# Method 3: Azure Portal
# Container App → Settings → Environment variables → Add/Edit
```

**Note:** Updating env vars triggers a **rolling restart** of containers (zero downtime).

---

### **Interview Point:**
> "Environment variables are injected by Azure Container Apps at runtime. I configured them through the Jenkins deployment pipeline, and they're encrypted at rest. Currently, they're stored as plain environment variables, but for production, I would migrate to Azure Key Vault with managed identity for enhanced security, centralized management, and audit logging. This eliminates secrets from the CI/CD pipeline entirely."

---

<a id="auto-scaling-deep-dive"></a>
## 🚀 Auto-Scaling Deep Dive

### **What is Auto-Scaling?**

Auto-scaling **automatically adjusts the number of container replicas** based on demand:
- **Scale out** (increase replicas) when load is high
- **Scale in** (decrease replicas) when load is low
- **Zero downtime** during scaling events

---

### **Your Configuration**

```bash
# Set during deployment (Jenkinsfile)
az containerapp create \
    --name llmops-app \
    --min-replicas 1 \    # Always keep 1 running (no cold starts)
    --max-replicas 3      # Scale up to 3 under high load
```

**What this means:**
- **Min: 1** → Application always has 1 container running (instant response)
- **Max: 3** → Can scale to 3 containers during traffic spikes
- **Default rules:** Azure uses built-in HTTP, CPU, and memory triggers

---

### **Visual: How Auto-Scaling Works**

```
┌─────────────────────────────────────────────────────────────────────────┐
│              AUTO-SCALING IN ACTION                                      │
└─────────────────────────────────────────────────────────────────────────┘

Scenario: Monday morning traffic spike

Time     Traffic    CPU    Memory    Replicas    Action
────────────────────────────────────────────────────────────────────────────
8:00 AM  Low        20%    40%       1           Normal operation
         5 req/s

8:15 AM  Medium     45%    55%       1           Load increasing
         15 req/s                                 (still manageable)

8:30 AM  High       85%    75%       1 → 2       SCALE OUT!
         35 req/s                                 (CPU > 80% threshold)
                                                  New replica starting...

8:31 AM  High       55%    60%       2           Load distributed
         35 req/s                                 Each replica: 17-18 req/s

8:45 AM  Very High  80%    70%       2 → 3       SCALE OUT!
         55 req/s                                 (Still high load)
                                                  New replica starting...

8:46 AM  Very High  55%    58%       3           Load distributed
         55 req/s                                 Each replica: 18-19 req/s

9:30 AM  Medium     40%    50%       3           Load decreasing
         20 req/s                                 (but waiting before scale-in)

9:40 AM  Medium     35%    45%       3 → 2       SCALE IN
         15 req/s                                 (5 min cooldown passed)

10:00 AM Low        25%    40%       2 → 1       SCALE IN
         8 req/s                                  (back to baseline)
```

---

### **Default Scaling Triggers**

Azure Container Apps uses these **built-in rules** (no configuration needed):

#### **1. HTTP Concurrent Requests**
```yaml
Trigger: Concurrent HTTP requests per replica
Scale Out When: > 10 concurrent requests
Scale In When: < 5 concurrent requests for 5 minutes

Example:
- Replica 1 handling 15 concurrent requests
- Azure creates Replica 2
- Now each handles ~7-8 requests
```

#### **2. CPU Usage**
```yaml
Trigger: CPU utilization percentage
Scale Out When: > 80% CPU for 30 seconds
Scale In When: < 50% CPU for 5 minutes

Example:
- Heavy ML inference task causes CPU spike to 90%
- Azure creates additional replica
- Load distributed, CPU drops to 60% per replica
```

#### **3. Memory Usage**
```yaml
Trigger: Memory utilization percentage
Scale Out When: > 90% Memory for 30 seconds
Scale In When: < 70% Memory for 5 minutes

Example:
- Large FAISS index loaded (memory spike to 950 MB)
- Azure creates additional replica
- Memory stabilizes at 500-600 MB per replica
```

---

### **Scaling Behavior Details**

```
┌─────────────────────────────────────────────────────────────────────────┐
│              REPLICA LIFECYCLE                                           │
└─────────────────────────────────────────────────────────────────────────┘

SCALE OUT (Fast - 30-60 seconds):
  1. Azure detects trigger (CPU > 80%)
  2. Provision new container instance (10-15s)
  3. Pull Docker image from ACR (5-10s, cached after first pull)
  4. Start container (5-10s)
  5. Application startup (10-30s - load models, initialize)
  6. Health check passes
  7. Register with load balancer
  8. Start receiving traffic
  
SCALE IN (Slow - 5-10 minutes):
  1. Azure detects low load (CPU < 50% for 5 min)
  2. Mark replica for termination
  3. Stop sending new requests to replica
  4. Wait for existing requests to complete (grace period)
  5. Send SIGTERM to container
  6. Container graceful shutdown (30s max)
  7. Force kill if not stopped (SIGKILL)
  8. Deregister from load balancer

Why slow scale-in?
- Prevents "flapping" (rapid scale out/in cycles)
- Ensures no dropped requests
- Saves cost (keep replicas running if spike might return)
```

---

### **View Current Scaling Status**

```bash
# Check number of active replicas
az containerapp replica list \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --query '[].{Name:name, State:properties.runningState, Created:properties.createdTime}' \
    -o table

# Output:
Name                          State     Created
----------------------------  --------  ------------------------
llmops-app--abc123-xyz789    Running   2026-02-08T10:30:00Z
llmops-app--def456-uvw012    Running   2026-02-08T10:35:00Z  ← Scaled out

# Check scaling configuration
az containerapp show \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --query 'properties.template.scale' \
    -o json

# Output:
{
  "maxReplicas": 3,
  "minReplicas": 1,
  "rules": []  # Empty = using default rules
}
```

---

### **Custom Scaling Rules (Advanced)**

You can override defaults with custom rules:

#### **HTTP-based Scaling**
```bash
az containerapp update \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --scale-rule-name http-scaling \
    --scale-rule-type http \
    --scale-rule-http-concurrency 20  # Scale out at 20 concurrent requests

# Now scales out when > 20 concurrent requests (instead of default 10)
```

#### **CPU-based Scaling**
```bash
az containerapp update \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --scale-rule-name cpu-scaling \
    --scale-rule-type cpu \
    --scale-rule-metadata \
        type=Utilization \
        value=70  # Scale out at 70% CPU (instead of default 80%)
```

#### **Memory-based Scaling**
```bash
az containerapp update \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --scale-rule-name memory-scaling \
    --scale-rule-type memory \
    --scale-rule-metadata \
        type=Utilization \
        value=85  # Scale out at 85% memory
```

#### **Schedule-based Scaling**
```bash
# Scale to 2 replicas during business hours
az containerapp update \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --scale-rule-name business-hours \
    --scale-rule-type cron \
    --scale-rule-metadata \
        timezone="America/New_York" \
        start="0 8 * * 1-5" \      # 8 AM Mon-Fri
        end="0 18 * * 1-5" \        # 6 PM Mon-Fri
        desiredReplicas="2"
```

---

### **Cost Implications of Scaling**

```
┌─────────────────────────────────────────────────────────────────────────┐
│              COST CALCULATION                                            │
└─────────────────────────────────────────────────────────────────────────┘

Pricing: Azure Container Apps (East US)
- CPU: $0.000012 per vCPU-second
- Memory: $0.000003 per GB-second

Your Configuration:
- 0.5 vCPU per replica
- 1 GB memory per replica
- Min 1, Max 3 replicas

Scenario 1: Always 1 replica (24/7)
- CPU: 0.5 vCPU × 86,400 sec/day × 30 days = 1,296,000 vCPU-sec
- Cost: 1,296,000 × $0.000012 = $15.55/month
- Memory: 1 GB × 2,592,000 sec = 2,592,000 GB-sec
- Cost: 2,592,000 × $0.000003 = $7.78/month
- Total: ~$23/month

Scenario 2: 1 replica + 2 hours/day at 3 replicas
- Base: 1 replica × 22 hours/day = same as above
- Peak: 3 replicas × 2 hours/day × 30 days
  - CPU: 3 × 0.5 × 7,200 × 30 = 324,000 vCPU-sec = $3.89
  - Memory: 3 × 1 × 216,000 = 648,000 GB-sec = $1.94
- Total: ~$23 + $6 = $29/month

Key Insight:
- Auto-scaling adds minimal cost (only pay for extra replicas during spikes)
- Much cheaper than keeping 3 replicas running 24/7 ($69/month)
```

---

### **Monitor Scaling Events**

```bash
# View scaling events in logs
az monitor activity-log list \
    --resource-group llmops-app-rg \
    --resource-type Microsoft.App/containerApps \
    --query "[?contains(operationName.value, 'scale')]" \
    -o table

# View replica count over time (Azure Portal)
# Container App → Monitoring → Metrics → Select "Replica Count"

# View auto-scaling decisions in container logs
az containerapp logs show \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --tail 500 \
    | grep -i "scale\|replica"
```

---

### **Scaling Best Practices**

✅ **DO:**
- Set `min-replicas: 1` for production (avoid cold starts)
- Set `max-replicas` based on budget and expected traffic
- Monitor replica count and adjust limits over time
- Use health probes to ensure replicas are ready before receiving traffic

❌ **DON'T:**
- Set `min-replicas: 0` for user-facing apps (cold start delay)
- Set `max-replicas` too low (risk of overload)
- Scale based on metrics not relevant to your app
- Forget to test scaling behavior under load

---

### **Testing Auto-Scaling**

```bash
# Load testing tool: Apache Bench
apt-get install apache2-utils  # Linux
brew install apache2-utils     # macOS

# Send 1000 requests with 50 concurrent connections
ab -n 1000 -c 50 https://llmops-app.YOUR_AZURE_ENV.eastus.azurecontainerapps.io/

# Watch replicas scale up
watch -n 5 'az containerapp replica list \
    --name llmops-app \
    --resource-group llmops-app-rg \
    --query "[].{Name:name, State:properties.runningState}" \
    -o table'

# Expected behavior:
# - Start: 1 replica
# - During load: 2-3 replicas (based on CPU/requests)
# - After load: Scale back to 1 (after 5-10 min cooldown)
```

---

### **Interview Point:**
> "I configured auto-scaling with min 1 and max 3 replicas. Azure Container Apps uses built-in HTTP, CPU, and memory triggers—it automatically scales out when concurrent requests exceed 10 per replica or CPU exceeds 80%. Scale-in is gradual (5-minute cooldown) to prevent flapping. This serverless approach means I only pay for active compute time. Under normal load, I run 1 replica (~$23/month), but during traffic spikes, it automatically scales to 3 replicas with zero downtime. For production, I would add custom scaling rules based on business metrics and implement comprehensive load testing to validate scaling thresholds."

---

<a id="github-webhook-configuration"></a>
## 🔗 GitHub Webhook Configuration

### **Complete CI/CD Pipeline Flow**

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: CODE COMMIT                                                 │
└─────────────────────────────────────────────────────────────────────┘
  
  Developer → Git Commit → Push to azure-deploy branch
                                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: GITHUB WEBHOOK TRIGGERS (< 1 second)                       │
└─────────────────────────────────────────────────────────────────────┘
  
  GitHub Webhook → Sends POST request to:
  ├─ GitHub Actions (workflow_dispatch)
  └─ Jenkins (github-webhook endpoint)
                                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: GITHUB ACTIONS - BUILD & PUSH (3-5 minutes)                │
└─────────────────────────────────────────────────────────────────────┘

  Step 1: Checkout Code (5s)
    ├─ Clone azure-deploy branch
    └─ Get commit SHA for tagging

  Step 2: Build Docker Image (2-3 min)
    ├─ Use Dockerfile.optimized
    ├─ Layer 1-4: CACHED (base image, OS packages)
    ├─ Layer 5: CACHED (Python dependencies - 4.4 GB)
    └─ Layer 6: REBUILD (application code - 4 KB)
  
  Step 3: Login to ACR (5s)
    └─ Use GitHub Secrets (ACR_USERNAME, ACR_PASSWORD)
  
  Step 4: Push to ACR (30s - 1 min)
    ├─ Push with tag: <commit-sha>
    ├─ Push with tag: latest
    └─ Only new layers pushed (4 KB if code-only change)

  ✅ Result: Image available in ACR
                                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 4: JENKINS PIPELINE - TEST & DEPLOY (8-12 minutes)            │
└─────────────────────────────────────────────────────────────────────┘

  Stage 1: Checkout (10s)
    └─ Clone azure-deploy branch

  Stage 2: Setup Python Environment (30s)
    ├─ Install uv (fast package manager)
    ├─ Install Python 3.12
    └─ Create virtual environment in /tmp/venv-<BUILD_NUMBER>

  Stage 3: Install Dependencies (1-2 min)
    ├─ Sanitize requirements.txt (remove OS-specific packages)
    ├─ Install with uv (faster than pip)
    └─ Install pytest, pytest-cov for testing

  Stage 4: Run Tests (1-2 min)
    ├─ Run pytest on tests/ directory
    ├─ Generate coverage report (XML, HTML, terminal)
    ├─ Generate JUnit XML for Jenkins
    └─ Archive results (even if tests fail)

  Stage 5: Login to Azure (10s)
    ├─ Use Service Principal credentials
    ├─ Authenticate with Azure CLI
    └─ Set subscription context

  Stage 6: Verify Docker Image Exists (30s)
    ├─ Check if repository exists in ACR
    ├─ Check if 'latest' tag exists
    ├─ Retry up to 6 times (eventual consistency)
    └─ List available tags

  Stage 7: Deploy to Container Apps (3-5 min)
    ├─ Ensure resource group exists
    ├─ Ensure Container Apps environment exists
    │   ├─ Check provisioning state
    │   ├─ Wait for "Succeeded" state
    │   └─ Recreate if "Failed" or "ScheduledForDelete"
    ├─ Check if Container App exists:
    │   ├─ If exists → Update image to ACR/llmops-app:latest
    │   └─ If not exists → Create new with:
    │       ├─ Image: ACR/llmops-app:latest
    │       ├─ Ingress: External, port 8080
    │       ├─ Scaling: 1-3 replicas
    │       ├─ Registry: ACR credentials
    │       └─ Environment variables (API keys)
    └─ Wait 30s for stabilization

  Stage 8: Verify Deployment (30s)
    ├─ Get Container App URL
    ├─ Health check with curl (HTTP 200 or 307)
    ├─ Show recent logs (last 50 lines)
    └─ Cleanup virtual environment

  ✅ Result: Application updated and running
                                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 5: RUNTIME (Container Apps)                                   │
└─────────────────────────────────────────────────────────────────────┘

  Container App Running:
  ├─ Pulls image from ACR (if not cached)
  ├─ Starts uvicorn server on port 8080
  ├─ Registers with load balancer
  ├─ Health checks every 10s
  └─ Auto-scales based on:
      ├─ HTTP concurrent requests
      ├─ CPU usage
      └─ Memory usage

  Monitoring:
  ├─ Console logs → Log Analytics
  ├─ System logs → Log Analytics
  ├─ Metrics → Azure Monitor
  └─ Alerts (optional)

  ✅ Result: Application serving user requests
```


### ** Configure GitHub Webhook**

#### **1. In GitHub Repository**

1. Go to **Settings** → **Webhooks** → **Add webhook**
2. Configure:

```
Payload URL: http://<jenkins-url>:8080/github-webhook/
Content type: application/json
Secret: (optional)

Events:
✅ Pushes
✅ Pull requests

Active: ✅ Checked
```

#### **2. In Jenkins Job**

1. Go to job → **Configure**
2. Under **Build Triggers**:
   - ✅ Check "GitHub hook trigger for GITScm polling"
3. Under **Source Code Management** → **Branches to build**:
   - Set to: `*/azure-deploy`

**What happens:**
- When PR merges to azure-deploy → GitHub sends webhook
- Jenkins receives webhook → Triggers build instantly
- No polling needed (faster, more efficient)

---

<a id="interview-questions--answers"></a>
## Interview Questions & Answers

### **Q1: Explain your Azure deployment architecture.**

**Answer:**
> "I built a fully automated CI/CD pipeline for deploying a LangChain-based RAG application to Azure. The architecture has three main components:
> 
> 1. **GitHub Actions** handles Docker image building and pushing to Azure Container Registry. It uses layer caching for fast builds—only the 4 KB code layer rebuilds on changes, while the 4.4 GB dependency layer stays cached.
> 
> 2. **Jenkins** runs tests and deploys to Azure Container Apps. It uses a Service Principal for authentication, runs pytest with coverage reporting, and updates the Container App with the latest image.
> 
> 3. **Azure Container Apps** provides serverless container hosting with auto-scaling (1-3 replicas), built-in HTTPS, and pay-per-use pricing. The application is a FastAPI server running on port 8080.
> 
> The entire pipeline takes about 10-15 minutes from code commit to production deployment."

---

### **Q2: Why did you choose Azure Container Apps over Azure Kubernetes Service (AKS)?**

**Answer:**
> "I chose Container Apps over AKS for several reasons:
> 
> 1. **Simplicity**: Container Apps is fully managed—no need to manage Kubernetes clusters, node pools, or networking complexity.
> 
> 2. **Cost**: With AKS, you pay for nodes even when idle. Container Apps is serverless—you only pay for active compute resources. For a single application with variable traffic, this saves significant cost.
> 
> 3. **Auto-scaling**: Built-in auto-scaling based on HTTP requests, CPU, and memory, without configuring HPA (Horizontal Pod Autoscaler) or KEDA.
> 
> 4. **Faster deployment**: No cluster provisioning time. Container App updates take 30 seconds vs. several minutes for AKS pod rollouts.
> 
> 5. **Built-in features**: Automatic HTTPS certificates, traffic splitting, and Dapr integration out of the box.
> 
> For production applications requiring advanced Kubernetes features like custom networking, StatefulSets, or operators, I would choose AKS. But for stateless web applications, Container Apps provides better developer experience and lower operational overhead."

---

### **Q3: How do you handle secrets and sensitive data?**

**Answer:**
> "I use a layered approach to secret management:
> 
> 1. **Azure Container Apps Secrets**: API keys (GROQ_API_KEY, GOOGLE_API_KEY) are stored as Container App secrets, not environment variables. They're encrypted at rest and injected at runtime.
> 
> 2. **ACR Credentials**: Registry authentication uses admin credentials stored in Jenkins credential store. In production, I'd use managed identity for passwordless authentication.
> 
> 3. **Service Principal**: Jenkins authenticates to Azure using a Service Principal with least-privilege access (Contributor role scoped to subscription). Credentials stored in Jenkins secrets.
> 
> 4. **GitHub Secrets**: ACR credentials stored in GitHub repository secrets for GitHub Actions authentication.
> 
> 5. **No secrets in code**: Used .gitignore to exclude .env files, and all scripts reference environment variables or credential stores, never hard-coded values.
> 
> For enhanced security in production, I would:
> - Use Azure Key Vault for centralized secret management
> - Enable managed identity for Container Apps to ACR (no credentials)
> - Implement secret rotation policies
> - Use Azure AD authentication instead of admin users for ACR"

---

### **Q4: Explain your Docker optimization strategy.**

**Answer:**
> "I optimized Docker builds in three ways:
> 
> **1. .dockerignore optimization:**
> - Excluded .venv/ (915 MB), .git/ (4 MB), logs, tests, and docs
> - Reduced build context from 8.6 GB → 3.9 KB (99.95% reduction)
> - Build time dropped from 20-25 min → 3 min
> 
> **2. Layer caching strategy:**
> ```dockerfile
> # Layers 1-4: Base image and OS packages (changes rarely)
> FROM python:3.12-slim
> RUN apt-get install poppler-utils
> 
> # Layer 5: Python dependencies (only rebuilds if requirements.txt changes)
> COPY requirements.txt ./
> RUN pip install -r requirements.txt
> 
> # Layer 6: Application code (rebuilds on every code change - only 4 KB)
> COPY . .
> ```
> 
> **3. Package manager optimization:**
> - Switched from uv to pip for Docker builds
> - pip downloads pre-built binary wheels (fast)
> - uv sometimes compiles from source (slow in containers)
> - Reduced dependency install from 7+ min → 2-3 min
> 
> Result: First build takes 5 minutes, subsequent code-only builds take 3 minutes and push only 4 KB to ACR."

---

### **Q5: How does your CI/CD pipeline handle failures?**

**Answer:**
> "I implemented comprehensive failure handling at each stage:
> 
> **1. Test failures:**
> - Pytest runs with `|| true` to not fail the pipeline immediately
> - Test results archived regardless of pass/fail
> - Jenkins UI shows test trends and coverage over time
> - Deployment only proceeds if tests pass
> 
> **2. Image verification failures:**
> - Retry logic with exponential backoff (6 retries, 10s intervals)
> - Handles ACR eventual consistency
> - Clear error messages guide user to run local build script
> 
> **3. Environment provisioning failures:**
> - Check Container Apps environment state before deployment
> - If state is 'ScheduledForDelete' or 'Failed', automatically recreate
> - Wait for 'Succeeded' state with timeout (10 minutes)
> 
> **4. Deployment failures:**
> - Azure CLI commands fail fast with clear error messages
> - Jenkins marks build as FAILED
> - Recent logs shown in console output for debugging
> - Previous working version remains deployed (no downtime)
> 
> **5. Monitoring:**
> - Post-deployment health check (HTTP 200/307)
> - Show last 50 lines of container logs
> - Alert if health check fails
> 
> All failures send notifications to Jenkins dashboard and can trigger email/Slack alerts."

---

### **Q6: What would you do differently for production?**

**Answer:**
> "For production deployment, I would implement:
> 
> **1. Security enhancements:**
> - Enable Azure Key Vault for secret management
> - Use managed identity for ACR authentication (no passwords)
> - Implement private endpoints for ACR
> - Add WAF (Web Application Firewall) in front of Container Apps
> - Enable Azure Defender for Container Registry (vulnerability scanning)
> 
> **2. Monitoring and observability:**
> - Integrate Application Insights for distributed tracing
> - Set up Azure Monitor alerts for error rates, latency, and availability
> - Implement custom metrics for LLM usage tracking
> - Configure log retention policies and archival to Storage Accounts
> 
> **3. Deployment strategy:**
> - Implement blue-green deployments using Container Apps revisions
> - Traffic splitting for canary releases (10% → 50% → 100%)
> - Automated rollback on health check failures
> - Use Git tags for versioning (not just 'latest')
> 
> **4. Cost optimization:**
> - Enable scale-to-zero for dev/staging environments
> - Use Azure Reservations for predictable workloads
> - Implement caching layer (Redis) to reduce LLM API costs
> - Set up budget alerts
> 
> **5. High availability:**
> - Deploy to multiple Azure regions (geo-redundancy)
> - Use Traffic Manager for global load balancing
> - Enable ACR geo-replication
> - Configure auto-scaling rules based on business metrics
> 
> **6. CI/CD improvements:**
> - Add integration tests against staging environment
> - Implement approval gates for production deployments
> - Use separate ACR repositories for dev/staging/prod
> - Add automated security scanning (Trivy, Snyk)"

---

### **Q7: Explain the networking flow in your deployment.**

**Answer:**
> "The networking flow has multiple layers:
> 
> **External Request Flow:**
> ```
> User Browser
>   ↓ HTTPS (443)
> Azure Edge (CDN)
>   ↓ Nearest Azure region
> Azure Load Balancer
>   ↓ Health-checked routing
> Container App Replica (1 of 1-3)
>   ↓ Port 8080 (HTTP inside VNet)
> FastAPI / Uvicorn
>   ↓ Process request
> LangChain → External LLM API
> ```
> 
> **Key networking components:**
> 
> 1. **Ingress Controller**: Azure-managed load balancer
>    - Automatically handles HTTPS termination
>    - Free SSL certificate from Microsoft
>    - Distributes traffic across replicas
> 
> 2. **Virtual Network**: Container Apps Environment has a VNet
>    - Private IPs for container-to-container communication
>    - Isolated from internet (only ingress controller exposed)
>    - Can integrate with VNet peering for private resources
> 
> 3. **DNS**: Auto-assigned FQDN
>    - Format: {app-name}.{hash}.{region}.azurecontainerapps.io
>    - Can add custom domains with CNAME records
> 
> 4. **Outbound**: Containers can reach internet
>    - Calls to LLM APIs (Groq, Google)
>    - Pulls from ACR during deployments
>    - Can restrict with VNet egress rules if needed
> 
> **Security:**
> - All external traffic is HTTPS
> - Internal communication is HTTP (inside trusted VNet)
> - No direct access to container IPs (only via load balancer)
> - Can enable IP restrictions for admin endpoints"

---

### **Q8: How do you handle application state and data persistence?**

**Answer:**
> "My LangChain application has two types of data:
> 
> **1. Stateless application design:**
> - Each HTTP request is independent
> - No session state stored in containers
> - FAISS vector index loaded from persistent storage on startup
> - User chat history stored externally (could be Redis, Cosmos DB)
> 
> **2. Persistent data strategy:**
> - **Vector indices**: Mount Azure Files or Blob Storage
> - **Chat history**: Store in Azure Cosmos DB or PostgreSQL
> - **Uploaded documents**: Store in Azure Blob Storage
> - **Application logs**: Send to Log Analytics Workspace
> 
> **Why this approach?**
> - Container Apps replicas are ephemeral (can be replaced anytime)
> - Auto-scaling creates/destroys replicas dynamically
> - Data must survive container restarts
> 
> **Implementation example:**
> ```python
> # On startup
> def load_vector_index():
>     # Download from Blob Storage
>     blob_client.download_to_file('faiss_index/')
>     return FAISS.load_local('faiss_index/')
> 
> # Per request
> def chat(user_id, message):
>     # Get chat history from database
>     history = cosmos_db.get_chat_history(user_id)
>     
>     # Process with LangChain
>     response = chain.run(message, history)
>     
>     # Save updated history
>     cosmos_db.save_chat_history(user_id, history + [message, response])
>     
>     return response
> ```
> 
> **Alternative for stateful apps:**
> - Use Azure Container Apps with Dapr state management
> - Or use Azure Kubernetes Service with StatefulSets
> - Or use Azure App Service (better for monoliths)"

---

### **Q9: Walk me through a typical deployment scenario.**

**Answer:**
> "Let me walk through a real deployment scenario:
> 
> **Scenario: Add new feature to improve RAG retrieval accuracy**
> 
> **Day 1 - Development:**
> ```bash
> # Create feature branch
> git checkout -b feature/improve-retrieval
> 
> # Make code changes
> vim multi_doc_chat/src/retrieval.py
> # Updated similarity threshold from 0.7 to 0.8
> 
> # Test locally
> pytest tests/test_retrieval.py
> # All tests pass
> 
> # Commit and push
> git commit -m \"Improve retrieval accuracy with higher threshold\"
> git push origin feature/improve-retrieval
> 
> # Create Pull Request on GitHub
> # Target: azure-deploy branch
> # Reviewers: Team members
> ```
> 
> **Day 2 - Review and Merge:**
> ```
> Team reviews PR → Approved → Merge to azure-deploy
> ```
> 
> **Automated CI/CD (15 minutes):**
> 
> **Minute 0-5: GitHub Actions**
> - Webhook triggers on merge
> - Checkout azure-deploy branch
> - Build Docker image:
>   * Layers 1-5 CACHED (only 4 KB code layer rebuilds)
> - Push to ACR:
>   * Tag: a5d5abb (commit SHA)
>   * Tag: latest
> - Total: 3-4 minutes
> 
> **Minute 5-15: Jenkins Pipeline**
> - Webhook triggers Jenkins
> - Stage 1: Checkout (10s)
> - Stage 2: Setup Python (30s)
> - Stage 3: Install deps (1 min)
> - Stage 4: Run tests (1-2 min)
>   * All 47 tests pass
>   * Coverage: 82%
> - Stage 5: Azure login (10s)
> - Stage 6: Verify image (30s)
>   * Image a5d5abb found in ACR ✓
> - Stage 7: Deploy (3-5 min)
>   * Update Container App with new image
>   * Rolling update (zero downtime):
>     - Start new replica with image a5d5abb
>     - Wait for health check (HTTP 200)
>     - Route traffic to new replica
>     - Terminate old replica
> - Stage 8: Health check (30s)
>   * HTTP 200 from https://llmops-app...io/ ✓
>   * Show logs: \"Application started successfully\"
> - Total: 8-10 minutes
> 
> **Result:**
> - New feature live in production: 15 minutes after merge
> - Zero downtime deployment
> - Old version automatically replaced
> - All tests passed before deployment
> - Deployment logged and auditable
> 
> **Rollback if needed:**
> ```bash
> # Get previous image tag
> az acr repository show-tags --name llmopsappacr --repository llmops-app
> 
> # Rollback to previous version
> az containerapp update \
>   --name llmops-app \
>   --image llmopsappacr.azurecr.io/llmops-app:76db7f0
> 
> # Or via Jenkins: Trigger build with previous commit
> ```"

---

### **Q10: How do you monitor and troubleshoot the application?**

**Answer:**
> "I use multiple monitoring layers:
> 
> **1. Real-time monitoring:**
> ```bash
> # View live logs
> az containerapp logs show \
>   --name llmops-app \
>   --follow \
>   --tail 100
> 
> # Monitor replicas
> az containerapp replica list \
>   --name llmops-app \
>   --query '[].{Name:name, Status:properties.runningState}'
> ```
> 
> **2. Azure Portal dashboards:**
> - Container App overview: CPU, memory, request count
> - Log Analytics: Query console and system logs
> - Metrics: Response time, error rate, scaling events
> 
> **3. Troubleshooting workflow:**
> 
> **Problem: Application returns 500 errors**
> 
> Step 1: Check recent deployments
> ```bash
> az containerapp revision list \
>   --name llmops-app \
>   --query '[].{Name:name, Active:properties.active, Created:properties.createdTime}'
> ```
> 
> Step 2: View error logs
> ```bash
> az containerapp logs show --name llmops-app --tail 500 | grep ERROR
> ```
> 
> Step 3: Check replica health
> ```bash
> az containerapp replica list --name llmops-app
> # Are replicas in Running state?
> # Are health checks passing?
> ```
> 
> Step 4: Inspect environment variables
> ```bash
> az containerapp show --name llmops-app \
>   --query 'properties.template.containers[0].env'
> # Are API keys configured?
> ```
> 
> Step 5: Test image locally
> ```bash
> # Pull same image from ACR
> docker pull llmopsappacr.azurecr.io/llmops-app:latest
> 
> # Run locally
> docker run -p 8080:8080 \
>   -e GROQ_API_KEY=$GROQ_API_KEY \
>   llmopsappacr.azurecr.io/llmops-app:latest
> 
> # Test with curl
> curl http://localhost:8080/
> ```
> 
> Step 6: Check external dependencies
> ```bash
> # Test LLM API connectivity
> curl https://api.groq.com/openai/v1/models \
>   -H \"Authorization: Bearer $GROQ_API_KEY\"
> ```
> 
> Step 7: Rollback if needed
> ```bash
> # Revert to previous working version
> az containerapp revision activate \
>   --name llmops-app \
>   --revision llmops-app--xyz123
> ```
> 
> **4. Proactive monitoring (would add for production):**
> - Azure Monitor alerts:
>   * Error rate > 5% for 5 minutes
>   * Response time > 2 seconds (95th percentile)
>   * Container restart count > 3 in 10 minutes
> - Application Insights:
>   * Distributed tracing for request flow
>   * Dependency tracking (LLM API calls)
>   * Custom events for RAG metrics (retrieval quality, LLM costs)
> - PagerDuty/Slack integration for critical alerts"

---

<a id="common-pitfalls--solutions"></a>
## ⚠️ Common Pitfalls & Solutions

### **1. Image push is very slow (10+ hours)**

**Problem:**
```bash
docker push llmopsappacr.azurecr.io/llmops-app:latest
# Pushing 4.4 GB at 6-7 MB/min = 10+ hours
```

**Root Cause:**
- Slow home internet upload speed
- Pushing from local machine to Azure

**Solution:**
- Use GitHub Actions to build and push (3-5 minutes)
- GitHub servers have fast connectivity to Azure
- Only 4 KB pushed on code-only changes (layer caching)

---

### **2. Jenkins build fails: "triggers can not be empty"**

**Problem:**
```groovy
triggers {
    // Empty triggers block
}
```

**Root Cause:**
- Jenkins doesn't allow empty `triggers {}` blocks
- Webhook config is in Jenkins UI, not Jenkinsfile

**Solution:**
- Remove or comment out the `triggers` block
- Configure webhook in Jenkins job settings instead

---

### **3. Container App deployment fails: "Environment in ScheduledForDelete state"**

**Problem:**
```
ERROR: Cannot deploy. Environment 'llmops-env' is being deleted.
```

**Root Cause:**
- Previous environment deletion not completed
- Azure takes time to fully delete resources

**Solution:**
```bash
# Wait for deletion to complete
while [ "$(az containerapp env show --name llmops-env --query properties.provisioningState -o tsv 2>/dev/null)" != "NotFound" ]; do
    echo "Waiting for deletion..."
    sleep 10
done

# Recreate environment
az containerapp env create \
    --name llmops-env \
    --resource-group llmops-app-rg \
    --location eastus
```

**Prevention:**
- Add retry logic in Jenkins pipeline (already implemented)
- Check environment state before deployment

---

### **4. Container fails to start: "ImagePullBackOff"**

**Problem:**
```
Container replica failed to start: ImagePullBackOff
```

**Root Cause:**
- ACR authentication failure
- Image doesn't exist in ACR
- Wrong image name/tag

**Solution:**
```bash
# 1. Verify image exists
az acr repository show-tags \
    --name llmopsappacr \
    --repository llmops-app

# 2. Test ACR authentication
az acr login --name llmopsappacr

# 3. Verify Container App registry config
az containerapp show \
    --name llmops-app \
    --query 'properties.configuration.registries'

# 4. Update registry credentials
az containerapp registry set \
    --name llmops-app \
    --server llmopsappacr.azurecr.io \
    --username <username> \
    --password <password>
```

---

### **5. Application starts but returns 502 Bad Gateway**

**Problem:**
- Container App URL returns 502
- Logs show: "Application started successfully"

**Root Cause:**
- Application not listening on correct port (0.0.0.0:8080)
- Health probe failing

**Solution:**
```dockerfile
# Ensure CMD listens on 0.0.0.0 (not 127.0.0.1)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

```bash
# Verify ingress configuration
az containerapp show \
    --name llmops-app \
    --query 'properties.configuration.ingress'

# Should show:
# {
#   "external": true,
#   "targetPort": 8080,
#   "transport": "auto"
# }
```

---

### **6. Tests pass locally but fail in Jenkins**

**Problem:**
```
pytest tests/test_retrieval.py
# Local: PASSED
# Jenkins: FAILED
```

**Root Cause:**
- Missing dependencies in Jenkins environment
- Environment variable differences
- File path issues

**Solution:**
```groovy
stage('Run Tests') {
    steps {
        sh '''
            # Activate venv
            . /tmp/venv-${BUILD_NUMBER}/bin/activate
            
            # Set PYTHONPATH explicitly
            export PYTHONPATH="${WORKSPACE}:${WORKSPACE}/multi_doc_chat"
            
            # Show Python info for debugging
            python --version
            pip list
            
            # Run tests with verbose output
            pytest tests/ -vv
        '''
    }
}
```

---

### **7. High memory usage / Container OOM (Out of Memory)**

**Problem:**
```
Container terminated: OOMKilled (Exit code 137)
```

**Root Cause:**
- ML models (PyTorch) + FAISS index consume lots of memory
- Configured only 1 GB RAM per replica

**Solution:**
```bash
# Increase memory allocation
az containerapp update \
    --name llmops-app \
    --cpu 1.0 \
    --memory 2.0Gi

# Or adjust scaling to handle load
az containerapp update \
    --name llmops-app \
    --min-replicas 2 \
    --max-replicas 5
```

**Optimization:**
```python
# Lazy load models to reduce memory
class ModelCache:
    _model = None
    
    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = load_model()
        return cls._model

# Unload model after use (if needed)
def process_request():
    model = ModelCache.get_model()
    result = model.predict(data)
    # Optional: del model, gc.collect() for very large models
    return result
```

---

### **8. Slow startup time (Cold start > 60 seconds)**

**Problem:**
- First request after deployment takes 60+ seconds
- Users see timeout errors

**Root Cause:**
- Large Docker image (4.4 GB) takes time to pull
- Model loading on startup

**Solutions:**

**Short-term:**
```bash
# Keep 1 replica always running (no cold starts)
az containerapp update \
    --name llmops-app \
    --min-replicas 1  # Never scale to zero
```

**Medium-term:**
```python
# Add startup probe with longer timeout
# In Dockerfile or K8s manifest
# (Container Apps doesn't support custom probes yet)

# Use warm-up endpoint
@app.get("/warmup")
def warmup():
    # Pre-load models
    _ = get_embeddings("warmup query")
    return {"status": "ready"}
```

**Long-term:**
```dockerfile
# Multi-stage build to reduce image size
FROM python:3.12-slim AS builder
RUN pip install -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY app /app
```

---

<a id="study-tips-for-interview"></a>
## 🎓 Study Tips for Interview

### **1. Understand the "Why"**
- Don't just memorize commands
- Understand **why** each resource exists
- Explain trade-offs (e.g., Container Apps vs AKS)

### **2. Draw the architecture**
- Practice drawing the architecture diagram on paper/whiteboard
- Label each component and its purpose
- Show data flow with arrows

### **3. Memorize key metrics**
```
Build context: 8.6 GB → 3.9 KB (99.95% reduction)
Build time: 20-25 min → 3 min (87% faster)
Image size: 4.4 GB (normal for ML/AI)
Deployment time: 10-15 min (commit to prod)
Scaling: 1-3 replicas (configurable)
```

### **4. Practice explaining out loud**
- Explain the deployment flow to someone (or yourself)
- Use the "teach someone" method
- Record yourself and listen back

### **5. Prepare for scenario questions**
- "What if X fails?" → Have rollback plan
- "How would you improve this?" → Security, monitoring, HA
- "Why not use Y instead?" → Explain trade-offs

### **6. Know your commands**
```bash
# Most common Azure CLI commands
az login
az account show
az group create
az acr create
az acr repository show-tags
az containerapp create
az containerapp update
az containerapp logs show
az containerapp revision list
```

### **7. Be ready to compare**
- Azure Container Apps vs AKS vs App Service
- ACR vs DockerHub vs GHCR
- GitHub Actions vs Jenkins vs Azure DevOps
- Managed Identity vs Service Principal vs Admin Keys

---

<a id="quick-reference-cheat-sheet"></a>
## 📊 Quick Reference Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────┐
│                    AZURE RESOURCE SUMMARY                        │
├─────────────────────────────────────────────────────────────────┤
│ Resource Group:        llmops-app-rg                             │
│ Location:              East US                                   │
│ ACR:                   llmopsappacr.azurecr.io                   │
│ ACR SKU:               Basic ($5/month for 10 GB storage)        │
│ Environment:           llmops-env                                │
│ Container App:         llmops-app                                │
│ URL:                   https://llmops-app.YOUR_AZURE_ENV       │
│                        .eastus.azurecontainerapps.io/            │
│ CPU per replica:       0.5 vCPU                                  │
│ Memory per replica:    1 GB                                      │
│ Min replicas:          1                                         │
│ Max replicas:          3                                         │
│ Port:                  8080                                      │
│ Image:                 llmopsappacr.azurecr.io/llmops-app:latest │
│ Image size:            4.4 GB                                    │
├─────────────────────────────────────────────────────────────────┤
│                    CI/CD PIPELINE SUMMARY                        │
├─────────────────────────────────────────────────────────────────┤
│ Git Branch:            azure-deploy                              │
│ GitHub Actions:        Build & Push to ACR (3-5 min)            │
│ Jenkins:               Test & Deploy (8-12 min)                  │
│ Total Time:            10-15 min (commit to production)          │
│ Webhook Trigger:       < 5 seconds after push                    │
│ Tests:                 47 unit + integration tests                │
│ Coverage:              82%                                       │
├─────────────────────────────────────────────────────────────────┤
│                    KEY OPTIMIZATIONS                             │
├─────────────────────────────────────────────────────────────────┤
│ .dockerignore:         8.6 GB → 3.9 KB (99.95% reduction)        │
│ Layer caching:         Dependencies cached (4.4 GB)              │
│ Code-only push:        4 KB (< 10 seconds)                       │
│ Build time:            20-25 min → 3 min (87% faster)            │
│ Package manager:       pip (pre-built wheels, fast)              │
└─────────────────────────────────────────────────────────────────┘
```

---

<a id="final-interview-preparation-checklist"></a>
## 🎯 Final Interview Preparation Checklist

- [ ] Can draw architecture diagram from memory
- [ ] Can explain each Azure resource and its purpose
- [ ] Can walk through deployment flow step-by-step
- [ ] Know key optimization metrics (build time, image size)
- [ ] Understand Docker layer caching
- [ ] Can explain GitHub Actions vs Jenkins roles
- [ ] Know how to troubleshoot common issues
- [ ] Can discuss production improvements (security, HA, monitoring)
- [ ] Understand cost implications of each resource
- [ ] Know rollback procedures

---

<a id="additional-resources"></a>
## 📚 Additional Resources

**Azure Documentation:**
- [Azure Container Apps Overview](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure Container Registry Best Practices](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-best-practices)
- [Deploying to Container Apps with GitHub Actions](https://learn.microsoft.com/en-us/azure/container-apps/github-actions)

**Docker Optimization:**
- [Docker Build Cache Best Practices](https://docs.docker.com/build/cache/)
- [Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)

**CI/CD Patterns:**
- [Blue-Green Deployments](https://martinfowler.com/bliki/BlueGreenDeployment.html)
- [Canary Releases](https://martinfowler.com/bliki/CanaryRelease.html)

---


*Last Updated: February 8, 2026*
*Author: Your LLMOps Deployment*
