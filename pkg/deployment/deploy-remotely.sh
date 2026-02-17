#!/usr/bin/env bash
set -exo pipefail

# Get the root directory of the current git repository and the current commit hash
REPO_ROOT_DIR=$(git rev-parse --show-toplevel)
APP_REVISION=$(git rev-parse --short HEAD)

# Parse arguments: target (host:path or '-') and optional env file path
DEPLOY_TARGET="${1:-}"
ENV_FILE_PATH="${2:-.env}"

if [[ -z "$DEPLOY_TARGET" ]]; then
    echo "Usage: $0 <deploy_target> [env_file_path]"
    exit 1
fi

if [[ "$DEPLOY_TARGET" == "-" ]]; then
    TARGET_DEPLOY_DIR="$REPO_ROOT_DIR"
    REMOTE_CMD_PREFIX=""
elif [[ "$DEPLOY_TARGET" =~ ^[^:]+:.+ ]]; then
    SSH_HOST=$(echo "$DEPLOY_TARGET" | cut -d':' -f1)
    REMOTE_PATH=$(echo "$DEPLOY_TARGET" | cut -d':' -f2-)
    # Ensure remote directory exists
    ssh "$SSH_HOST" "mkdir -p '$REMOTE_PATH'"
    # Sync repository to remote, excluding .git
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='apps/deployment/.tmp' \
        "$REPO_ROOT_DIR/" "$SSH_HOST:$REMOTE_PATH/"
    TARGET_DEPLOY_DIR="$REMOTE_PATH"
    REMOTE_CMD_PREFIX="ssh $SSH_HOST"
else
    echo "Error: <deploy_target> must be '-' or in the format SSH_HOST:PATH"
    exit 1
fi

APP_DEPLOY_DIR="$TARGET_DEPLOY_DIR/pkg/deployment"

# Run deployment commands (locally or remotely)
$REMOTE_CMD_PREFIX bash -c "
    set -euo pipefail
    bash $APP_DEPLOY_DIR/manage.sh ${MANAGE_CMD_OVERRIDE:-up} \
        --env-file '$ENV_FILE_PATH' \
        --revision '$APP_REVISION'
"
