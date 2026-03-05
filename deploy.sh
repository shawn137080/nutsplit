#!/bin/bash

# Auto Split Deploy Script
# This script pushes local changes to GitHub and pulls them on the Hostinger server.

SERVER_IP="72.61.74.110"
SERVER_USER="root"
REMOTE_DIR="/opt/open_split"

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Staging all local changes..."
    git add .
    
    echo "Committing changes..."
    # You can provide a custom commit message as an argument, or default to "Automated deploy update"
    COMMIT_MSG=${1:-"Update for deployment"}
    git commit -m "$COMMIT_MSG"
else
    echo "No local changes to commit. Proceeding to deploy..."
fi

echo "Pushing code to GitHub..."
git push origin main
if [ $? -ne 0 ]; then
    echo "❌ Failed to push to GitHub. Aborting deploy."
    exit 1
fi
echo "✅ Code pushed to GitHub successfully."

echo "Connecting to Hostinger server to pull code and restart Docker container..."
# Using SSH to run commands directly on the server
ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} << EOF
    cd ${REMOTE_DIR} || exit
    echo "Pulling latest code from GitHub..."
    git pull origin main
    
    echo "Rebuilding and restarting Docker containers..."
    docker compose up -d --build
    
    echo "Deployment complete! Checking bot logs..."
    docker compose logs bot --tail=10
EOF

echo "🎉 Auto Split is successfully updated and running on Hostinger!"
