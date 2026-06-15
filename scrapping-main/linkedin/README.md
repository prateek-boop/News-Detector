# LinkedIn Scraper with Django

A Django-based automation tool for scraping emails and LinkedIn profiles from post comments. The system stores data in a local SQLite database and provides export capabilities to multiple formats.

## Project Overview

This tool automates the collection of contact information from LinkedIn posts. It can extract both email addresses from comments and full LinkedIn profile information from comment authors. All data is stored in a structured database with relationship mapping between contacts and profiles.

## Setup Instructions

1. Activate your Python virtual environment and install required dependencies:
```bash
source venv/bin/activate
pip install django seleniumbase
```

2. Apply database migrations to create necessary tables:
```bash
python manage.py migrate
```

3. Create an admin user to access the Django admin interface:
```bash
python manage.py createsuperuser
```

## Available Commands

### Complete Scraping (Recommended)

Scrape both emails and profiles in a single command:

```bash
# Scrape everything from a post (emails + profiles) - FAST MODE DEFAULT
python manage.py scrape_all --url "https://www.linkedin.com/posts/..."

# Maximum speed (3.4x faster, use for large batches)
python manage.py scrape_all --url "YOUR_URL" --speed aggressive

# Conservative mode (slower but safest)
python manage.py scrape_all --url "YOUR_URL" --speed normal

# Run in visible mode for debugging
python manage.py scrape_all --url "YOUR_URL" --visible

# Limit number of profiles (useful for testing)
python manage.py scrape_all --url "YOUR_URL" --limit 50

# Only scrape emails, skip profiles
python manage.py scrape_all --url "YOUR_URL" --skip-profiles

# Only scrape profiles, skip emails
python manage.py scrape_all --url "YOUR_URL" --skip-emails

# Combine options for maximum speed test
python manage.py scrape_all --url "YOUR_URL" --speed aggressive --limit 20 --visible
```

**Speed Modes:**
- `--speed normal`: Original speed with 0.8s delays (safest)
- `--speed fast`: **Default mode** with 0.3s delays (2.25x faster)
- `--speed aggressive`: Maximum speed with 0.15s delays (3.4x faster)

See [SPEED_OPTIMIZATION.md](SPEED_OPTIMIZATION.md) for detailed performance benchmarks.

This command automatically:
- Loads all comments from the post
- Extracts and saves emails to database
- Extracts and saves LinkedIn profiles to database
- Links profiles to contacts by name matching
- Exports all data to JSON and CSV files

### Email Scraping

Scrape email addresses from LinkedIn post comments:

```bash
# Basic usage with required URL parameter
python manage.py scrape_emails --url "https://www.linkedin.com/posts/..."

# Show browser window instead of running in headless mode
python manage.py scrape_emails --url "YOUR_URL" --visible

# Specify target number of comments to load
python manage.py scrape_emails --url "YOUR_URL" --target 1000

# Use custom output directory for result files
python manage.py scrape_emails --url "YOUR_URL" --output-dir ./emails

# Specify Chrome profile directory
python manage.py scrape_emails --url "YOUR_URL" --profile-dir ./profile
```

### Profile Scraping

Scrape full LinkedIn profiles from comment authors:

```bash
# Scrape all profiles from a post
python manage.py scrape_profiles --url "https://www.linkedin.com/posts/..."

# Run in visible mode for debugging
python manage.py scrape_profiles --url "YOUR_URL" --visible

# Limit the number of profiles to scrape
python manage.py scrape_profiles --url "YOUR_URL" --limit 50

# Combine options
python manage.py scrape_profiles --url "YOUR_URL" --limit 20 --visible
```

### Export Contacts

Export scraped email contacts to file formats:

```bash
# Export to both JSON and CSV formats
python manage.py export_contacts

# Export to specific format only
python manage.py export_contacts --format json
python manage.py export_contacts --format csv

# Use custom output filename
python manage.py export_contacts --output my_contacts
```

### Export Profiles

Export scraped LinkedIn profiles to file formats:

```bash
# Export to both JSON and CSV formats
python manage.py export_profiles

# Include linked contact email information
python manage.py export_profiles --with-contacts

# Export to specific format only
python manage.py export_profiles --format json
python manage.py export_profiles --format csv

# Use custom output filename
python manage.py export_profiles --output my_profiles

# Combine options
python manage.py export_profiles --with-contacts --format csv --output full_data
```

