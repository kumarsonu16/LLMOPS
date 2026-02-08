# 🚀 Complete AWS Deployment Guide - MultiDocChat

**From Zero to Production: Step-by-Step Guide for GitHub Actions + AWS ECS Fargate**

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Resources Setup](#aws-resources-setup)
3. [GitHub Secrets Configuration](#github-secrets-configuration)
4. [Project Files Setup](#project-files-setup)
5. [Testing & Deployment](#testing--deployment)
6. [Troubleshooting](#troubleshooting)
7. [Cost Estimation](#cost-estimation)

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Actions                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   CI Tests   │ -> │ Build Docker │ -> │ Deploy to    │     │
│  │   (ci.yml)   │    │  Push to ECR │    │     ECS      │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud                                │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │     ECR      │ -> │  ECS Fargate │ <- │    Secrets   │    │
│  │ (Docker Repo)│    │  (Containers)│    │   Manager    │    │
│  └──────────────┘    └──────────────┘    └──────────────┘    │
│         ↑                   ↑                                  │
│  ┌──────────────┐    ┌──────────────┐                        │
│  │ Application  │    │     ALB      │ <- User Traffic        │
│  │ Load Balancer│    │ (Port 8080)  │                        │
│  └──────────────┘    └──────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Prerequisites {#prerequisites}

### ✅ Required Accounts
- [ ] **AWS Account** (with admin/billing access)
- [ ] **GitHub Account** (repository owner access)
- [ ] **Domain** (optional, for custom DNS)

### ✅ Required Tools (Local Development)
- [ ] **AWS CLI** installed and configured
  ```bash
  # Install (macOS)
  brew install awscli
  
  # Verify
  aws --version
  ```

- [ ] **Docker Desktop** running
  ```bash
  # Verify
  docker --version
  ```

- [ ] **Git** configured
  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "your@email.com"
  ```

---

## 2. AWS Resources Setup {#aws-resources-setup}

### 📌 Setup Order Overview

Follow these steps **in exact order** to avoid confusion:

```
Step 2.1  → IAM User (for GitHub Actions)
Step 2.2  → Task Execution Role (for ECS tasks)
Step 2.3  → ECR Repository (Docker image storage)
Step 2.4  → Secrets Manager (API keys)
Step 2.5  → CloudWatch Log Group (application logs) - OPTIONAL
Step 2.6  → VPC/Subnets (network foundation)
Step 2.7  → Security Group (firewall rules)
Step 2.8  → ECS Cluster ⭐ (container platform)
Step 2.9  → Target Group (for load balancing)
Step 2.10 → Application Load Balancer (traffic routing)
Step 2.11 → Task Definition (container blueprint)
Step 2.12 → ECS Service (run containers)
```

---

### Step 2.1: Create IAM User for GitHub Actions

**Purpose:** Secure credentials for GitHub to deploy to AWS

1. **Login to AWS Console** → Navigate to **IAM**

2. **Create User**
   - Click **Users** → **Add users**
   - Username: `github-actions-llmops`
   - Access type: ☑️ **Access key - Programmatic access**
   - Click **Next**

3. **Set Permissions**
   - Click **Attach existing policies directly**
   - Search and select these policies:
     - ☑️ `AmazonEC2ContainerRegistryFullAccess`
     - ☑️ `AmazonECS_FullAccess`
     - ☑️ `AmazonS3FullAccess`
     - ☑️ `CloudWatchLogsFullAccess`
     - ☑️ `AmazonS3FullAccess`
     - ☑️ `SecretsManagerReadWrite`

     Added below In-line policies:
     - AllowECSLogs

     ```
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Statement1",
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "*"
                }
            ]
        }


        ```

     - AllowSecretsAccess


     ```
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Statement1",
                    "Effect": "Allow",
                    "Action": "secretsmanager:GetSecretValue",
                    "Resource": "arn:aws:secretsmanager:us-east-1:341252054363:secret:llmops_prod-3fs6sC*"
                }
            ]
        }

     ```

   - Click **Next: Tags** → **Next: Review** → **Create user**

4. **Save Credentials** (IMPORTANT!)
   ```
   Access Key ID: AKIA****************
   Secret Access Key: wJal********************************
   ```
   ⚠️ **Save these immediately! You won't see them again.**

### Step 2.2: Create ECS Task Execution Role

**Purpose:** Allows ECS tasks to pull Docker images and access secrets

1. **Navigate to IAM** → **Roles** → **Create role**

    Role name: ecsTaskExecutionRole
    Permissions policies:
    - AmazonECSTaskExecutionRolePolicy - (AWS managed)
    - CloudWatchLogsFullAccess - (AWS managed)
    - ecs-exec-secrets-llmops  - (Customer inline)

        ```
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "secretsmanager:GetSecretValue",
                            "secretsmanager:DescribeSecret"
                        ],
                        "Resource": "arn:aws:secretsmanager:us-east-1:341252054363:secret:llmops_prod-*"
                    }
                ]
            }
        ```


2. **Select Trusted Entity**
   - Trusted entity type: **AWS service**
   - Use case: **Elastic Container Service** → **Elastic Container Service Task**
   - Click **Next**

3. **Add Permissions**
   - Search and attach these policies:
     - ☑️ `AmazonECSTaskExecutionRolePolicy`
     - ☑️ `CloudWatchLogsFullAccess` (or create custom with limited access)
   - Click **Next**

4. **Name Role**
   - Role name: `ecsTaskExecutionRole`
   - Click **Create role**

5. **Copy ARN** (you'll need this later)
   ```
   arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole
   ```

### Step 2.3: Create ECR Repository

**Purpose:** Docker image storage

1. **Navigate to ECR** → **Repositories** → **Create repository**

2. **Configure Repository**
   - Visibility: **Private**
   - Repository name: `llmops`
   - Tag immutability: **Disabled** (for easier updates)
   - Scan on push: ☑️ **Enabled** (security scanning)
   - Encryption: **AES-256** (default)
   - Click **Create repository**

3. **Copy Repository URI**
   ```
   ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llmops
   ```

### Step 2.4: Create Secrets Manager Secret

**Purpose:** Store API keys securely

1. **Navigate to Secrets Manager** → **Store a new secret**

2. **Choose Secret Type**
   - Secret type: **Other type of secret**
   - Key/value pairs: Click **+ Add row** for each:
   
   | Key | Value |
   |-----|-------|
   | `GROQ_API_KEY` | `gsk_...` (your actual key) |
   | `GOOGLE_API_KEY` | `AIza...` (your actual key) |
   | `LLM_PROVIDER` | `groq` |
   | `LANGCHAIN_PROJECT` | `LLMOPS` |
   | `LANGCHAIN_TRACING_V2` | `true` |
   | `LANGCHAIN_ENDPOINT` | `https://api.smith.langchain.com` |
   | `LANGCHAIN_API_KEY` | `lsv2_pt_...` (your actual key) |

