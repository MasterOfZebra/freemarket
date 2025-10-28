#!/bin/bash
# Initialize database with all tables from SQLAlchemy models

cd /app

# Run Python script to create all tables
python << 'EOF'
import os
from backend.database import engine, Base
from backend import models

print("Creating all tables from SQLAlchemy models...")

# Create all tables defined in models
Base.metadata.create_all(bind=engine)

print("✓ Database initialized successfully!")
print("All tables created from models.")
EOF