### Admin Interface

Access the Django admin panel to view and manage data:

```bash
# Start the development server
python manage.py runserver

# Access admin at http://localhost:8000/admin
# View contacts at http://localhost:8000/admin/contacts/contact/
# View profiles at http://localhost:8000/admin/contacts/profile/
```

## Complete Workflow Example

The simplest way to scrape everything from a LinkedIn post:

```bash
# Step 1: Activate virtual environment
source venv/bin/activate

# Step 2: Scrape everything (emails + profiles) in one command
python manage.py scrape_all --url "https://www.linkedin.com/posts/YOUR_POST_URL"

# Step 3: View data in admin interface
python manage.py runserver
# Then open http://localhost:8000/admin in your browser
```

Alternative workflow using separate commands:

```bash
# Step 1: Activate virtual environment
source venv/bin/activate

# Step 2: Scrape emails from the post
python manage.py scrape_emails --url "https://www.linkedin.com/posts/YOUR_POST_URL"

# Step 3: Scrape LinkedIn profiles from the same post
python manage.py scrape_profiles --url "https://www.linkedin.com/posts/YOUR_POST_URL"

# Step 4: Export contacts (emails)
python manage.py export_contacts

# Step 5: Export profiles with linked contact information
python manage.py export_profiles --with-contacts

# Step 6: View data in admin interface
python manage.py runserver
# Then open http://localhost:8000/admin in your browser
```

## Database Structure

### Contact Model
Stores email addresses extracted from comments:
- email (unique identifier, required)
- name (extracted from email or profile, optional)
- created_at (timestamp, automatic)
- updated_at (timestamp, automatic)

### Profile Model
Stores comprehensive LinkedIn profile data:
- linkedin_url (unique identifier, required)
- full_name (optional)
- headline (optional)
- location (optional)
- current_company (optional)
- current_position (optional)
- industry (optional)
- connections (integer count, optional)
- followers (integer count, optional)
- about (text bio section, optional)
- profile_image_url (optional)
- is_verified (boolean, default false)
- contact (foreign key to Contact, optional one-to-one relationship)
- scraped_at (timestamp, automatic)
- updated_at (timestamp, automatic)

### Relationships
The Profile model can optionally link to a Contact via a one-to-one relationship. This allows you to associate a LinkedIn profile with an email address when both are available. The linking happens automatically during scraping based on name matching.

## Output Files

The system generates the following files based on your commands:

- db.sqlite3 - SQLite database containing all scraped data
- contacts_export.json - Contact emails in JSON format
- contacts_export.csv - Contact emails in CSV format
- linkedin_profiles.json - Profile data in JSON format
- linkedin_profiles.csv - Profile data in CSV format
- linkedin_emails.txt - Plain text list of emails (one per line)
- linkedin_emails.json - Email list in JSON format
- linkedin_emails.csv - Email list in CSV format

## Key Features

### Email Scraper
- Automatically loads all comments by clicking "Load more" buttons repeatedly
- Fast scraping with optimized 0.8 second delays between actions
- Incremental database saves every 10 button clicks to prevent data loss
- Multiple selector strategies for button detection (class, text, attribute)
- Email validation using regex patterns
- Duplicate prevention through unique database constraints
- Headless browser mode for faster operation (runs in background)
- Uses saved Chrome profile to maintain LinkedIn login session
- Configurable target for number of comments to load

### Profile Scraper
- Extracts all unique profile URLs from comment authors
- Visits each profile individually to collect detailed information
- Automatically links profiles to existing contacts by name matching
- Skips already scraped profiles to avoid duplicates
- URL cleaning removes query parameters and tracking codes
- Continues operation even if individual profiles fail to scrape
- Real-time progress tracking with detailed statistics
- Configurable limit to scrape only a subset of profiles for testing
- Robust extraction with multiple fallback selectors for each field

## How It Works

