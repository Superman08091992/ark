#!/bin/bash
# ARK Federation Multi-Instance Test Script
# Simulates local, cloud, and Pi instances for testing federation

set -e

echo "🧪 ARK Federation Multi-Instance Test"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
BACKEND_PORT_1=8001
BACKEND_PORT_2=8002
BACKEND_PORT_3=8003
FED_PORT_1=9001
FED_PORT_2=9002
FED_PORT_3=9003

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up test instances...${NC}"
    pkill -f "intelligent-backend.cjs.*PORT=$BACKEND_PORT_1" 2>/dev/null || true
    pkill -f "intelligent-backend.cjs.*PORT=$BACKEND_PORT_2" 2>/dev/null || true
    pkill -f "intelligent-backend.cjs.*PORT=$BACKEND_PORT_3" 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Set trap for cleanup on exit
trap cleanup EXIT INT TERM

# Function to start instance
start_instance() {
    local instance_type=$1
    local backend_port=$2
    local fed_port=$3
    local log_file=$4
    
    echo -e "${BLUE}Starting $instance_type instance...${NC}"
    echo "  Backend port: $backend_port"
    echo "  Federation port: $fed_port"
    
    ARK_INSTANCE_TYPE=$instance_type \
    PORT=$backend_port \
    FEDERATION_PORT=$fed_port \
    FEDERATION_MODE=p2p \
    FEDERATION_AUTO_SYNC=false \
    node intelligent-backend.cjs > "$log_file" 2>&1 &
    
    local pid=$!
    echo "  PID: $pid"
    
    # Wait for backend to start
    for i in {1..10}; do
        if curl -s "http://localhost:$backend_port/api/agents" > /dev/null 2>&1; then
            echo -e "${GREEN}  ✅ $instance_type instance started${NC}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${YELLOW}  ⚠️  Warning: $instance_type instance may not have started properly${NC}"
    return 1
}

# Function to make API request
api_request() {
    local port=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    if [ -z "$data" ]; then
        curl -s -X "$method" "http://localhost:$port$endpoint"
    else
        curl -s -X "$method" "http://localhost:$port$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data"
    fi
}

echo -e "${BLUE}Step 1: Starting three ARK instances${NC}"
echo "  Instance 1: local (ports $BACKEND_PORT_1, $FED_PORT_1)"
echo "  Instance 2: cloud (ports $BACKEND_PORT_2, $FED_PORT_2)"
echo "  Instance 3: pi (ports $BACKEND_PORT_3, $FED_PORT_3)"
echo ""

start_instance "local" $BACKEND_PORT_1 $FED_PORT_1 "test-instance-local.log"
start_instance "cloud" $BACKEND_PORT_2 $FED_PORT_2 "test-instance-cloud.log"
start_instance "pi" $BACKEND_PORT_3 $FED_PORT_3 "test-instance-pi.log"

sleep 3

echo ""
echo -e "${BLUE}Step 2: Starting federation servers${NC}"

# Start federation on instance 1
echo -e "${YELLOW}Starting federation on local instance...${NC}"
result=$(api_request $BACKEND_PORT_1 POST "/api/federation/start")
echo "$result" | jq '.' 2>/dev/null || echo "$result"

# Start federation on instance 2
echo -e "${YELLOW}Starting federation on cloud instance...${NC}"
result=$(api_request $BACKEND_PORT_2 POST "/api/federation/start")
echo "$result" | jq '.' 2>/dev/null || echo "$result"

# Start federation on instance 3
echo -e "${YELLOW}Starting federation on pi instance...${NC}"
result=$(api_request $BACKEND_PORT_3 POST "/api/federation/start")
echo "$result" | jq '.' 2>/dev/null || echo "$result"

sleep 2

echo ""
echo -e "${BLUE}Step 3: Checking federation status${NC}"

echo -e "${YELLOW}Local instance status:${NC}"
api_request $BACKEND_PORT_1 GET "/api/federation/status" | jq '.info | {instanceName, instanceType, listenPort}' 2>/dev/null

echo -e "${YELLOW}Cloud instance status:${NC}"
api_request $BACKEND_PORT_2 GET "/api/federation/status" | jq '.info | {instanceName, instanceType, listenPort}' 2>/dev/null

echo -e "${YELLOW}Pi instance status:${NC}"
api_request $BACKEND_PORT_3 GET "/api/federation/status" | jq '.info | {instanceName, instanceType, listenPort}' 2>/dev/null

echo ""
echo -e "${BLUE}Step 4: Configuring peer connections${NC}"

