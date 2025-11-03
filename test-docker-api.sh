#!/bin/bash

# Quick API testing script for Docker deployment
BASE_URL="http://localhost:8001"

echo "🧪 Testing FreeMarket API endpoints..."
echo "====================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_endpoint() {
    local url="$1"
    local description="$2"

    echo -n "Testing $description... "
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

# Test basic endpoints
echo "📋 Basic Health Checks:"
test_endpoint "$BASE_URL/health" "Health check"

# Test categories API
echo ""
echo "🏷️  Categories API:"
test_endpoint "$BASE_URL/v1/categories" "All categories"
test_endpoint "$BASE_URL/v1/categories/permanent" "Permanent categories"
test_endpoint "$BASE_URL/v1/categories/temporary" "Temporary categories"

# Test auth endpoints (should return 405 Method Not Allowed for GET, but service should be up)
echo ""
echo "🔐 Auth API (service availability):"
if curl -s "$BASE_URL/auth/login" | grep -q "Method Not Allowed"; then
    echo -e "Auth service: ${GREEN}✅ AVAILABLE${NC}"
else
    echo -e "Auth service: ${RED}❌ UNAVAILABLE${NC}"
fi

# Test user endpoints (should require auth)
echo ""
echo "👤 User API (auth required):"
if curl -s "$BASE_URL/user/cabinet" | grep -q "Not authenticated"; then
    echo -e "User endpoints: ${GREEN}✅ PROTECTED${NC}"
else
    echo -e "User endpoints: ${YELLOW}⚠️  RESPONSE UNEXPECTED${NC}"
fi

echo ""
echo "🎯 Testing user registration flow..."

# Test user registration
echo -n "Registering test user... "
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User",
    "city": "Алматы"
  }')

if echo "$REGISTER_RESPONSE" | grep -q "id"; then
    echo -e "${GREEN}✅ SUCCESS${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    echo "Response: $REGISTER_RESPONSE"
fi

# Test user login
echo -n "Logging in test user... "
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "identifier": "test@example.com",
    "password": "testpass123"
  }')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ SUCCESS${NC}"

    # Test authenticated endpoint
    echo -n "Testing authenticated cabinet access... "
    CABINET_RESPONSE=$(curl -s -X GET "$BASE_URL/user/cabinet" \
      -b cookies.txt)

    if echo "$CABINET_RESPONSE" | grep -q "profile"; then
        echo -e "${GREEN}✅ SUCCESS${NC}"
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "Cabinet response: $CABINET_RESPONSE"
    fi

else
    echo -e "${RED}❌ FAILED${NC}"
    echo "Login response: $LOGIN_RESPONSE"
fi

# Clean up
rm -f cookies.txt

echo ""
echo "📊 Test Summary:"
echo "==============="
echo "✅ If all tests show green checkmarks, the system is working correctly!"
echo "✅ Frontend should be accessible at http://localhost:3001"
echo "✅ API documentation at http://localhost:8001/docs"
echo ""
echo "🛑 To stop the services:"
echo "docker compose -f docker-compose.test.yml down --volumes"
