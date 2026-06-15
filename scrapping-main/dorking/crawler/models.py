from django.db import models

class DorkQuery(models.Model):
    query = models.TextField(unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_crawled = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.query
    
    class Meta:
        ordering = ['-created_at']

class CrawledLink(models.Model):
    dork_query = models.ForeignKey(DorkQuery, on_delete=models.CASCADE, related_name='links')
    url = models.URLField(max_length=2048)
    title = models.CharField(max_length=512, blank=True)
    snippet = models.TextField(blank=True)
    position = models.IntegerField()
    page_number = models.IntegerField(default=1)
    found_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.url} (Page {self.page_number}, Pos {self.position})"
    
    class Meta:
        ordering = ['dork_query', 'page_number', 'position']
        unique_together = ['dork_query', 'url']