### Email Scraping Process
1. Opens the specified LinkedIn post URL using your saved Chrome profile
2. Waits for page to fully load and verifies you are logged in
3. Opens the comments section if not already visible
4. Continuously clicks "Load more comments" button until no more exist
5. Extracts all text content from the page after each load
6. Uses regex patterns to find email addresses in comment text
7. Validates each email address and filters out spam or invalid formats
8. Saves valid emails to database with incremental commits every 10 clicks
9. Extracts name from email prefix (part before @ symbol)
10. Exports final results to specified file formats

### Profile Scraping Process
1. Opens the LinkedIn post URL and waits for it to load
2. Verifies login status to ensure access to content
3. Loads all comments by repeatedly clicking "Load more" button
4. Extracts all profile URLs from comment author links using JavaScript
5. Filters to only include valid LinkedIn profile URLs (not company pages)
6. Cleans URLs by removing query parameters and anchor tags
7. Creates a list of unique profile URLs to visit
8. Visits each profile page individually in sequence
9. Extracts profile information using multiple CSS selectors
10. Attempts to link profile with existing contact by matching first name
11. Saves profile to database if not already present (checked by URL)
12. Continues to next profile even if current one fails
13. Generates summary report with counts of scraped, skipped, and failed profiles

## Command Reference

### scrape_all

Scrape both emails and profiles from a LinkedIn post in one command. This is the recommended command for most use cases.

Options:
- --url (required) - LinkedIn post URL to scrape
- --visible (optional) - Show browser window for debugging
- --limit (optional) - Maximum number of profiles to scrape (default: unlimited)
- --skip-emails (optional) - Skip email scraping, only scrape profiles
- --skip-profiles (optional) - Skip profile scraping, only scrape emails

Features:
- Automatically loads all comments
- Scrapes both emails and profiles in one run
- Links profiles to contacts by name
- Auto-exports data to JSON and CSV files
- Shows comprehensive summary at the end

Performance: Depends on number of comments and profiles. For a post with 500 comments and 100 profiles, expect 10-15 minutes in headless mode.

### scrape_emails

Scrape email addresses from LinkedIn post comments.

Options:
- --url (required) - LinkedIn post URL to scrape
- --visible (optional) - Show browser window for debugging
- --target (optional) - Target number of comments to load (default: 554)
- --output-dir (optional) - Directory to save output files (default: current directory)
- --profile-dir (optional) - Chrome profile directory (default: ./profile)

Performance: Approximately 2-3 minutes for 554 comments in headless mode.

### scrape_profiles

Scrape LinkedIn profiles from comment authors.

Options:
- --url (required) - LinkedIn post URL to scrape
- --visible (optional) - Show browser window for debugging
- --limit (optional) - Maximum number of profiles to scrape (default: unlimited)

Performance: Approximately 3-5 seconds per profile. For 100 profiles, expect 5-10 minutes.

### export_contacts

Export contact emails to file formats.

Options:
- --format (optional) - Export format: json, csv, or both (default: both)
- --output (optional) - Output filename without extension (default: contacts_export)

Output: Creates JSON and/or CSV files with contact email data.

### export_profiles

Export LinkedIn profiles to file formats.

Options:
- --format (optional) - Export format: json, csv, or both (default: both)
- --output (optional) - Output filename without extension (default: linkedin_profiles)
- --with-contacts (optional) - Include linked contact email information in export

Output: Creates JSON and/or CSV files with profile data.

## Infinite Loop Scraper (Exponential Growth System)

The infinite loop scraper is an advanced feature that enables exponential data collection by discovering new posts through profile activity. Instead of manually providing post URLs, the system automatically discovers thousands of posts by following a chain of connections.

### How It Works

1. Start with a seed post URL
2. Scrape profiles and emails from that post
3. Visit each profile's recent activity page
4. Discover posts they have commented on
5. Queue those posts for scraping
6. Repeat indefinitely

This creates exponential growth:
- 1 seed post → 100 profiles
- 100 profiles × 50 posts each = 5,000 new posts
- 5,000 posts × 100 profiles each = 500,000 profiles
- Continue infinitely...

### Basic Usage

Start infinite scraping with a seed post:

