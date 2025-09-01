#!/bin/zsh

export APPIUM_HOST=${APPIUM_HOST:-127.0.0.1}
export APPIUM_PORT=${APPIUM_PORT:-4723}
export PLATFORM_NAME=${PLATFORM_NAME:-iOS}
export AUTOMATION_NAME=${AUTOMATION_NAME:-XCUITest}
export WDA_LOCAL_PORT=${WDA_LOCAL_PORT:-8100}
export DEFAULT_LAUNCH_TIMEOUT=${DEFAULT_LAUNCH_TIMEOUT:-30000}
export NEW_COMMAND_TIMEOUT=${NEW_COMMAND_TIMEOUT:-360}
export SERVER_HOST=${SERVER_HOST:-127.0.0.1}
export SERVER_PORT=${SERVER_PORT:-8765}
export SERVER_PATH=${SERVER_PATH:-/mcp}
export DEVICE_UDID=${DEVICE_UDID:-""}
export DEFAULT_BUNDLE_ID=${DEFAULT_BUNDLE_ID:-com.apple.Preferences}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

cleanup() {
    echo "[*] cleaning up processes..."
    if [[ -n $APPIUM_PID ]]; then
        kill -9 $APPIUM_PID 2>/dev/null || true
    fi
    if [[ -n $PYTHON_PID ]]; then
        kill -9 $PYTHON_PID 2>/dev/null || true
    fi
}

trap cleanup EXIT

echo "[*] starting Appium on $APPIUM_HOST:$APPIUM_PORT..."
appium --address $APPIUM_HOST --port $APPIUM_PORT \
    --log-level info \
    --relaxed-security \
    --use-drivers xcuitest \
    &
APPIUM_PID=$!

sleep 5

echo "[*] starting MCP server..."
./.venv/bin/python main.py \
    --udid $DEVICE_UDID \
    --host $SERVER_HOST \
    --port $SERVER_PORT \
    &
PYTHON_PID=$!

echo "[*] all services started successfully"
echo "    Appium PID: $APPIUM_PID"
echo "    Python server PID: $PYTHON_PID"

wait