# Instance 1 (local) connects to instance 2 (cloud)
echo -e "${YELLOW}Local → Cloud peer connection...${NC}"
result=$(api_request $BACKEND_PORT_1 POST "/api/federation/peers/add" "{\"peerUrl\":\"http://localhost:$FED_PORT_2\"}")
echo "$result" | jq '.' 2>/dev/null || echo "$result"

# Instance 1 (local) connects to instance 3 (pi)
echo -e "${YELLOW}Local → Pi peer connection...${NC}"
result=$(api_request $BACKEND_PORT_1 POST "/api/federation/peers/add" "{\"peerUrl\":\"http://localhost:$FED_PORT_3\"}")
echo "$result" | jq '.' 2>/dev/null || echo "$result"

# Instance 2 (cloud) connects to instance 1 (local)
echo -e "${YELLOW}Cloud → Local peer connection...${NC}"
result=$(api_request $BACKEND_PORT_2 POST "/api/federation/peers/add" "{\"peerUrl\":\"http://localhost:$FED_PORT_1\"}")
echo "$result" | jq '.' 2>/dev/null || echo "$result"

# Instance 2 (cloud) connects to instance 3 (pi)
echo -e "${YELLOW}Cloud → Pi peer connection...${NC}"
result=$(api_request $BACKEND_PORT_2 POST "/api/federation/peers/add" "{\"peerUrl\":\"http://localhost:$FED_PORT_3\"}")
echo "$result" | jq '.' 2>/dev/null || echo "$result"

# Instance 3 (pi) connects to instance 1 (local) and 2 (cloud)
echo -e "${YELLOW}Pi → Local peer connection...${NC}"
result=$(api_request $BACKEND_PORT_3 POST "/api/federation/peers/add" "{\"peerUrl\":\"http://localhost:$FED_PORT_1\"}")
echo "$result" | jq '.' 2>/dev/null || echo "$result"

echo -e "${YELLOW}Pi → Cloud peer connection...${NC}"
result=$(api_request $BACKEND_PORT_3 POST "/api/federation/peers/add" "{\"peerUrl\":\"http://localhost:$FED_PORT_2\"}")
echo "$result" | jq '.' 2>/dev/null || echo "$result"

echo ""
echo -e "${BLUE}Step 5: Listing configured peers${NC}"

echo -e "${YELLOW}Local instance peers:${NC}"
api_request $BACKEND_PORT_1 GET "/api/federation/peers" | jq '.' 2>/dev/null

echo -e "${YELLOW}Cloud instance peers:${NC}"
api_request $BACKEND_PORT_2 GET "/api/federation/peers" | jq '.' 2>/dev/null

echo -e "${YELLOW}Pi instance peers:${NC}"
api_request $BACKEND_PORT_3 GET "/api/federation/peers" | jq '.' 2>/dev/null

echo ""
echo -e "${BLUE}Step 6: Testing synchronization${NC}"

echo -e "${YELLOW}Triggering sync from local instance...${NC}"
result=$(api_request $BACKEND_PORT_1 POST "/api/federation/sync")
echo "$result" | jq '.' 2>/dev/null || echo "$result"

sleep 2

echo -e "${YELLOW}Triggering sync from cloud instance...${NC}"
result=$(api_request $BACKEND_PORT_2 POST "/api/federation/sync")
echo "$result" | jq '.' 2>/dev/null || echo "$result"

sleep 2

echo ""
echo -e "${BLUE}Step 7: Checking final statistics${NC}"

echo -e "${YELLOW}Local instance final stats:${NC}"
api_request $BACKEND_PORT_1 GET "/api/federation/status" | jq '.stats' 2>/dev/null

echo -e "${YELLOW}Cloud instance final stats:${NC}"
api_request $BACKEND_PORT_2 GET "/api/federation/status" | jq '.stats' 2>/dev/null

echo -e "${YELLOW}Pi instance final stats:${NC}"
api_request $BACKEND_PORT_3 GET "/api/federation/status" | jq '.stats' 2>/dev/null

echo ""
echo -e "${GREEN}✅ Federation test complete!${NC}"
echo ""
echo "Log files:"
echo "  - test-instance-local.log"
echo "  - test-instance-cloud.log"
echo "  - test-instance-pi.log"
echo ""
echo "Instances will be cleaned up on script exit."
echo "Press Ctrl+C to stop all instances and exit."
echo ""

# Keep script running
read -p "Press Enter to stop all instances and exit..."
