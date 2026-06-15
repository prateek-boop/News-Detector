# LinkedIn Infinite Scraper - Implementation Guide

## Overview

An exponentially growing scraping system that:
1. Scrapes posts to get profiles and emails
2. Visits each profile's recent activity to find posts they commented on
3. Queues those posts for scraping
4. Repeats infinitely, creating a self-sustaining data collection loop

## Architecture

### Data Flow

```
Seed Post URL
    ↓
Scrape Post (scrape_all)
    ↓
Extract: Profile URLs + Emails
    ↓
Save to Database
    ↓
Queue: Profiles for Activity Scraping
    ↓
For Each Profile: Visit /recent-activity/comments/
    ↓
Extract: Post URLs (filter by comment count)
    ↓
Queue: Posts for Scraping
    ↓
LOOP BACK TO: Scrape Post
```

### Growth Example

```
Iteration 1: 1 post → 100 profiles
Iteration 2: 100 profiles → 5,000 posts (50 posts per profile)
Iteration 3: 5,000 posts → 500,000 profiles (100 profiles per post)
Iteration 4: 500,000 profiles → 25,000,000 posts
```

## Database Schema

### New Models to Add

#### 1. Post Model

```python
class Post(models.Model):
    post_url = models.URLField(unique=True)
    comment_count = models.IntegerField(default=0, blank=True, null=True)
    scraped = models.BooleanField(default=False)
    scraped_at = models.DateTimeField(null=True, blank=True)
    discovered_from_profile = models.ForeignKey(
        'Profile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discovered_posts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-comment_count']
        indexes = [
            models.Index(fields=['scraped', 'comment_count']),
        ]
```

#### 2. Update Profile Model

Add these fields to existing Profile model:

```python
activity_scraped = models.BooleanField(default=False)
activity_scraped_at = models.DateTimeField(null=True, blank=True)
posts_discovered_count = models.IntegerField(default=0)
```

#### 3. ScrapingSession Model (Optional - for tracking)

```python
class ScrapingSession(models.Model):
    seed_url = models.URLField()
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    depth_level = models.IntegerField(default=0)
    posts_scraped = models.IntegerField(default=0)
    profiles_scraped = models.IntegerField(default=0)
    emails_collected = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('running', 'Running'),
            ('paused', 'Paused'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='running'
    )
```

## Implementation Steps

### Phase 1: Database Setup

**File:** `contacts/models.py`

1. Add Post model
2. Update Profile model with activity tracking fields
3. Add ScrapingSession model (optional)
4. Create migration:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

**File:** `contacts/admin.py`

Add admin interfaces for new models:

```python
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['post_url', 'comment_count', 'scraped', 'scraped_at']
    list_filter = ['scraped', 'comment_count']
    search_fields = ['post_url']
    readonly_fields = ['created_at', 'scraped_at']
```

### Phase 2: Profile Activity Scraper

**File:** `contacts/management/commands/scrape_profile_activity.py`

This command visits a profile's recent activity page and extracts post URLs.

```python
from django.core.management.base import BaseCommand
from seleniumbase import SB
from contacts.models import Profile, Post
import os

class Command(BaseCommand):
    help = 'Scrape posts from a LinkedIn profile recent activity'

    def add_arguments(self, parser):
        parser.add_argument('--profile-url', type=str, help='Specific profile URL')
        parser.add_argument('--batch-size', type=int, default=50, help='Number of profiles to process')
        parser.add_argument('--min-comments', type=int, default=100, help='Minimum comments to queue post')
        parser.add_argument('--visible', action='store_true', help='Show browser')

    def handle(self, *args, **options):
        # Implementation details below
        pass
```

**Key functions needed:**

1. `_visit_recent_activity(profile_url)` - Navigate to /recent-activity/comments/
2. `_extract_post_urls()` - Extract all post URLs from activity page
3. `_get_comment_count(post_url)` - Estimate or extract comment count
4. `_queue_post(post_url, comment_count, source_profile)` - Add to Post table

**Algorithm:**

```python
def handle(self, *args, **options):
    # Get profiles that haven't had activity scraped
    profiles = Profile.objects.filter(activity_scraped=False)[:batch_size]
    
    for profile in profiles:
        # Visit /recent-activity/comments/
        activity_url = profile.linkedin_url.rstrip('/') + '/recent-activity/comments/'
        
        # Extract post URLs
        post_urls = extract_post_urls_from_activity(activity_url)
        
        # For each post URL
        for post_url in post_urls:
            # Check comment count (if visible)
            comment_count = estimate_comment_count(post_url)
            
            # Only queue if meets minimum threshold
            if comment_count >= min_comments:
                Post.objects.get_or_create(
                    post_url=post_url,
                    defaults={
                        'comment_count': comment_count,
                        'discovered_from_profile': profile
                    }
                )
        
        # Mark profile as scraped
        profile.activity_scraped = True
        profile.activity_scraped_at = timezone.now()
        profile.posts_discovered_count = len(post_urls)
        profile.save()
```