3. **Configure Secret**
   - Secret name: `llmops_prod`
   - Description: `API keys for MultiDocChat production`
   - Encryption key: **aws/secretsmanager** (default)
   - Click **Next**

4. **Configure Rotation** (Optional)
   - Disable automatic rotation for now
   - Click **Next** → **Store**

5. **Copy Secret ARN**
   ```
   arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:llmops_prod-XXXXX
   ```

---

### Step 2.5: Create CloudWatch Log Group (OPTIONAL - Can Auto-Create)

**Purpose:** Store container logs for debugging and monitoring

**⚠️ IMPORTANT: Two Options**

**Option A: Auto-Create (Recommended - Easier)** ✅

You don't need to manually create the log group! When you set `"awslogs-create-group": "true"` in your task definition (Step 2.11), ECS will automatically create the log group `/ecs/llmopstdlive` when the first task starts.

**Prerequisites for auto-creation:**
- Task Execution Role must have `logs:CreateLogGroup` permission (already included in Step 2.2)
- That's it! ECS handles everything else.

**Skip to Step 2.6 if using auto-creation.** ⬇️

---

**Option B: Manual Creation (For Production - Better Control)**

If you want to pre-create the log group with specific settings:

1. **Navigate to CloudWatch** → **Log groups** → **Create log group**

