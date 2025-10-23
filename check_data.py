import sys
sys.path.append('.')
from backend.database import SessionLocal
from backend.crud import get_market_listings

db = SessionLocal()
listings, total = get_market_listings(db, listing_type='wants')
print(f'Wants: {total} listings')
listings, total = get_market_listings(db, listing_type='offers')
print(f'Offers: {total} listings')
db.close()
