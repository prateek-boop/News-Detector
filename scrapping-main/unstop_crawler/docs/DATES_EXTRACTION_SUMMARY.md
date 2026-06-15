# ✅ Important Dates Extraction - UPDATED

## What Changed

The scraper now **prioritizes extracting dates from the specific Angular component** you mentioned:
`/html/body/app-root/div[2]/main/app-global-search/div/div[2]/div[2]/app-competition-preview/app-explore-opportunity-viewer/div/app-competition-round-form`

## Extraction Priority

The scraper now follows this priority order:

1. **PRIORITY 1**: `<app-competition-round-form>` - The specific section with structured dates
2. **PRIORITY 2**: `<app-explore-opportunity-viewer>` - The parent container
3. **PRIORITY 3**: Sections with classes containing: `round`, `stage`, `timeline`, `deadline`
4. **FALLBACK**: General search with strict date pattern matching

## What Gets Extracted

The scraper now captures:
- ✅ **Start dates** with times (e.g., "Start: 24 Oct 25, 04:30 PM CUT")
- ✅ **End dates** with times (e.g., "End: 26 Oct 25, 06:29 PM CUT")
- ✅ **Registration deadlines** (e.g., "Registration Deadline 25 Oct 25, 06:29 PM CUT")
- ✅ **Stage/Round information** (e.g., "The Race - Start: 15 Nov 25, 09:00 AM")
- ✅ **Multiple rounds/phases** if available

## Example Output

```
HACKATHON: Mach 1.0
IMPORTANT DATES:
Start: 15 Nov 25, 09:00 AM CUT
End: 15 Nov 25, 12:30 PM CUT
Registration Deadline 31 Oct 25, 03:07 PM CUT

HACKATHON: Open Vibe Hackathon 2025
IMPORTANT DATES:
Start: 24 Oct 25, 04:30 PM CUT
End: 26 Oct 25, 06:29 PM CUT
Start: 26 Oct 25, 06:29 PM CUT
End: 27 Oct 25, 06:29 PM CUT
Registration Deadline 25 Oct 25, 06:29 PM CUT
```

## How to Use

```bash
# Scrape hackathons with new date extraction
python manage.py scrape_unstop --limit 10

# Export with important dates
python manage.py export_hackathons --format json --output hackathons.json
python manage.py export_hackathons --format csv --output hackathons.csv
```

## Technical Details

- Targets the Angular component `app-competition-round-form`
- Extracts dates with format: `DD Mon YY, HH:MM AM/PM TZ`
- Removes duplicates automatically
- Stores up to 20 date entries per hackathon
- Handles multiple rounds/stages/phases

All working and tested! ✅
