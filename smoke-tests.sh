#!/bin/bash
# FreeMarket Smoke Tests Script
# Usage: bash smoke-tests.sh <API_URL>
# Example: bash smoke-tests.sh http://localhost:8000

API_URL="${1:-http://localhost:8000}"
FAILED=0
PASSED=0

echo "=========================================="
echo "FreeMarket Smoke Tests"
echo "=========================================="
echo "Target API: $API_URL"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
run_test() {
    local test_name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=$5

    echo -n "Testing $test_name... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$endpoint")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $http_code)"
        echo "  Response: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Test 1: Health check
echo "--- Basic Endpoints ---"
run_test "Health Check" "GET" "/health" "" "200"

# Test 2: Create user
echo ""
echo "--- User Endpoints ---"
USERNAME="testuser_$(date +%s)"
USER_DATA="{\"username\":\"$USERNAME\",\"contact\":\"test@example.com\"}"
run_test "Create User" "POST" "/users/" "$USER_DATA" "200"

# Extract user info (for follow-up tests)
USERS_RESPONSE=$(curl -s -X GET "$API_URL/users/$USERNAME")
echo ""
echo "Created user response: $USERS_RESPONSE"

# Test 3: Get user by username
echo ""
run_test "Get User by Username" "GET" "/users/$USERNAME" "" "200"

# Test 4: Create profile
echo ""
echo "--- Profile Endpoints ---"
PROFILE_DATA="{\"username\":\"$USERNAME\",\"name\":\"Test User\",\"category\":\"Electronics\",\"description\":\"Test profile\",\"location\":\"Almaty\"}"
run_test "Create Profile" "POST" "/profiles/" "$PROFILE_DATA" "200"

# Test 5: Get profile
echo ""
run_test "Get Profile" "GET" "/profiles/$USERNAME" "" "200"

# Test 6: List categories
echo ""
echo "--- Marketplace Endpoints ---"
run_test "Get Categories" "GET" "/categories" "" "200"

# Test 7: List market listings
echo ""
run_test "List Market Listings" "GET" "/market-listings/" "" "200"

# Test 8: List wants
echo ""
run_test "List Wants" "GET" "/market-listings/wants/all" "" "200"

# Test 9: List offers
echo ""
run_test "List Offers" "GET" "/market-listings/offers/all" "" "200"

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