### Phase 3: Infinite Loop Orchestrator

**File:** `contacts/management/commands/scrape_infinite.py`

Main command that orchestrates the entire loop.

```python
from django.core.management.base import BaseCommand
from django.core.management import call_command
from contacts.models import Post, Profile, Contact
import time

class Command(BaseCommand):
    help = 'Infinite scraping loop - post → profiles → activity → posts → repeat'

    def add_arguments(self, parser):
        parser.add_argument('--seed-url', type=str, required=True, help='Initial post URL')
        parser.add_argument('--max-depth', type=int, default=999, help='Maximum depth levels')
        parser.add_argument('--max-posts', type=int, default=999999, help='Maximum posts to scrape')
        parser.add_argument('--min-comments', type=int, default=100, help='Minimum comments per post')
        parser.add_argument('--delay', type=int, default=5, help='Delay between posts (seconds)')
        parser.add_argument('--batch-size', type=int, default=10, help='Profiles per batch')
        parser.add_argument('--visible', action='store_true', help='Show browser')

    def handle(self, *args, **options):
        # Implementation details below
        pass
```

**Main Loop Algorithm:**

```python
def handle(self, *args, **options):
    seed_url = options['seed_url']
    max_depth = options['max_depth']
    max_posts = options['max_posts']
    min_comments = options['min_comments']
    delay = options['delay']
    batch_size = options['batch_size']
    
    # Add seed URL to Post queue
    Post.objects.get_or_create(
        post_url=seed_url,
        defaults={'comment_count': 9999}
    )
    
    depth = 0
    posts_scraped = 0
    
    while depth < max_depth and posts_scraped < max_posts:
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(f"DEPTH LEVEL: {depth}")
        self.stdout.write(f"{'='*70}\n")
        
        # STAGE 1: Scrape pending posts
        pending_posts = Post.objects.filter(scraped=False)[:batch_size]
        
        if not pending_posts.exists():
            self.stdout.write("No pending posts. Checking for profiles to scrape...")
            
            # STAGE 2: Scrape profile activities
            pending_profiles = Profile.objects.filter(activity_scraped=False)[:batch_size]
            
            if not pending_profiles.exists():
                self.stdout.write("No pending profiles. Loop complete!")
                break
            
            self.stdout.write(f"Scraping activities from {pending_profiles.count()} profiles...")
            
            for profile in pending_profiles:
                call_command(
                    'scrape_profile_activity',
                    profile_url=profile.linkedin_url,
                    min_comments=min_comments,
                    visible=options['visible']
                )
                time.sleep(delay)
            
            continue
        
        self.stdout.write(f"Scraping {pending_posts.count()} posts...")
        
        for post in pending_posts:
            self.stdout.write(f"\nScraping: {post.post_url}")
            
            # Call scrape_all command
            call_command(
                'scrape_all',
                url=post.post_url,
                visible=options['visible']
            )
            
            # Mark as scraped
            post.scraped = True
            post.scraped_at = timezone.now()
            post.save()
            
            posts_scraped += 1
            
            # Delay between posts
            time.sleep(delay)
            
            # Show progress
            profiles_count = Profile.objects.count()
            emails_count = Contact.objects.count()
            pending_count = Post.objects.filter(scraped=False).count()
            
            self.stdout.write(f"Progress: {posts_scraped}/{max_posts} posts scraped")
            self.stdout.write(f"Database: {profiles_count} profiles, {emails_count} emails")
            self.stdout.write(f"Queue: {pending_count} posts pending")
        
        depth += 1
    
    self.stdout.write("\n" + "="*70)
    self.stdout.write("INFINITE SCRAPING COMPLETE")
    self.stdout.write("="*70)
    self.stdout.write(f"Final stats:")
    self.stdout.write(f"  Depth reached: {depth}")
    self.stdout.write(f"  Posts scraped: {posts_scraped}")
    self.stdout.write(f"  Total profiles: {Profile.objects.count()}")
    self.stdout.write(f"  Total emails: {Contact.objects.count()}")
    self.stdout.write(f"  Pending posts: {Post.objects.filter(scraped=False).count()}")
```

### Phase 4: Queue Management Commands

**File:** `contacts/management/commands/queue_stats.py`

Show current queue status:

```python
from django.core.management.base import BaseCommand
from contacts.models import Post, Profile, Contact

class Command(BaseCommand):
    help = 'Show scraping queue statistics'

    def handle(self, *args, **options):
        pending_posts = Post.objects.filter(scraped=False).count()
        scraped_posts = Post.objects.filter(scraped=True).count()
        pending_profiles = Profile.objects.filter(activity_scraped=False).count()
        scraped_profiles = Profile.objects.filter(activity_scraped=True).count()
        
        self.stdout.write("="*70)
        self.stdout.write("QUEUE STATISTICS")
        self.stdout.write("="*70)
        self.stdout.write(f"\nPosts:")
        self.stdout.write(f"  Pending:  {pending_posts}")
        self.stdout.write(f"  Scraped:  {scraped_posts}")
        self.stdout.write(f"  Total:    {pending_posts + scraped_posts}")
        
        self.stdout.write(f"\nProfiles:")
        self.stdout.write(f"  Pending:  {pending_profiles}")
        self.stdout.write(f"  Scraped:  {scraped_profiles}")
        self.stdout.write(f"  Total:    {pending_profiles + scraped_profiles}")
        
        self.stdout.write(f"\nEmails collected: {Contact.objects.count()}")
        
        # Show top posts by comment count
        top_posts = Post.objects.filter(scraped=False).order_by('-comment_count')[:5]
        if top_posts:
            self.stdout.write(f"\nTop pending posts:")
            for post in top_posts:
                self.stdout.write(f"  {post.comment_count} comments - {post.post_url}")
```

**File:** `contacts/management/commands/queue_reset.py`

Reset queue (for testing):

```python
from django.core.management.base import BaseCommand
from contacts.models import Post, Profile

class Command(BaseCommand):
    help = 'Reset scraping queue flags'

    def add_arguments(self, parser):
        parser.add_argument('--posts', action='store_true', help='Reset post scraped flags')
        parser.add_argument('--profiles', action='store_true', help='Reset profile activity flags')
        parser.add_argument('--confirm', action='store_true', help='Confirm reset')

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write("Add --confirm flag to proceed")
            return
        
        if options['posts']:
            count = Post.objects.filter(scraped=True).update(scraped=False, scraped_at=None)
            self.stdout.write(f"Reset {count} posts")
        
        if options['profiles']:
            count = Profile.objects.filter(activity_scraped=True).update(
                activity_scraped=False,
                activity_scraped_at=None
            )
            self.stdout.write(f"Reset {count} profiles")
```

## Usage Examples

### Start Infinite Scraping

```bash
# Basic infinite loop
python manage.py scrape_infinite --seed-url "https://www.linkedin.com/posts/..."

# With limits
python manage.py scrape_infinite \
  --seed-url "https://www.linkedin.com/posts/..." \
  --max-depth 5 \
  --max-posts 100 \
  --min-comments 500

# With visible browser
python manage.py scrape_infinite \
  --seed-url "https://www.linkedin.com/posts/..." \
  --visible \
  --batch-size 5
```

### Check Queue Status

```bash
python manage.py queue_stats
```

### Scrape Profile Activity Only

```bash
# Single profile
python manage.py scrape_profile_activity \
  --profile-url "https://www.linkedin.com/in/example/"

# Batch of pending profiles
python manage.py scrape_profile_activity \
  --batch-size 20 \
  --min-comments 100
```

### Reset Queue (Testing)

```bash
python manage.py queue_reset --posts --confirm
python manage.py queue_reset --profiles --confirm
```

## Smart Features to Implement

### 1. Comment Count Estimation

Since getting exact comment count requires visiting the post, use heuristics:

```python
def estimate_comment_count(post_url):
    """
    Quick estimation without full page load
    - Look for comment count in activity preview
    - Use engagement indicators
    - Default to high value if unknown
    """
    # Try to get from activity page preview
    # Return estimated count or default high value
    return 1000  # Safe default
```

### 2. Duplicate Prevention

```python
# Before adding to queue
post, created = Post.objects.get_or_create(
    post_url=clean_url(post_url),
    defaults={'comment_count': count}
)

if not created and post.scraped:
    # Already scraped, skip
    pass
```

### 3. Priority Queue

```python
# Prioritize posts with higher comment counts
pending_posts = Post.objects.filter(
    scraped=False
).order_by('-comment_count')[:batch_size]
```

### 4. Rate Limiting

```python
import time

# Between posts
time.sleep(delay)

# Between batches
time.sleep(delay * 2)

# Dynamic delay based on response time
if slow_response:
    time.sleep(delay * 3)
```

### 5. Progress Tracking

```python
# Real-time stats
self.stdout.write(f"Depth {depth} | Posts: {scraped}/{total} | Profiles: {new_profiles} | Emails: {new_emails}")

# Estimated time remaining
avg_time_per_post = total_time / posts_scraped
remaining_posts = max_posts - posts_scraped
eta = avg_time_per_post * remaining_posts
```

## Safety Features

### 1. Stop Conditions