```bash
# Basic infinite loop
python manage.py scrape_infinite --seed-url "https://www.linkedin.com/posts/..."

# With safety limits
python manage.py scrape_infinite \
  --seed-url "https://www.linkedin.com/posts/..." \
  --max-depth 5 \
  --max-posts 100 \
  --min-comments 200

# Visible mode for debugging
python manage.py scrape_infinite \
  --seed-url "https://www.linkedin.com/posts/..." \
  --visible \
  --batch-size 10
```

### Command Options

- --seed-url (required) - Initial post URL to start the scraping chain
- --max-depth (default: 999) - Maximum depth levels to scrape
- --max-posts (default: 999999) - Stop after scraping this many posts
- --min-comments (default: 100) - Only queue posts with at least this many comments
- --delay (default: 5) - Seconds to wait between posts
- --batch-size (default: 10) - Number of profiles to process per batch
- --visible - Show browser window
- --skip-activity - Only scrape seed posts, don't discover new ones

### Profile Activity Scraping

Scrape posts from specific profiles' recent activity:

```bash
# Scrape single profile's activity
python manage.py scrape_profile_activity \
  --profile-url "https://www.linkedin.com/in/username/"

# Scrape batch of pending profiles
python manage.py scrape_profile_activity \
  --batch-size 20 \
  --min-comments 100 \
  --scroll-limit 10

# Visible mode
python manage.py scrape_profile_activity \
  --batch-size 5 \
  --visible
```

Options:
- --profile-url - Specific profile to scrape (otherwise processes pending profiles)
- --batch-size (default: 50) - Number of profiles to process
- --min-comments (default: 100) - Minimum comments to queue post
- --scroll-limit (default: 10) - Maximum scrolls on activity page
- --visible - Show browser window

### Queue Management

Check current queue status:

```bash
# View queue statistics
python manage.py queue_stats
```

Shows:
- Pending and scraped posts
- Pending and scraped profiles
- Total emails collected
- Top posts by comment count
- Recent scraping sessions
- Discovery statistics

Reset queue flags for re-scraping:

```bash
# Reset posts (mark as unscraped)
python manage.py queue_reset --posts --confirm

# Reset profile activity flags
python manage.py queue_reset --profiles --confirm

# Delete all sessions
python manage.py queue_reset --sessions --confirm

# Reset everything
python manage.py queue_reset --all --confirm
```

Note: The --confirm flag is required to prevent accidental resets.

### Database Models

The infinite scraper adds three new models:

**Post Model:**
- post_url (unique) - LinkedIn post URL
- comment_count - Number of comments
- scraped - Whether post has been scraped
- scraped_at - Timestamp
- discovered_from_profile - Which profile discovered this post
- created_at - When added to queue

**ScrapingSession Model:**
- seed_url - Initial post URL
- started_at, ended_at - Session timestamps
- depth_level - Current depth in discovery chain
- posts_scraped, profiles_scraped, emails_collected - Counters
- status - running, paused, completed, or failed
- max_posts, max_depth - Safety limits

**Profile Model (additional fields):**
- activity_scraped - Whether profile activity has been scraped
- activity_scraped_at - Timestamp
- posts_discovered_count - Number of posts discovered from this profile

### Complete Workflow Example

```bash
# Step 1: Start infinite scraping with safety limits
python manage.py scrape_infinite \
  --seed-url "https://www.linkedin.com/posts/example-post" \
  --max-depth 3 \
  --max-posts 50 \
  --min-comments 200

# Step 2: Monitor progress
python manage.py queue_stats

# Step 3: Export collected data
python manage.py export_all_to_supabase

# Step 4: View in admin interface
python manage.py runserver
# Visit http://localhost:8000/admin
```

### Safety Features

The infinite scraper includes several safety mechanisms:

1. **Depth limits** - Prevent infinite recursion
2. **Post limits** - Cap total number of posts scraped
3. **Comment filters** - Only queue high-engagement posts
4. **Duplicate prevention** - Skip already scraped posts/profiles
5. **Session tracking** - Monitor and resume interrupted sessions
6. **Keyboard interrupt** - Ctrl+C saves progress and exits gracefully
7. **Error handling** - Continue despite individual failures

### Performance Expectations

- **Post scraping**: 2-3 minutes per post (depends on comment count)
- **Activity scraping**: 10-15 seconds per profile
- **Batch of 10 profiles**: 2-3 minutes
- **Complete cycle**: 30-45 minutes for batch of 10 posts

