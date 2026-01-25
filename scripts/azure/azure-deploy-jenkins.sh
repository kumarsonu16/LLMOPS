#!/bin/bash

# -e → exit on error
# -u → error if variable is undefined
set -e
set -u

# Configuration
RESOURCE_GROUP="llmops-jenkins-rg"
LOCATION="eastus"
UNIQUE_SUFFIX=$RANDOM
STORAGE_ACCOUNT="llmopsjenkinsstore${UNIQUE_SUFFIX}"
FILE_SHARE_NAME="jenkins-data"
ACR_NAME="llmopsjenkinsacr${UNIQUE_SUFFIX}"
CONTAINER_NAME="jenkins-llmops"
DNS_NAME="jenkins-llmops-${RANDOM}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Azure Jenkins Deployment Script ===${NC}\n"

# Step 1: Create Resource Group
echo -e "${GREEN}Step 1: Creating Resource Group...${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION

# Step 2: Create Storage Account
echo -e "${GREEN}Step 2: Creating Storage Account...${NC}"
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Step 3: Get Storage Key
echo -e "${GREEN}Step 3: Getting Storage Key...${NC}"
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --query '[0].value' -o tsv)

# Step 4: Create File Share
echo -e "${GREEN}Step 4: Creating File Share...${NC}"
az storage share create \
  --name $FILE_SHARE_NAME \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --quota 10
 
# Step 5: Create Container Registry
echo -e "${GREEN}Step 5: Creating Azure Container Registry...${NC}"
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic

az acr update --name $ACR_NAME --admin-enabled true

# Step 6: Get ACR Credentials
echo -e "${GREEN}Step 6: Getting ACR Credentials...${NC}"
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Step 7: Build and Push Image
echo -e "${GREEN}Step 7: Building and Pushing Jenkins Image...${NC}"
az acr login --name $ACR_NAME
docker build --platform linux/amd64 -f Dockerfile.jenkins -t $ACR_NAME.azurecr.io/jenkins-python:latest .
docker push $ACR_NAME.azurecr.io/jenkins-python:latest

# Step 8: Deploy Container
echo -e "${GREEN}Step 8: Deploying Jenkins Container...${NC}"
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image $ACR_NAME.azurecr.io/jenkins-python:latest \
  --os-type Linux \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label $DNS_NAME \
  --ports 8080 50000 \
  --cpu 2 \
  --memory 4 \
  --azure-file-volume-account-name $STORAGE_ACCOUNT \
  --azure-file-volume-account-key $STORAGE_KEY \
  --azure-file-volume-share-name $FILE_SHARE_NAME \
  --azure-file-volume-mount-path /var/jenkins_home \
  --environment-variables \
    GROQ_API_KEY="${GROQ_API_KEY}" \
    GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
    LLM_PROVIDER=groq

# Get Jenkins URL
JENKINS_URL=$(az container show \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --query ipAddress.fqdn -o tsv)

echo -e "\n${GREEN}=== Deployment Complete! ===${NC}"
echo -e "Jenkins URL: ${BLUE}http://${JENKINS_URL}:8080${NC}"
echo -e "\nWait 2-3 minutes for Jenkins to start, then run:"
echo -e "${BLUE}az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command \"/bin/bash -c 'cat /var/jenkins_home/secrets/initialAdminPassword'\"${NC}"