2. **Configure Log Group**
   - Log group name: `/ecs/llmopstdlive`
   - Retention setting: 
     - **Never expire** (default, but costs more)
     - **7 days** (recommended for development)
     - **30 days** (recommended for production)
     - **1 year** (for compliance/audit)
   - KMS encryption: **Disabled** (or enable with KMS key for security)
   - Click **Create**

3. **Copy Log Group Name**
   ```
   /ecs/llmopstdlive
   ```

4. **Verify Permissions**
   - Ensure Task Execution Role (from Step 2.2) has these permissions:
     - `logs:CreateLogStream`
     - `logs:PutLogEvents`
   - (Already included if you followed Step 2.2 ✅)

**Benefits of manual creation:**
- ✅ Set retention period (save costs)
- ✅ Enable KMS encryption upfront
- ✅ Configure log group before deployment
- ✅ Easier to monitor in CloudWatch console

**When to use manual creation:**
- Production environments
- Need specific retention policies
- Require encryption with custom KMS keys
- Want to set up alarms before deployment

---

### Step 2.6: Create VPC and Subnets (if not using default)

**Purpose:** Network infrastructure for ECS

**Option A: Use Default VPC** (Easier - Recommended for testing)
1. Navigate to **VPC** → Note down:
   - Default VPC ID: `vpc-xxxxx`
   - Default Subnets (at least 2): `subnet-xxxxx`, `subnet-yyyyy`
   - Default Security Group: `sg-xxxxx`

**Option B: Create New VPC** (Production - More control)
1. **Navigate to VPC** → **Create VPC**
   - Name: `llmops-vpc`
   - IPv4 CIDR: `10.0.0.0/16`
   - Click **Create VPC**

2. **Create Subnets** (Need at least 2 in different AZs)
   - Subnet 1:
     - Name: `llmops-subnet-public-1a`
     - AZ: `us-east-1a`
     - CIDR: `10.0.1.0/24`
   - Subnet 2:
     - Name: `llmops-subnet-public-1b`
     - AZ: `us-east-1b`
     - CIDR: `10.0.2.0/24`

3. **Create Internet Gateway**
   - Name: `llmops-igw`
   - Attach to VPC: `llmops-vpc`

4. **Create Route Table**
   - Name: `llmops-public-rt`
   - Add route: `0.0.0.0/0` → Internet Gateway
   - Associate with both subnets

---

### Step 2.7: Create Security Group

**Purpose:** Control inbound/outbound traffic

1. **Navigate to EC2** → **Security Groups** → **Create security group**

2. **Basic Details**
   - Name: `llmops-ecs-sg`
   - Description: `Security group for MultiDocChat ECS tasks`
   - VPC: Select your VPC

3. **Inbound Rules**
   - Click **Add rule**:
     - Type: **Custom TCP**
     - Port: `8080`
     - Source: `0.0.0.0/0` (or restrict to ALB security group)
     - Description: `Allow HTTP traffic to app`

4. **Outbound Rules**
   - Keep default: **All traffic** to `0.0.0.0/0`

5. **Create Security Group** → Copy **Security Group ID**: `sg-xxxxx`

---

### Step 2.8: Create ECS Cluster ⭐

**Purpose:** Container orchestration platform - **Create this before ALB!**

**Why now?** You need the cluster name when setting up the service later. It's better to create it early in the process.

1. **Navigate to ECS** → **Clusters** → **Create cluster**

2. **Cluster Configuration**
   - Cluster name: `llmopscluster`
   - Infrastructure: ☑️ **AWS Fargate (serverless)**
   - Monitoring: ☑️ **Use Container Insights** (optional, for monitoring)
   - Click **Create**

3. **Wait for Creation** (takes ~30 seconds)
   - Status should show: **ACTIVE**
   - Copy Cluster Name: `llmopscluster`

✅ **Cluster created! This is your container platform foundation.**

---

### Step 2.9: Create Target Group (for Load Balancer)

**Purpose:** Define health checks and routing for containers

**Why before ALB?** The ALB needs a target group to route traffic to.

1. **Navigate to EC2** → **Target Groups** → **Create target group**

2. **Basic Configuration**
   - Target type: **IP addresses** (for Fargate)
   - Target group name: `llmops-tg`
   - Protocol: **HTTP**
   - Port: `8080`
   - VPC: Select your VPC