With conservative settings:
- 10 posts × 3 min = 30 minutes
- Discover 500 new posts from 100 profiles
- Next iteration: 500 posts × 3 min = 25 hours

### Best Practices

1. **Start small** - Test with --max-posts 10 first
2. **Use comment filters** - Set --min-comments 200+ for quality posts
3. **Monitor queue** - Run queue_stats regularly to check growth
4. **Export frequently** - Backup data to Supabase every few hours
5. **Adjust delays** - Increase --delay if you notice rate limiting
6. **Set depth limits** - Use --max-depth 3-5 for controlled growth
7. **Run overnight** - Long sessions work well unattended

### Troubleshooting Infinite Scraper

**Queue not growing:**
- Check min-comments threshold (may be filtering all posts)
- Verify profiles have recent activity
- Some profiles may have private activity pages

**Too many posts queued:**
- Lower min-comments threshold
- Reduce batch-size
- Set stricter max-posts limit

**Session interrupted:**
- Progress is automatically saved
- Check queue_stats to see current state
- Resume with same command (skips already scraped)

**Rate limiting:**
- Increase --delay parameter
- Reduce --batch-size
- Add more time between runs

## Troubleshooting

### Not logged into LinkedIn
If you see an authentication error or are redirected to login page:
- Make sure you have logged into LinkedIn in Chrome before running the scraper
- Verify the profile directory path points to your Chrome profile
- Try running with --visible flag to see what is happening

### No comments loading
If the scraper is not finding the "Load more" button:
- Run with --visible flag to see the browser actions
- Check that the post URL is correct and publicly accessible
- Verify you are logged into LinkedIn
- The post may have comments disabled or no comments to load

### Import errors
If you get module import errors:
- Make sure you activated the virtual environment
- Install required packages: pip install django seleniumbase
- Run migrations: python manage.py migrate

### Profile extraction fails
If profile scraping is not extracting data:
- LinkedIn may have changed their page structure
- Run with --visible flag to debug
- Check that profiles are publicly visible
- Some fields may be empty if not set on the profile

### Export creates empty files
If export files are empty:
- Check that you have data in the database first
- Run the scrape commands before exporting
- View data in admin interface to verify: python manage.py runserver

## Performance Notes

Headless mode (default) is 3-5 times faster than visible mode because it does not need to render the browser window. Use visible mode only when debugging issues.

The scrapers use deliberate delays between actions to avoid triggering LinkedIn's rate limiting or bot detection. Do not reduce these delays or you may get blocked.

Incremental saving during scraping means your data is protected even if the scraper is interrupted. You can restart and it will skip already processed items.

## Database Queries

You can query the database programmatically using Django's ORM:

```python
from contacts.models import Contact, Profile

# Get all contacts
contacts = Contact.objects.all()

# Get contacts with linked profiles
contacts_with_profiles = Contact.objects.filter(profile__isnull=False)

# Get all profiles
profiles = Profile.objects.all()

# Get profiles from a specific company
company_profiles = Profile.objects.filter(current_company__icontains='Google')

# Get highly connected profiles
influencers = Profile.objects.filter(connections__gte=500).order_by('-connections')

# Access related data
contact = Contact.objects.first()
if hasattr(contact, 'profile'):
    print(f"LinkedIn: {contact.profile.linkedin_url}")
    print(f"Company: {contact.profile.current_company}")
```

## Getting Help

View detailed help for any command:

```bash
python manage.py scrape_all --help
python manage.py scrape_emails --help
python manage.py scrape_profiles --help
python manage.py export_contacts --help
python manage.py export_profiles --help
```

For more information about Django management commands:
```bash
python manage.py help
```

## Quick Reference

Most common command (recommended):
```bash
python manage.py scrape_all --url "YOUR_LINKEDIN_POST_URL"
```

Test with limited profiles:
```bash
python manage.py scrape_all --url "YOUR_URL" --limit 20 --visible
```

Only emails:
```bash
python manage.py scrape_all --url "YOUR_URL" --skip-profiles
```

Only profiles:
```bash
python manage.py scrape_all --url "YOUR_URL" --skip-emails
```
