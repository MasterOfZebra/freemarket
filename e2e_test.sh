#!/bin/bash
# e2e_test.sh - End-to-end testing for FreeMarket system

set -e

# Configuration
API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
TEST_USER_ID=999999999
TEST_TELEGRAM_ID=123456789

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

test_result() {
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        return 1
    fi
}

# Test API health
test_api_health() {
    log "Testing API health..."
    curl -f -s "$API_URL/health" > /dev/null
    test_result "API health check"
}

# Test user creation
test_user_creation() {
    log "Testing user creation..."
    response=$(curl -s -X POST "$API_URL/users/" \
        -H "Content-Type: application/json" \
        -d "{\"telegram_id\": $TEST_TELEGRAM_ID}")
    echo "$response" | grep -q "id"
    test_result "User creation"
}

# Test profile creation
test_profile_creation() {
    log "Testing profile creation..."
    response=$(curl -s -X POST "$API_URL/profiles/" \
        -H "Content-Type: application/json" \
        -d "{
            \"user_id\": $TEST_USER_ID,
            \"data\": {
                \"money\": \"1000 KZT\",
                \"tech\": \"Laptop\",
                \"clothes\": \"Jacket\",
                \"transport\": \"Bike\",
                \"food\": \"Fruits\",
                \"compute\": \"GPU\",
                \"services\": \"Cleaning\",
                \"tools\": \"Hammer\",
                \"other\": \"Books\"
            }
        }")
    echo "$response" | grep -q "id"
    test_result "Profile creation"
}

# Test profile retrieval
test_profile_retrieval() {
    log "Testing profile retrieval..."
    response=$(curl -s "$API_URL/profiles/$TEST_USER_ID")
    echo "$response" | grep -q "data"
    test_result "Profile retrieval"
}

# Test matching
test_matching() {
    log "Testing matching logic..."
    # Create another test profile
    curl -s -X POST "$API_URL/profiles/" \
        -H "Content-Type: application/json" \
        -d "{
            \"user_id\": $((TEST_USER_ID + 1)),
            \"data\": {
                \"money\": \"2000 KZT\",
                \"tech\": \"Monitor\",
                \"clothes\": \"Shoes\",
                \"transport\": \"Car\",
                \"food\": \"Vegetables\",
                \"compute\": \"CPU\",
                \"services\": \"Repair\",
                \"tools\": \"Screwdriver\",
                \"other\": \"Music\"
            }
        }" > /dev/null

    # Check if matches are created
    sleep 2  # Wait for matching to complete
    response=$(curl -s "$API_URL/matches/$TEST_USER_ID")
    echo "$response" | grep -q "score"
    test_result "Matching logic"
}

# Test rating
test_rating() {
    log "Testing rating system..."
    response=$(curl -s -X POST "$API_URL/ratings/" \
        -H "Content-Type: application/json" \
        -d "{
            \"from_user\": $TEST_USER_ID,
            \"to_user\": $((TEST_USER_ID + 1)),
            \"score\": 5,
            \"comment\": \"Great exchange!\"
        }")
    echo "$response" | grep -q "id"
    test_result "Rating creation"
}

# Test frontend
test_frontend() {
    log "Testing frontend..."
    curl -f -s "$FRONTEND_URL" > /dev/null
    test_result "Frontend availability"
}

# Test database backup
test_backup() {
    log "Testing backup functionality..."
    # This would require actual database setup
    # For now, just check if backup script exists
    [[ -f "backend/pg_backup.sh" ]]
    test_result "Backup script exists"
}

# Main test execution
main() {
    log "Starting FreeMarket end-to-end tests..."

    # Run all tests
    tests_passed=0
    tests_total=0

    ((tests_total++))
    if test_api_health; then ((tests_passed++)); fi

    ((tests_total++))
    if test_user_creation; then ((tests_passed++)); fi

    ((tests_total++))
    if test_profile_creation; then ((tests_passed++)); fi

    ((tests_total++))
    if test_profile_retrieval; then ((tests_passed++)); fi

    ((tests_total++))
    if test_matching; then ((tests_passed++)); fi

    ((tests_total++))
    if test_rating; then ((tests_passed++)); fi

    ((tests_total++))
    if test_frontend; then ((tests_passed++)); fi

    ((tests_total++))
    if test_backup; then ((tests_passed++)); fi

    # Summary
    echo ""
    log "Test Summary: $tests_passed/$tests_total tests passed"

    if [[ $tests_passed -eq $tests_total ]]; then
        log "All tests passed! 🎉"
        exit 0
    else
        error "Some tests failed. Please check the output above."
        exit 1
    fi
}

# Run main function
main "$@"