```python
# Maximum runtime
if time.time() - start_time > max_runtime_seconds:
    break

# Maximum database size
if Profile.objects.count() > max_profiles:
    break

# No more pending items
if not pending_posts and not pending_profiles:
    break
```

### 2. Error Handling

```python
try:
    call_command('scrape_all', url=post.post_url)
except Exception as e:
    # Log error but continue
    post.scraped = True  # Mark as scraped to avoid retry
    post.save()
    self.stdout.write(f"Error: {str(e)}")
    continue
```

### 3. Interrupt Handling

```python
import signal

def signal_handler(sig, frame):
    self.stdout.write("\nInterrupted by user. Saving state...")
    # Save current progress
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
```

## Performance Optimization

### 1. Batch Processing

```python
# Process multiple profiles in parallel (future enhancement)
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    executor.map(scrape_profile_activity, profile_urls)
```

### 2. Database Indexes

```python
class Meta:
    indexes = [
        models.Index(fields=['scraped', 'comment_count']),
        models.Index(fields=['activity_scraped']),
    ]
```

### 3. Bulk Operations

```python
# Bulk create posts
Post.objects.bulk_create([
    Post(post_url=url, comment_count=count)
    for url, count in posts_data
], ignore_conflicts=True)
```

## Monitoring and Analytics

### Export Loop Statistics

```python
# Export to JSON
{
    "session_id": 1,
    "seed_url": "...",
    "depth_reached": 5,
    "posts_scraped": 150,
    "profiles_discovered": 15000,
    "emails_collected": 1200,
    "runtime_minutes": 480,
    "average_time_per_post": 3.2
}
```

### Visualization Ideas

- Growth curve: posts vs depth level
- Network graph: posts connected by shared profiles
- Heat map: most active profiles
- Timeline: scraping progress over time

## Testing Strategy

### Unit Tests

Test individual components:

```bash
# Test profile activity extraction
python manage.py scrape_profile_activity --profile-url "..." --visible

# Test post queueing
python manage.py shell
>>> from contacts.models import Post
>>> Post.objects.create(post_url="...", comment_count=1000)
```

### Integration Test

Small-scale test:

```bash
python manage.py scrape_infinite \
  --seed-url "..." \
  --max-depth 2 \
  --max-posts 5 \
  --visible
```

### Full Test

Large-scale test with monitoring:

```bash
# Run in screen/tmux
screen -S linkedin_scraper

python manage.py scrape_infinite \
  --seed-url "..." \
  --max-depth 10 \
  --max-posts 1000 \
  --delay 10

# Detach: Ctrl+A, D
# Reattach: screen -r linkedin_scraper
```

## Deployment Considerations

### Production Setup

1. Use PostgreSQL instead of SQLite
2. Set up proper logging
3. Use Celery for background tasks
4. Add monitoring and alerts
5. Implement retry logic
6. Add rate limiting

### Configuration File

Create `scraper_config.py`:

```python
SCRAPER_CONFIG = {
    'MAX_DEPTH': 10,
    'MAX_POSTS': 10000,
    'MIN_COMMENTS': 100,
    'DELAY_SECONDS': 5,
    'BATCH_SIZE': 10,
    'MAX_RUNTIME_HOURS': 24,
    'HEADLESS': True,
}
```

## Troubleshooting

### Common Issues

1. **Too many pending posts**
   - Solution: Increase min_comments threshold
   - Solution: Reduce batch_size

2. **Scraping too slow**
   - Solution: Decrease delay
   - Solution: Increase batch_size
   - Solution: Skip low-value posts

3. **Rate limited**
   - Solution: Increase delay
   - Solution: Use multiple accounts
   - Solution: Pause and resume

4. **Database growing too fast**
   - Solution: Add max_profiles limit
   - Solution: Filter by engagement level
   - Solution: Periodic cleanup

## Next Steps

1. Implement Phase 1: Database models
2. Test with manual queue management
3. Implement Phase 2: Profile activity scraper
4. Test activity scraper with 5-10 profiles
5. Implement Phase 3: Infinite loop orchestrator
6. Test with max-depth 2, max-posts 10
7. Implement Phase 4: Queue management commands
8. Run full test with monitoring
9. Optimize based on results
10. Deploy to production

## Success Metrics

- Posts scraped per hour
- Profiles discovered per hour
- Emails collected per hour
- Success rate (posts scraped / posts attempted)
- Average time per post
- Queue growth rate

## Risk Mitigation

1. **Rate Limiting**: Add exponential backoff
2. **Account Ban**: Rotate accounts, use delays
3. **Infinite Growth**: Set hard limits
4. **Data Quality**: Filter spam, validate emails
5. **Storage**: Implement data pruning strategy

---

**Ready to implement? Start with Phase 1 (Database models) and work your way through!**
