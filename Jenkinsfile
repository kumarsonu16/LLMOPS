/*
 * LLMOps Azure CI/CD Pipeline
 * 
 * IMPORTANT: This pipeline does NOT build Docker images due to ACR Tasks limitations
 * in free trial/student subscriptions.
 * 
 * Workflow Options:
 * 
 * OPTION 1 (Local Build):
 *   1. Build Docker images LOCALLY: ./scripts/azure/build-and-push-docker-image.sh
 *   2. Run this Jenkins pipeline to test and deploy
 * 
 * OPTION 2 (GitHub Actions):
 *   1. Push to azure-deploy branch
 *   2. GitHub Actions builds and pushes to ACR (faster upload from cloud)
 *   3. Run this Jenkins pipeline to test and deploy
 * 
 * Pipeline stages:
 * - Checkout code from Git
 * - Setup Python environment
 * - Install dependencies
 * - Run tests with coverage
 * - Verify Docker image exists in ACR
 * - Deploy to Azure Container Apps
 * - Verify deployment health
 */

pipeline {
    agent any
    
    environment {
        // Python settings
        PYTHON_VERSION = '3.12'
        PYTHONPATH = "${WORKSPACE}:${WORKSPACE}/multi_doc_chat"
        
        // API Keys for testing (optional - set in Jenkins if needed)
        GROQ_API_KEY = "${env.GROQ_API_KEY ?: ''}"
        GOOGLE_API_KEY = "${env.GOOGLE_API_KEY ?: ''}"
        LLM_PROVIDER = "${env.LLM_PROVIDER ?: 'groq'}"
        
        // Azure Container Registry settings
        APP_ACR_NAME = "llmopsappacr"
        APP_ACR_SERVER = "${APP_ACR_NAME}.azurecr.io"
        IMAGE_NAME = "llmops-app"
        
        // Azure Container Apps settings
        APP_RESOURCE_GROUP = "llmops-app-rg"
        CONTAINER_APP_NAME = "llmops-app"
        CONTAINER_APP_ENV = "llmops-env"
        APP_LOCATION = "eastus"
        
        // NOTE: Azure credentials are loaded dynamically in deploy stages
        // to allow test-only runs without requiring credentials
    }
    
    // triggers {
    //     // GitHub webhook trigger is configured in Jenkins job settings (Build Triggers)
    //     // Not needed in Jenkinsfile - triggers block must contain actual trigger definitions
    //     // For polling: pollSCM('H/2 * * * *')
    // }
    
    // Note: GitHub webhook trigger is configured in Jenkins job settings (not here).
    // Branch filtering is done in the pipeline job configuration (*/azure-deploy for Azure branch).
    
    stages {
        stage('Checkout') {
            steps {
                echo '📦 Checking out code from repository...'
                checkout scm
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                echo '🐍 Setting up Python virtual environment...'
                sh '''
                    set -e
                    
                    # Install uv (fast Python package/dependency manager)
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    UV="$HOME/.local/bin/uv"

                    # Avoid Azure Files limitations by storing uv data outside Jenkins HOME
                    export UV_PYTHON_INSTALL_DIR=/tmp/uv/python
                    export XDG_DATA_HOME=/tmp/.local/share
                    export XDG_CACHE_HOME=/tmp/.cache
                    
                    # Ensure exact Python version matches project (e.g., 3.12)
                    "$UV" python install ${PYTHON_VERSION}
                    
                    # Create venv with the requested Python version
                    "$UV" venv --python ${PYTHON_VERSION} /tmp/venv-${BUILD_NUMBER}
                    
                    # Show versions for debugging
                    /tmp/venv-${BUILD_NUMBER}/bin/python --version
                    "$UV" --version
                '''
            }
        }
        
        stage('Install Dependencies') {
            steps {
                echo '📥 Installing project dependencies...'
                sh '''
                    set -e
                    VENV_PY="/tmp/venv-${BUILD_NUMBER}/bin/python"
                    UV="$HOME/.local/bin/uv"

                    # Ensure uv also uses temp storage during dependency resolution
                    export XDG_DATA_HOME=/tmp/.local/share
                    export XDG_CACHE_HOME=/tmp/.cache
                    
                    # Create a sanitized requirements file removing local-only and OS-specific deps
                    SAN_REQ=$(mktemp)
                    cat requirements.txt \
                      | sed -E '/^[[:space:]]*llmops-series(==.*)?[[:space:]]*$/d' \
                      | sed -E '/^[[:space:]]*pywin32(==.*)?[[:space:]]*$/d' \
                      > "$SAN_REQ"
                    
                    # Install third-party dependencies with uv into the venv interpreter
                    "$UV" pip install --python "$VENV_PY" -r "$SAN_REQ"
                    
                    # Ensure test tooling is available
                    "$UV" pip install --python "$VENV_PY" pytest pytest-cov
                    
                    # Skip editable install; rely on PYTHONPATH set at pipeline level
                    echo "Using PYTHONPATH=${PYTHONPATH} for local package imports"
                '''
            }
        }
        
        stage('Run Tests') {
            steps {
                echo '🧪 Running pytest tests...'
                sh '''
                    set -e
                    . /tmp/venv-${BUILD_NUMBER}/bin/activate
                    mkdir -p test-results
                    pytest tests/ \
                        --verbose \
                        --junit-xml=test-results/results.xml \
                        --cov=multi_doc_chat \
                        --cov-report=xml:coverage.xml \
                        --cov-report=html:htmlcov \
                        --cov-report=term \
                        || true
                '''
                
                // Archive test results and coverage reports immediately
                echo '📊 Archiving test results...'
                junit allowEmptyResults: true, testResults: 'test-results/*.xml'
                archiveArtifacts artifacts: 'coverage.xml,htmlcov/**,test-results/**/*.xml', allowEmptyArchive: true
            }
        }
        
        stage('Login to Azure') {
            steps {
                echo '🔐 Logging into Azure...'
                withCredentials([
                    string(credentialsId: 'azure-client-id', variable: 'AZURE_CLIENT_ID'),
                    string(credentialsId: 'azure-client-secret', variable: 'AZURE_CLIENT_SECRET'),
                    string(credentialsId: 'azure-tenant-id', variable: 'AZURE_TENANT_ID'),
                    string(credentialsId: 'azure-subscription-id', variable: 'AZURE_SUBSCRIPTION_ID')
                ]) {
                    sh '''
                        az login --service-principal \
                            -u ${AZURE_CLIENT_ID} \
                            -p ${AZURE_CLIENT_SECRET} \
                            --tenant ${AZURE_TENANT_ID}
                        
                        az account set --subscription ${AZURE_SUBSCRIPTION_ID}
                        az account show
                    '''
                }
            }
        }
        
        stage('Verify Docker Image Exists') {
            steps {
                echo '🔍 Verifying Docker image exists in ACR...'
                withCredentials([
                    string(credentialsId: 'azure-client-id', variable: 'AZURE_CLIENT_ID'),
                    string(credentialsId: 'azure-client-secret', variable: 'AZURE_CLIENT_SECRET'),
                    string(credentialsId: 'azure-tenant-id', variable: 'AZURE_TENANT_ID'),
                    string(credentialsId: 'azure-subscription-id', variable: 'AZURE_SUBSCRIPTION_ID')
                ]) {
                    sh '''
                        # Login to Azure
                        az login --service-principal \
                            -u ${AZURE_CLIENT_ID} \
                            -p ${AZURE_CLIENT_SECRET} \
                            --tenant ${AZURE_TENANT_ID}
                        az account set --subscription ${AZURE_SUBSCRIPTION_ID}
                    
                    # Retry parameters for eventual consistency on ACR/role assignments
                    MAX_RETRIES=6
                    SLEEP_SECS=10
                    ATTEMPT=1

                    echo "Checking for repository '${IMAGE_NAME}' in ACR '${APP_ACR_NAME}' with up to ${MAX_RETRIES} retries..."
                    until az acr repository show --name ${APP_ACR_NAME} --repository ${IMAGE_NAME} &>/dev/null; do
                        if [ $ATTEMPT -ge $MAX_RETRIES ]; then
                            echo "❌ ERROR: Image repository '${IMAGE_NAME}' not found in ACR after ${MAX_RETRIES} attempts."
                            echo ""
                            echo "Please build and push the Docker image locally first:"
                            echo "  chmod +x build-and-push-docker-image.sh"
                            echo "  ./build-and-push-docker-image.sh"
                            echo ""
                            exit 1
                        fi
                        echo "Attempt ${ATTEMPT}/${MAX_RETRIES}: repository not found. Waiting ${SLEEP_SECS}s and retrying..."
                        sleep ${SLEEP_SECS}
                        ATTEMPT=$((ATTEMPT+1))
                    done

                    echo "Repository found. Checking for 'latest' tag with retries..."
                    ATTEMPT=1
                    until az acr repository show-tags --name ${APP_ACR_NAME} --repository ${IMAGE_NAME} --output tsv | grep -q "^latest$"; do
                        if [ $ATTEMPT -ge $MAX_RETRIES ]; then
                            echo "❌ ERROR: No 'latest' tag found for image '${IMAGE_NAME}' after ${MAX_RETRIES} attempts."
                            echo ""
                            echo "Please build and push the Docker image locally:"
                            echo "  ./build-and-push-docker-image.sh"
                            echo ""
                            exit 1
                        fi
                        echo "Attempt ${ATTEMPT}/${MAX_RETRIES}: 'latest' tag not found. Waiting ${SLEEP_SECS}s and retrying..."
                        sleep ${SLEEP_SECS}
                        ATTEMPT=$((ATTEMPT+1))
                    done

                    echo "✅ Image '${IMAGE_NAME}:latest' found in ACR"
                    echo ""
                    echo "Available tags:"
                    az acr repository show-tags \
                        --name ${APP_ACR_NAME} \
                        --repository ${IMAGE_NAME} \
                        --output table
                    '''
                }
            }
        }
        
        stage('Deploy to Azure Container Apps') {
            steps {
                echo '🚀 Deploying to Azure Container Apps...'
                withCredentials([
                    string(credentialsId: 'azure-client-id', variable: 'AZURE_CLIENT_ID'),
                    string(credentialsId: 'azure-client-secret', variable: 'AZURE_CLIENT_SECRET'),
                    string(credentialsId: 'azure-tenant-id', variable: 'AZURE_TENANT_ID'),
                    string(credentialsId: 'azure-subscription-id', variable: 'AZURE_SUBSCRIPTION_ID'),
                    string(credentialsId: 'acr-username', variable: 'ACR_USERNAME'),
                    string(credentialsId: 'acr-password', variable: 'ACR_PASSWORD')
                ]) {
                    sh '''
                        # Login to Azure
                        az login --service-principal \
                            -u ${AZURE_CLIENT_ID} \
                            -p ${AZURE_CLIENT_SECRET} \
                            --tenant ${AZURE_TENANT_ID}
                        az account set --subscription ${AZURE_SUBSCRIPTION_ID}
                    
                    # Ensure containerapp extension is available
                    az extension show -n containerapp >/dev/null 2>&1 || az extension add -n containerapp

                    # Ensure resource group exists
                    if [ "$(az group exists --name ${APP_RESOURCE_GROUP})" != "true" ]; then
                        echo "Resource group ${APP_RESOURCE_GROUP} not found. Creating..."
                        az group create --name ${APP_RESOURCE_GROUP} --location ${APP_LOCATION} >/dev/null
                    fi

                    # Ensure Container Apps environment exists and is healthy
                    get_env_state() {
                        az containerapp env show \
                            --name ${CONTAINER_APP_ENV} \
                            --resource-group ${APP_RESOURCE_GROUP} \
                            --query properties.provisioningState -o tsv 2>/dev/null || echo "NotFound"
                    }

                    recreate_env() {
                        echo "Recreating Container Apps environment ${CONTAINER_APP_ENV}..."
                        az containerapp env delete \
                            --name ${CONTAINER_APP_ENV} \
                            --resource-group ${APP_RESOURCE_GROUP} \
                            --yes --no-wait || true
                        # Wait until it's fully deleted
                        MAX_DELETE_RETRIES=60
                        ATT=1
                        until [ "$(get_env_state)" = "NotFound" ]; do
                            if [ $ATT -ge $MAX_DELETE_RETRIES ]; then
                                echo "❌ ERROR: Environment ${CONTAINER_APP_ENV} did not delete in time."
                                exit 1
                            fi
                            echo "Waiting for ${CONTAINER_APP_ENV} deletion... (${ATT}/${MAX_DELETE_RETRIES})"
                            sleep 10
                            ATT=$((ATT+1))
                        done
                        # Create fresh env
                        az containerapp env create \
                            --name ${CONTAINER_APP_ENV} \
                            --resource-group ${APP_RESOURCE_GROUP} \
                            --location ${APP_LOCATION}
                    }

                    STATE=$(get_env_state)
                    if [ "$STATE" = "NotFound" ]; then
                        echo "Container Apps environment ${CONTAINER_APP_ENV} not found. Creating..."
                        az containerapp env create \
                            --name ${CONTAINER_APP_ENV} \
                            --resource-group ${APP_RESOURCE_GROUP} \
                            --location ${APP_LOCATION}
                        STATE="$(get_env_state)"
                    fi

                    if [ "$STATE" = "ScheduledForDelete" ] || [ "$STATE" = "Failed" ]; then
                        echo "Environment state is '$STATE'. Will recreate."
                        recreate_env
                        STATE="$(get_env_state)"
                    fi

                    echo "Waiting for environment ${CONTAINER_APP_ENV} to be 'Succeeded'... (current: $STATE)"
                    MAX_RETRIES=60
                    SLEEP_SECS=10
                    ATTEMPT=1
                    while [ "$(get_env_state)" != "Succeeded" ]; do
                        if [ $ATTEMPT -ge $MAX_RETRIES ]; then
                            echo "❌ ERROR: Environment ${CONTAINER_APP_ENV} is not ready after $((MAX_RETRIES*SLEEP_SECS))s."
                            az containerapp env show --name ${CONTAINER_APP_ENV} --resource-group ${APP_RESOURCE_GROUP} -o yaml || true
                            exit 1
                        fi
                        CURR=$(get_env_state)
                        echo "Attempt ${ATTEMPT}/${MAX_RETRIES}: provisioningState=${CURR}. Waiting ${SLEEP_SECS}s..."
                        sleep ${SLEEP_SECS}
                        ATTEMPT=$((ATTEMPT+1))
                        # If it flips to ScheduledForDelete or Failed mid-wait, recreate
                        if [ "$CURR" = "ScheduledForDelete" ] || [ "$CURR" = "Failed" ]; then
                            recreate_env
                        fi
                    done

                    # Create the Container App if it does not exist; otherwise update
                    if az containerapp show --name ${CONTAINER_APP_NAME} --resource-group ${APP_RESOURCE_GROUP} >/dev/null 2>&1; then
                        echo "Container App exists. Updating image..."
                        az containerapp update \
                            --name ${CONTAINER_APP_NAME} \
                            --resource-group ${APP_RESOURCE_GROUP} \
                            --image ${APP_ACR_SERVER}/${IMAGE_NAME}:latest
                    else
                        echo "Container App not found. Creating it now..."
                        az containerapp create \
                            --name ${CONTAINER_APP_NAME} \
                            --resource-group ${APP_RESOURCE_GROUP} \
                            --environment ${CONTAINER_APP_ENV} \
                            --image ${APP_ACR_SERVER}/${IMAGE_NAME}:latest \
                            --ingress external \
                            --target-port 8080 \
                            --min-replicas 1 \
                            --max-replicas 3 \
                            --registry-server ${APP_ACR_SERVER} \
                            --registry-username ${ACR_USERNAME} \
                            --registry-password ${ACR_PASSWORD} \
                            --env-vars \
                                GROQ_API_KEY="${GROQ_API_KEY}" \
                                GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
                                LLM_PROVIDER="${LLM_PROVIDER}"
                    fi
                    
                    echo "Waiting for deployment to stabilize..."
                    sleep 30
                    '''
                }
            }
        }
        
        stage('Verify Deployment') {
            steps {
                echo '✅ Verifying deployment...'
                withCredentials([
                    string(credentialsId: 'azure-client-id', variable: 'AZURE_CLIENT_ID'),
                    string(credentialsId: 'azure-client-secret', variable: 'AZURE_CLIENT_SECRET'),
                    string(credentialsId: 'azure-tenant-id', variable: 'AZURE_TENANT_ID'),
                    string(credentialsId: 'azure-subscription-id', variable: 'AZURE_SUBSCRIPTION_ID')
                ]) {
                    sh '''
                        # Login to Azure
                        az login --service-principal \
                            -u ${AZURE_CLIENT_ID} \
                            -p ${AZURE_CLIENT_SECRET} \
                            --tenant ${AZURE_TENANT_ID}
                        az account set --subscription ${AZURE_SUBSCRIPTION_ID}
                    
                    # Ensure containerapp extension is available
                    az extension show -n containerapp >/dev/null 2>&1 || az extension add -n containerapp
                    
                    # Get app URL
                    APP_URL=$(az containerapp show \
                        --name ${CONTAINER_APP_NAME} \
                        --resource-group ${APP_RESOURCE_GROUP} \
                        --query properties.configuration.ingress.fqdn -o tsv)
                    
                    echo "Application URL: https://${APP_URL}"
                    
                    # Health check
                    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://${APP_URL} || echo "000")
                    
                    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "307" ]; then
                        echo "✅ Deployment successful! App is responding."
                    else
                        echo "⚠️  Warning: App returned HTTP $HTTP_CODE"
                    fi
                    
                    # Show recent logs
                    echo "Recent logs:"
                    az containerapp logs show \
                        --name ${CONTAINER_APP_NAME} \
                        --resource-group ${APP_RESOURCE_GROUP} \
                        --tail 50 || true
                    
                    # Cleanup virtual environment
                    echo "🧹 Cleaning up virtual environment..."
                    rm -rf /tmp/venv-${BUILD_NUMBER} || true
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline completed successfully! 🎉'
            echo '📊 Test results and coverage reports have been archived.'
        }
        
        failure {
            echo '❌ Pipeline failed!'
            echo 'Check the console output above for error details.'
        }
        
        always {
            echo '🧹 Pipeline execution finished.'
            echo '💡 Virtual environment /tmp/venv-${BUILD_NUMBER} will be cleaned up automatically.'
        }
    }
}