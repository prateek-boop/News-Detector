from django.db import models

class Hackathon(models.Model):
    name = models.CharField(max_length=500)
    url = models.URLField(unique=True)
    organizer = models.CharField(max_length=500, blank=True, null=True)
    registered_count = models.CharField(max_length=100, blank=True, null=True)
    impression_count = models.CharField(max_length=100, blank=True, null=True)
    registration_count = models.CharField(max_length=100, blank=True, null=True)
    about_content = models.TextField(blank=True, null=True)
    organizer_contact = models.TextField(blank=True, null=True)
    important_dates = models.TextField(blank=True, null=True)
    official_website = models.URLField(blank=True, null=True)
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scraped_at']
    
    def __str__(self):
        return self.name

class Competition(models.Model):
    name = models.CharField(max_length=500)
    url = models.URLField(unique=True)
    organizer = models.CharField(max_length=500, blank=True, null=True)
    registered_count = models.CharField(max_length=100, blank=True, null=True)
    impression_count = models.CharField(max_length=100, blank=True, null=True)
    registration_count = models.CharField(max_length=100, blank=True, null=True)
    about_content = models.TextField(blank=True, null=True)
    organizer_contact = models.TextField(blank=True, null=True)
    important_dates = models.TextField(blank=True, null=True)
    official_website = models.URLField(blank=True, null=True)
    prizes = models.TextField(blank=True, null=True)
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scraped_at']
    
    def __str__(self):
        return self.name

class DevfolioHackathon(models.Model):
    name = models.CharField(max_length=500)
    url = models.URLField(unique=True)
    organizer = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)  # open, past, upcoming
    participants_count = models.CharField(max_length=100, blank=True, null=True)
    projects_count = models.CharField(max_length=100, blank=True, null=True)
    about_content = models.TextField(blank=True, null=True)
    organizer_contact = models.TextField(blank=True, null=True)
    important_dates = models.TextField(blank=True, null=True)
    start_date = models.CharField(max_length=200, blank=True, null=True)
    end_date = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=500, blank=True, null=True)
    mode = models.CharField(max_length=100, blank=True, null=True)  # online, offline, hybrid
    prizes = models.TextField(blank=True, null=True)
    themes = models.TextField(blank=True, null=True)
    official_website = models.URLField(blank=True, null=True)
    telegram_link = models.URLField(blank=True, null=True)
    discord_link = models.URLField(blank=True, null=True)
    linkedin_link = models.URLField(blank=True, null=True)
    twitter_link = models.URLField(blank=True, null=True)
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scraped_at']
    
    def __str__(self):
        return self.name

class DevpostHackathon(models.Model):
    name = models.CharField(max_length=500)
    url = models.URLField(unique=True)
    organizer = models.CharField(max_length=500, blank=True, null=True)
    participants_count = models.CharField(max_length=100, blank=True, null=True)
    about_content = models.TextField(blank=True, null=True)
    organizer_contact = models.TextField(blank=True, null=True)
    sponsors = models.TextField(blank=True, null=True)
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scraped_at']
    
    def __str__(self):
        return self.name
