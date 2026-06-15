-- Migration to add impression_count and registration_count columns to Unstop table
-- Run this in your Supabase SQL Editor

-- Add the new columns
ALTER TABLE "Unstop" 
ADD COLUMN IF NOT EXISTS "impression_count" VARCHAR(100),
ADD COLUMN IF NOT EXISTS "registration_count" VARCHAR(100);

-- Optional: Add comments to document the columns
COMMENT ON COLUMN "Unstop"."impression_count" IS 'Number of page views/impressions';
COMMENT ON COLUMN "Unstop"."registration_count" IS 'Actual number of participant registrations';
COMMENT ON COLUMN "Unstop"."registered_count" IS 'Legacy field - kept for backward compatibility';

-- Verify the columns were added
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'Unstop' 
ORDER BY ordinal_position;
