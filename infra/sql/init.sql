-- Create anime_user role if it doesn't exist
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = 'anime_user'
   ) THEN
      CREATE ROLE anime_user LOGIN PASSWORD 'anime_password';
   END IF;
END
$do$;

-- Ensure anime_user owns the database
ALTER DATABASE anime_dashboard OWNER TO anime_user;
GRANT ALL PRIVILEGES ON DATABASE anime_dashboard TO anime_user;

-- Initialize AnimeDashboard database schema

-- Create anime_snapshots table for storing Jikan API data snapshots
CREATE TABLE IF NOT EXISTS anime_snapshots (
    id SERIAL PRIMARY KEY,
    mal_id INTEGER NOT NULL,
    url VARCHAR(500),
    
    -- Title information
    title VARCHAR(500) NOT NULL,
    title_english VARCHAR(500),
    title_japanese VARCHAR(500),
    title_synonyms JSONB, -- Array of alternative titles
    titles JSONB, -- Full titles array with types
    
    -- Basic info
    type VARCHAR(50), -- "TV", "Movie", "OVA", etc.
    source VARCHAR(100),
    episodes INTEGER,
    status VARCHAR(100), -- "Finished Airing", "Currently Airing", etc.
    airing BOOLEAN,
    duration VARCHAR(100),
    rating VARCHAR(100), -- "G - All Ages", "PG-13", etc.
    
    -- Scores and rankings
    score DECIMAL(4,2), -- Can be up to 10.00
    scored_by INTEGER,
    rank INTEGER,
    popularity INTEGER,
    members INTEGER,
    favorites INTEGER,
    approved BOOLEAN,
    
    -- Dates
    season VARCHAR(50), -- "summer", "winter", etc.
    year INTEGER,
    aired JSONB, -- Full aired object with from/to/prop
    
    -- Content
    synopsis TEXT,
    background TEXT,
    
    -- Media
    images JSONB, -- Full images object (jpg/webp with different sizes)
    trailer JSONB, -- Trailer info (youtube_id, url, embed_url)
    
    -- Related entities (stored as JSON arrays)
    genres JSONB, -- Array of genre objects with mal_id, type, name, url
    explicit_genres JSONB,
    themes JSONB,
    demographics JSONB,
    studios JSONB,
    producers JSONB,
    licensors JSONB,
    
    -- Additional data
    broadcast JSONB, -- Broadcasting info
    relations JSONB, -- Related anime/manga
    theme JSONB, -- Opening/ending themes
    external JSONB, -- External links
    streaming JSONB, -- Streaming platforms
    
    -- Metadata
    snapshot_type VARCHAR(50) NOT NULL, -- 'top', 'seasonal', 'upcoming', 'search'
    snapshot_date DATE NOT NULL, -- When this snapshot was taken
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_anime_snapshots_mal_id ON anime_snapshots(mal_id);
CREATE INDEX IF NOT EXISTS idx_anime_snapshots_snapshot_type ON anime_snapshots(snapshot_type);
CREATE INDEX IF NOT EXISTS idx_anime_snapshots_snapshot_date ON anime_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_anime_snapshots_season_year ON anime_snapshots(season, year);
CREATE INDEX IF NOT EXISTS idx_anime_snapshots_score ON anime_snapshots(score);
CREATE INDEX IF NOT EXISTS idx_anime_snapshots_rank ON anime_snapshots(rank);
CREATE INDEX IF NOT EXISTS idx_anime_snapshots_created_at ON anime_snapshots(created_at);
CREATE INDEX IF NOT EXISTS idx_anime_snapshots_type ON anime_snapshots(type);
CREATE INDEX IF NOT EXISTS idx_anime_snapshots_status ON anime_snapshots(status);

-- Create unique constraint for upsert operations
CREATE UNIQUE INDEX IF NOT EXISTS idx_anime_snapshots_unique 
ON anime_snapshots(mal_id, snapshot_type, snapshot_date);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_anime_snapshots_updated_at 
    BEFORE UPDATE ON anime_snapshots 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
