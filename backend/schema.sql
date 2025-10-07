-- FreeMarket Database Schema
-- PostgreSQL 13+

-- Create database (run as superuser)
-- CREATE DATABASE freemarket_db;
-- CREATE USER freemarket_user WITH PASSWORD 'password';
-- GRANT ALL PRIVILEGES ON DATABASE freemarket_db TO freemarket_user;

-- Connect to freemarket_db
-- \c freemarket_db

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  username TEXT UNIQUE,
  telegram_id BIGINT UNIQUE,
  contact JSONB,
  trust_score FLOAT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  last_active_at TIMESTAMP WITH TIME ZONE
);

-- Profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  data JSONB NOT NULL,
  location TEXT,
  visibility BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Items table (offers/wants)
CREATE TABLE IF NOT EXISTS items (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  kind SMALLINT NOT NULL CHECK (kind IN (1, 2)), -- 1=offer, 2=want
  category TEXT NOT NULL,
  title TEXT,
  description TEXT,
  metadata JSONB,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
  id BIGSERIAL PRIMARY KEY,
  item_a BIGINT REFERENCES items(id),
  item_b BIGINT REFERENCES items(id),
  score FLOAT NOT NULL CHECK (score >= 0 AND score <= 1),
  computed_by TEXT DEFAULT 'rule-based',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  notified BOOLEAN DEFAULT FALSE,
  notified_at TIMESTAMP WITH TIME ZONE
);

-- Ratings table
CREATE TABLE IF NOT EXISTS ratings (
  id BIGSERIAL PRIMARY KEY,
  from_user BIGINT REFERENCES users(id),
  to_user BIGINT REFERENCES users(id),
  score SMALLINT NOT NULL CHECK (score BETWEEN 1 AND 5),
  comment TEXT,
  tx_id TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id),
  channel TEXT DEFAULT 'telegram',
  payload JSONB,
  status TEXT DEFAULT 'queued' CHECK (status IN ('queued', 'sent', 'failed')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  sent_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_items_user_id ON items(user_id);
CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
CREATE INDEX IF NOT EXISTS idx_items_active ON items(active);
CREATE INDEX IF NOT EXISTS idx_matches_item_a ON matches(item_a);
CREATE INDEX IF NOT EXISTS idx_matches_item_b ON matches(item_b);
CREATE INDEX IF NOT EXISTS idx_ratings_from_user ON ratings(from_user);
CREATE INDEX IF NOT EXISTS idx_ratings_to_user ON ratings(to_user);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_items_description_gin ON items USING GIN (to_tsvector('english', description));
CREATE INDEX IF NOT EXISTS idx_items_title_gin ON items USING GIN (to_tsvector('english', title));

-- GIN indexes for JSONB
CREATE INDEX IF NOT EXISTS idx_profiles_data_gin ON profiles USING GIN (data);
CREATE INDEX IF NOT EXISTS idx_items_metadata_gin ON items USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_notifications_payload_gin ON notifications USING GIN (payload);

-- Function to update trust score
CREATE OR REPLACE FUNCTION update_trust_score()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE users
  SET trust_score = (
    SELECT COALESCE(AVG(score), 0)
    FROM ratings
    WHERE to_user = NEW.to_user
  )
  WHERE id = NEW.to_user;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update trust score on rating insert/update
CREATE TRIGGER update_trust_score_trigger
  AFTER INSERT OR UPDATE ON ratings
  FOR EACH ROW
  EXECUTE FUNCTION update_trust_score();

-- Function to update last_active_at
CREATE OR REPLACE FUNCTION update_last_active()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE users
  SET last_active_at = now()
  WHERE id = NEW.user_id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for last_active_at
CREATE TRIGGER update_last_active_profiles
  AFTER INSERT OR UPDATE ON profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_last_active();

CREATE TRIGGER update_last_active_items
  AFTER INSERT OR UPDATE ON items
  FOR EACH ROW
  EXECUTE FUNCTION update_last_active();

CREATE TRIGGER update_last_active_ratings
  AFTER INSERT OR UPDATE ON ratings
  FOR EACH ROW
  EXECUTE FUNCTION update_last_active();

-- Sample data (optional, for testing)
-- INSERT INTO users (username, telegram_id) VALUES ('testuser', 123456789);
