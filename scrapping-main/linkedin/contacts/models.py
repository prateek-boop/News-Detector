from django.db import models

class Contact(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.email}" if self.name else self.email


class Profile(models.Model):
    contact = models.OneToOneField(
        Contact, 
        on_delete=models.CASCADE, 
        related_name='profile',
        null=True,
        blank=True
    )
    
    # Core profile data
    linkedin_url = models.URLField(unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    headline = models.CharField(max_length=500, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    
    # Professional info
    current_company = models.CharField(max_length=255, blank=True, null=True)
    current_position = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    
    # Social metrics
    connections = models.IntegerField(blank=True, null=True)
    followers = models.IntegerField(blank=True, null=True)
    
    # Additional data
    about = models.TextField(blank=True, null=True)
    profile_image_url = models.URLField(blank=True, null=True)
    
    # Metadata
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    
    # Activity tracking for infinite loop scraper
    activity_scraped = models.BooleanField(default=False)
    activity_scraped_at = models.DateTimeField(null=True, blank=True)
    posts_discovered_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-scraped_at']
    
    def __str__(self):
        return f"{self.full_name or 'Unknown'} - {self.linkedin_url}"


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
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-comment_count', '-created_at']
        indexes = [
            models.Index(fields=['scraped', 'comment_count']),
            models.Index(fields=['post_url']),
        ]
    
    def __str__(self):
        status = "✓ Scraped" if self.scraped else "⏳ Queued"
        count = f"{self.comment_count} comments" if self.comment_count else "Unknown comments"
        return f"{status} - {count} - {self.post_url[:60]}"


class ScrapingSession(models.Model):
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    seed_url = models.URLField()
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    depth_level = models.IntegerField(default=0)
    posts_scraped = models.IntegerField(default=0)
    profiles_scraped = models.IntegerField(default=0)
    emails_collected = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='running'
    )
    
    # Safety limits
    max_posts = models.IntegerField(default=1000)
    max_depth = models.IntegerField(default=3)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Session {self.id} - {self.status} - Level {self.depth_level} - {self.posts_scraped} posts"
