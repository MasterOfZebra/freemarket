#!/bin/bash
# Script to check listings in the database

echo "=========================================="
echo "Checking Listings in Database"
echo "=========================================="
echo ""

COMPOSE_FILE="docker-compose.prod.yml"
POSTGRES_SERVICE="postgres"
DB_USER="assistadmin_pg"
DB_NAME="assistance_kz"

# Get user_id from command line argument or default to checking all
USER_ID=${1:-""}

if [ -n "$USER_ID" ]; then
    echo "Checking listings for user_id: $USER_ID"
    echo ""
    
    # Check listings for specific user
    echo "[1/3] Listings for user $USER_ID:"
    docker compose -f "$COMPOSE_FILE" exec -T "$POSTGRES_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            id, 
            user_id, 
            title, 
            description, 
            created_at 
        FROM listings 
        WHERE user_id = $USER_ID 
        ORDER BY created_at DESC;
    "
    echo ""
    
    # Check listing items for this user's listings
    echo "[2/3] Listing items for user $USER_ID:"
    docker compose -f "$COMPOSE_FILE" exec -T "$POSTGRES_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            li.id,
            li.listing_id,
            li.item_type,
            li.category,
            li.exchange_type,
            li.item_name,
            li.value_tenge,
            li.duration_days,
            li.is_archived,
            li.created_at
        FROM listing_items li
        JOIN listings l ON li.listing_id = l.id
        WHERE l.user_id = $USER_ID
        ORDER BY li.created_at DESC;
    "
    echo ""
    
    # Count items by type
    echo "[3/3] Item counts for user $USER_ID:"
    docker compose -f "$COMPOSE_FILE" exec -T "$POSTGRES_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            l.id as listing_id,
            COUNT(CASE WHEN li.item_type = 'want' AND li.is_archived = false THEN 1 END) as wants_count,
            COUNT(CASE WHEN li.item_type = 'offer' AND li.is_archived = false THEN 1 END) as offers_count,
            COUNT(li.id) as total_items
        FROM listings l
        LEFT JOIN listing_items li ON l.id = li.listing_id
        WHERE l.user_id = $USER_ID
        GROUP BY l.id
        ORDER BY l.created_at DESC;
    "
else
    echo "Checking all listings"
    echo ""
    
    # Check all listings
    echo "[1/3] All listings:"
    docker compose -f "$COMPOSE_FILE" exec -T "$POSTGRES_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            id, 
            user_id, 
            title, 
            description, 
            created_at 
        FROM listings 
        ORDER BY created_at DESC 
        LIMIT 20;
    "
    echo ""
    
    # Check recent listing items
    echo "[2/3] Recent listing items:"
    docker compose -f "$COMPOSE_FILE" exec -T "$POSTGRES_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            li.id,
            li.listing_id,
            l.user_id,
            li.item_type,
            li.category,
            li.exchange_type,
            li.item_name,
            li.is_archived,
            li.created_at
        FROM listing_items li
        JOIN listings l ON li.listing_id = l.id
        ORDER BY li.created_at DESC
        LIMIT 20;
    "
    echo ""
    
    # Summary statistics
    echo "[3/3] Summary statistics:"
    docker compose -f "$COMPOSE_FILE" exec -T "$POSTGRES_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            COUNT(DISTINCT l.id) as total_listings,
            COUNT(DISTINCT l.user_id) as total_users_with_listings,
            COUNT(li.id) as total_items,
            COUNT(CASE WHEN li.item_type = 'want' AND li.is_archived = false THEN 1 END) as active_wants,
            COUNT(CASE WHEN li.item_type = 'offer' AND li.is_archived = false THEN 1 END) as active_offers
        FROM listings l
        LEFT JOIN listing_items li ON l.id = li.listing_id;
    "
fi

echo ""
echo "=========================================="
echo "Check completed!"
echo "=========================================="