3. **Health Checks**
   - Health check protocol: **HTTP**
   - Health check path: `/health`
   - Advanced health check settings:
     - Healthy threshold: `2`
     - Unhealthy threshold: `2`
     - Timeout: `5` seconds
     - Interval: `30` seconds
     - Success codes: `200`

4. **Create Target Group**
   - Click **Next** (don't register targets yet - ECS will do this)
   - Click **Create target group**

5. **Copy Target Group ARN** (you'll need this)
   ```
   arn:aws:elasticloadbalancing:us-east-1:ACCOUNT_ID:targetgroup/llmops-tg/xxxxx
   ```

✅ **Target Group created! Now you can create the ALB.**

---

### Step 2.10: Create Application Load Balancer

**Purpose:** Route traffic to ECS tasks

1. **Navigate to EC2** → **Load Balancers** → **Create Load Balancer**

2. **Choose Load Balancer Type**
   - Select **Application Load Balancer**

3. **Configure Load Balancer**
   - Name: `llmops-alb`
   - Scheme: **Internet-facing**
   - IP address type: **IPv4**

4. **Network Mapping**
   - VPC: Select your VPC
   - Mappings: Select at least 2 availability zones
   - Subnets: Select your public subnets

5. **Security Groups**
   - Create or select security group for ALB:
     - Name: `llmops-alb-sg`
     - Inbound: Port **80** (HTTP) from `0.0.0.0/0`
     - Inbound: Port **443** (HTTPS) from `0.0.0.0/0` (if using SSL)
     - Outbound: All traffic to `0.0.0.0/0`

6. **Listeners and Routing**
   - Protocol: **HTTP**
   - Port: **80**
   - Default action: **Forward to** → Select `llmops-tg` (created in Step 2.8)

7. **Create Load Balancer**
   - Review settings
   - Click **Create load balancer**
   - Wait for provisioning (~2-3 minutes)

8. **Copy DNS Name** (this is your application URL)
   ```
   llmops-alb-1234567890.us-east-1.elb.amazonaws.com
   ```

✅ **Load Balancer created! Traffic will now route to your containers.**

---

### Step 2.11: Register Task Definition

**Purpose:** Define container specifications (blueprint for your app)

**Option A: Using AWS Console** (Easier for beginners)

1. **Navigate to ECS** → **Task Definitions** → **Create new task definition**

2. **Configure Task Definition**
   - Task definition family: `llmopstd`
   - Launch type: **AWS Fargate**
   - Operating system: **Linux/X86_64**
   - Task role: **None** (for now)
   - Task execution role: Select `ecsTaskExecutionRole` (from Step 2.2)

3. **Task Size**
   - CPU: **1 vCPU** (1024)
   - Memory: **8 GB** (8192)

4. **Container Definition**
   - Click **Add container**
   - Container name: `llmops-container`
   - Image URI: `YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llmops:latest`
   - Port mappings: Container port **8080**, Protocol **TCP**

5. **Environment Variables**
   - Click **Add environment variable**:
     - `ENV` = `production`
     - `PORT` = `8080`

6. **Secrets** (from AWS Secrets Manager)
   - Click **Add secret**:
     - For each key, select:
       - Environment variable name: `GROQ_API_KEY`
       - Value from: **AWS Secrets Manager**
       - Secret: `llmops_prod`
       - Specific keys: `GROQ_API_KEY`
     - Repeat for: `GOOGLE_API_KEY`, `LLM_PROVIDER`, etc.

7. **Logging**
   - Log driver: **awslogs**
   - awslogs-group: `/ecs/llmopstdlive`
   - awslogs-region: `us-east-1`
   - awslogs-stream-prefix: `ecs`
   - ☑️ **Auto-create log group** ← This will auto-create the CloudWatch log group!

8. **Create Task Definition**

✅ **Task Definition registered!**

**💡 Note:** If you enabled auto-create log group, CloudWatch Logs will be created automatically when the first task runs. No manual step needed!

---

**Option B: Using JSON File** (What you have in your repo)

You already have `task_defination.json` in your repo! Just update these values:

```json
{
  "family": "llmopstd",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "8192",
  "containerDefinitions": [{
    "name": "llmops-container",
    "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llmops:latest",
    "portMappings": [{
      "containerPort": 8080,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "ENV", "value": "production"},
      {"name": "PORT", "value": "8080"}
    ],
    "secrets": [
      {
        "name": "GROQ_API_KEY",
        "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:llmops_prod-XXXXX:GROQ_API_KEY::"
      },
      {
        "name": "GOOGLE_API_KEY",
        "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:llmops_prod-XXXXX:GOOGLE_API_KEY::"
      }
      // ... add other secrets
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/llmopstdlive",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs",
        "awslogs-create-group": "true"
      }
    }
  }]
}
```

**Then register it via AWS CLI:**
```bash
aws ecs register-task-definition \
  --cli-input-json file://.github/workflows/task_defination.json
```

✅ **Task Definition registered!**

**💡 Note:** The `"awslogs-create-group": "true"` setting in your JSON will automatically create `/ecs/llmopstdlive` log group when the first task runs!

---

### Step 2.12: Create ECS Service (FINAL STEP!)

**Purpose:** Run and maintain tasks continuously

**Prerequisites Check:**
- ✅ ECS Cluster created (`llmopscluster` - Step 2.8)
- ✅ Task Definition registered (`llmopstd` - Step 2.11)
- ✅ Target Group created (`llmops-tg` - Step 2.9)
- ✅ ALB created (`llmops-alb` - Step 2.10)
- ✅ Security Group configured (`llmops-ecs-sg` - Step 2.7)
- ✅ CloudWatch Log Group (auto-created by task definition)

**Now create the service:**

1. **Navigate to ECS** → **Clusters** → Click `llmopscluster`

2. **Create Service**
   - Click **Services** tab → **Create** button
   
3. **Environment**
   - Compute options: **Launch type**
   - Launch type: **FARGATE**

4. **Deployment Configuration**
   - Application type: **Service**
   - Family: `llmopstd`
   - Revision: **Latest**
   - Service name: `llmops-service`
   - Desired tasks: `1` (start with 1, can scale later)

5. **Networking**
   - VPC: Select your VPC
   - Subnets: Select your subnets (at least 2)
   - Security group: Select `llmops-ecs-sg`
   - Public IP: ☑️ **Enabled** (if using public subnets)

6. **Load Balancing**
   - Load balancer type: **Application Load Balancer**
   - Load balancer: Select `llmops-alb`
   - Listener: Select existing **80:HTTP**
   - Target group: Select `llmops-tg`
   - Health check grace period: `60` seconds

7. **Auto Scaling** (Optional)
   - For now: **No auto scaling**
   - (Can add later based on CPU/Memory)

8. **Review and Create Service**
   - Review all settings
   - Click **Create**
   - Wait for deployment (takes 2-3 minutes)

9. **Verify Service is Running**
   - Go to **Services** tab
   - Service name: `llmops-service`
   - Status should be: **ACTIVE**
   - Desired tasks: **1**
   - Running tasks: **1** (wait for this to show up)
   - Click on service → **Tasks** tab → Task status should be **RUNNING**

✅ **ECS Service created and running! Your application is now live!**

---

## 📝 Quick Summary: Complete Setup Order

**Complete Sequential Order:**

```
FOUNDATION SETUP:
Step 2.1  → IAM User for GitHub Actions
Step 2.2  → Task Execution Role
Step 2.3  → ECR Repository
Step 2.4  → Secrets Manager
Step 2.5  → CloudWatch Log Group (OPTIONAL - can auto-create)
Step 2.6  → VPC/Subnets
Step 2.7  → Security Group

CONTAINER PLATFORM:
Step 2.8  → ECS Cluster ⭐ (create the platform)

LOAD BALANCER SETUP:
Step 2.9  → Target Group (define routing rules)
Step 2.10 → Application Load Balancer (route traffic)

RUN CONTAINERS:
Step 2.11 → Task Definition (container blueprint + auto-create logs)
Step 2.12 → ECS Service (deploy & run containers)

          🎉 APPLICATION RUNNING!
          📊 CloudWatch Logs automatically created!
```

**Key Dependencies:**
- **Service** needs: Cluster + Task Definition + Target Group + Security Group
- **Task Definition** needs: Execution Role + ECR URI + Secrets ARN
- **ALB** needs: Target Group + VPC + Subnets
- **Target Group** needs: VPC
- **CloudWatch Logs**: Auto-created by task definition (if enabled)

**💡 CloudWatch Log Creation:**
- **Automatic**: Task definition with `"awslogs-create-group": "true"` creates logs automatically
- **Manual**: Optional Step 2.5 for production with retention policies
- **Permissions**: Task Execution Role needs `logs:CreateLogGroup` (already included)

---

## 3. GitHub Secrets Configuration {#github-secrets-configuration}

### Step 3.1: Add Repository Secrets

1. **Go to GitHub Repository** → **Settings** → **Secrets and variables** → **Actions**

2. **Click "New repository secret"** and add each:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ACCESS_KEY_ID` | `AKIA...` | IAM user access key from Step 2.1 |
| `AWS_SECRET_ACCESS_KEY` | `wJal...` | IAM user secret key from Step 2.1 |
| `AWS_ACCOUNT_ID` | `123456789012` | Your 12-digit AWS account ID |
| `ECR_REPOSITORY` | `llmops` | ECR repository name |
| `ECS_CLUSTER` | `llmopscluster` | ECS cluster name |
| `ECS_SERVICE` | `llmops-service` | ECS service name |

**How to find AWS Account ID:**
```bash
aws sts get-caller-identity --query Account --output text
```

---

## 4. Project Files Setup {#project-files-setup}

### Step 4.1: Update Task Definition

**File:** `.github/workflows/task_defination.json`

Replace placeholders:
- `YOUR_ACCOUNT_ID` → Your actual AWS account ID
- `arn:aws:secretsmanager:...` → Your actual secret ARN from Step 2.4

### Step 4.2: Update GitHub Workflow

**File:** `.github/workflows/aws.yml`

Update environment variables (already correct in your file):
```yaml
env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: llmops
  ECS_SERVICE: llmops-service
  ECS_CLUSTER: llmopscluster
  ECS_TASK_DEFINITION: .github/workflows/task_defination.json
  CONTAINER_NAME: llmops-container
```

### Step 4.3: Verify CI Workflow

**File:** `.github/workflows/ci.yml`

Ensure tests run before deployment (already set up ✅)

### Step 4.4: Update .env (Local Only - DO NOT COMMIT)

Ensure `.env` has **no quotes**:
```bash
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AIza...
LLM_PROVIDER=groq
```

Add to `.gitignore` (should already be there):
```
.env
*.log
__pycache__/
```

---

## 5. Testing & Deployment {#testing--deployment}

### Step 5.1: Test Locally

```bash
# 1. Test with Python directly
python main.py
# Access: http://localhost:8080

# 2. Test with Docker
docker build -t llmops .
docker run -p 8080:8080 --env-file .env llmops
# Access: http://localhost:8080

# 3. Run tests
pytest
```

### Step 5.2: Initial Manual Deployment (Optional)

**Purpose:** Verify AWS setup before automation

```bash
# 1. Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# 2. Build and tag
docker build -t llmops .
docker tag llmops:latest \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llmops:latest

# 3. Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llmops:latest

# 4. Update ECS service (force new deployment)
aws ecs update-service \
  --cluster llmopscluster \
  --service llmops-service \
  --force-new-deployment
```

### Step 5.3: Deploy via GitHub Actions

1. **Commit and Push to Main**
   ```bash
   git add .
   git commit -m "Setup CI/CD pipeline"
   git push origin main
   ```

2. **Watch GitHub Actions**
   - Go to **GitHub** → **Actions** tab
   - Watch workflow execution:
     - ✅ CI (runs tests)
     - ✅ Build & Push (builds Docker image)
     - ✅ Deploy (deploys to ECS)

3. **Check ECS Deployment**
   - Go to **AWS ECS** → **Clusters** → `llmopscluster`
   - Click **Services** → `llmops-service`
   - Check **Tasks** tab → Should show **RUNNING**

4. **Access Application**
   ```
   http://llmops-alb-1234567890.us-east-1.elb.amazonaws.com
   ```

### Step 5.4: Verify Deployment

```bash
# Check health endpoint
curl http://YOUR_ALB_DNS/health

# Should return:
# {"status": "healthy"}

# Check application
open http://YOUR_ALB_DNS
```

---

## 6. Troubleshooting {#troubleshooting}

### Issue: CloudWatch Log Group Not Created

**Symptoms:**
- Task starts but you can't find logs in CloudWatch
- Error: "Log group does not exist"

**Solution:**

1. **Verify Task Definition has correct logging configuration:**
   ```bash
   aws ecs describe-task-definition --task-definition llmopstd
   ```
   
   Check for:
   ```json
   "logConfiguration": {
     "logDriver": "awslogs",
     "options": {
       "awslogs-create-group": "true",  // ← Must be "true" (string)
       "awslogs-group": "/ecs/llmopstdlive",
       "awslogs-region": "us-east-1",
       "awslogs-stream-prefix": "ecs"
     }
   }
   ```

2. **Check Task Execution Role permissions:**
   ```bash
   aws iam get-role-policy --role-name ecsTaskExecutionRole --policy-name AllowECSLogs
   ```
   
   Should include:
   - `logs:CreateLogGroup`
   - `logs:CreateLogStream`
   - `logs:PutLogEvents`

3. **Manually create log group if auto-create fails:**
   ```bash
   aws logs create-log-group --log-group-name /ecs/llmopstdlive
   
   # Set retention (optional)
   aws logs put-retention-policy \
     --log-group-name /ecs/llmopstdlive \
     --retention-in-days 7
   ```

4. **Verify log group exists:**
   ```bash
   aws logs describe-log-groups --log-group-name-prefix /ecs/llmopstdlive
   ```

---

### Issue: Task Fails to Start

**Check CloudWatch Logs:**
```bash
# View real-time logs
aws logs tail /ecs/llmopstdlive --follow

# View logs from specific time
aws logs tail /ecs/llmopstdlive --since 1h

# Filter logs
aws logs tail /ecs/llmopstdlive --filter-pattern "ERROR"
```

**Common Issues:**
1. **Missing secrets** → Verify Secrets Manager ARN in task definition
2. **ECR access denied** → Check task execution role has ECR permissions
3. **Health check failing** → Verify app listens on port 8080, `/health` endpoint works
4. **No logs appearing** → Check CloudWatch log group exists (see issue above)

### Issue: GitHub Actions Fails

**Check workflow logs:**
- GitHub → Actions → Click failed workflow → View logs

**Common Issues:**
1. **AWS credentials invalid** → Re-check GitHub secrets
2. **ECR push denied** → Verify IAM user has ECR permissions
3. **Task definition not found** → Check file path in workflow

### Issue: Cannot Access Application

**Check:**
1. **Security Group** → Allows inbound traffic on port 8080
2. **ALB Health Check** → Target group shows healthy targets
3. **Public IP** → ECS task has public IP assigned
4. **DNS** → ALB DNS resolves correctly

```bash
# Test ALB connectivity
curl -I http://YOUR_ALB_DNS

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn YOUR_TARGET_GROUP_ARN
```

### Issue: High Costs

**Monitor:**
```bash
# Check running tasks
aws ecs list-tasks --cluster llmopscluster

# Stop service if needed
aws ecs update-service \
  --cluster llmopscluster \
  --service llmops-service \
  --desired-count 0
```

---

## 7. Cost Estimation {#cost-estimation}

### Monthly Cost Breakdown (us-east-1)

| Service | Specification | Estimated Cost |
|---------|--------------|----------------|
| **ECS Fargate** | 1 task, 1 vCPU, 8GB RAM, 24/7 | ~$50/month |
| **ALB** | 1 ALB, low traffic | ~$20/month |
| **ECR** | Storage < 10GB | ~$1/month |
| **Secrets Manager** | 1 secret | ~$0.40/month |
| **Data Transfer** | < 10GB/month | ~$1/month |
| **CloudWatch Logs** | < 5GB/month | ~$2/month |
| **Total** | | **~$75/month** |

### Cost Optimization Tips:
- Use **ECS Fargate Spot** (70% savings, may interrupt)
- Reduce task count during off-hours
- Use smaller instance (0.5 vCPU, 2GB) for testing
- Set up CloudWatch alarms for unexpected spikes
- Delete unused ECR images
- **Set CloudWatch Logs retention to 7 days** (saves ~80% on log costs)

---

## 8. Checklist Summary {#checklist}

### AWS Setup ✅
- [ ] IAM user created with access keys (Step 2.1)
- [ ] ECS Task Execution Role created (Step 2.2)
- [ ] ECR repository created (Step 2.3)
- [ ] Secrets Manager secret created (Step 2.4)
- [ ] CloudWatch Log Group created OR auto-create enabled (Step 2.5)
- [ ] VPC/Subnets configured (Step 2.6)
- [ ] Security Group configured (Step 2.7)
- [ ] ECS Cluster created (Step 2.8)
- [ ] Target Group created (Step 2.9)
- [ ] Application Load Balancer created (Step 2.10)
- [ ] Task Definition registered (Step 2.11)
- [ ] ECS Service created (Step 2.12)

### CloudWatch Logs Verification ✅
- [ ] Log group `/ecs/llmopstdlive` exists (check AWS Console)
- [ ] Task Execution Role has CloudWatch Logs permissions
- [ ] Logs appearing in CloudWatch after task starts
- [ ] Retention policy set (optional, saves costs)

### GitHub Setup ✅
- [ ] Repository created/cloned
- [ ] GitHub secrets added
- [ ] Workflow files committed
- [ ] Task definition updated with real ARNs

### Testing ✅
- [ ] Local tests pass
- [ ] Docker builds successfully
- [ ] CI workflow passes
- [ ] Manual deployment works
- [ ] Automated deployment works
- [ ] Application accessible via ALB
- [ ] CloudWatch Logs showing container output

---

## 9. Quick Reference Commands {#quick-reference}

### Deployment Commands
```bash
# Force new deployment
aws ecs update-service \
  --cluster llmopscluster \
  --service llmops-service \
  --force-new-deployment

# Scale service
aws ecs update-service \
  --cluster llmopscluster \
  --service llmops-service \
  --desired-count 2

# View logs
aws logs tail /ecs/llmopstdlive --follow

# List tasks
aws ecs list-tasks --cluster llmopscluster

# Describe task
aws ecs describe-tasks \
  --cluster llmopscluster \
  --tasks TASK_ID
```

### Cleanup Commands (Teardown)
```bash
# 1. Delete ECS Service
aws ecs delete-service \
  --cluster llmopscluster \
  --service llmops-service \
  --force

# 2. Delete ECS Cluster
aws ecs delete-cluster --cluster llmopscluster

# 3. Delete ALB
aws elbv2 delete-load-balancer --load-balancer-arn YOUR_ALB_ARN

# 4. Delete Target Group
aws elbv2 delete-target-group --target-group-arn YOUR_TG_ARN

# 5. Delete ECR images
aws ecr batch-delete-image \
  --repository-name llmops \
  --image-ids imageTag=latest

# 6. Delete ECR repository
aws ecr delete-repository --repository-name llmops --force

# 7. Delete CloudWatch log group
aws logs delete-log-group --log-group-name /ecs/llmopstdlive
```

---

## 10. Next Steps & Enhancements

### Immediate
- [ ] Set up custom domain (Route 53 + ACM certificate)
- [ ] Enable HTTPS on ALB
- [ ] Set up auto-scaling (CPU/Memory based)
- [ ] Configure CloudWatch alarms

### Medium Term
- [ ] Add RDS database for persistent chat history
- [ ] Add S3 bucket for document storage
- [ ] Implement user authentication (Cognito)
- [ ] Add Redis for caching

### Advanced
- [ ] Multi-region deployment
- [ ] Blue-green deployments
- [ ] Canary deployments
- [ ] CI/CD for staging environment

---

## 📚 Additional Resources

- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**🎉 Congratulations!** You now have a complete CI/CD pipeline deploying your MultiDocChat application to AWS ECS Fargate!

**Questions?** Check the troubleshooting section or AWS CloudWatch logs.

---

*Document Version: 1.0*  
*Last Updated: January 13, 2026*  
*Author: Your AI Assistant 🤖*
