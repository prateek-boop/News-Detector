from django.contrib import admin
from .models import DorkQuery, CrawledLink

@admin.register(DorkQuery)
class DorkQueryAdmin(admin.ModelAdmin):
    list_display = ['query', 'description', 'is_active', 'last_crawled', 'created_at', 'link_count']
    list_filter = ['is_active', 'last_crawled', 'created_at']
    search_fields = ['query', 'description']
    readonly_fields = ['created_at', 'last_crawled']
    
    def link_count(self, obj):
        return obj.links.count()
    link_count.short_description = 'Links Found'

@admin.register(CrawledLink)
class CrawledLinkAdmin(admin.ModelAdmin):
    list_display = ['url', 'title', 'dork_query', 'page_number', 'position', 'found_at']
    list_filter = ['dork_query', 'page_number', 'found_at']
    search_fields = ['url', 'title', 'snippet']
    readonly_fields = ['found_at']
