from django.contrib import admin
from .models import Contact, Profile, Post, ScrapingSession

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'has_profile', 'created_at', 'updated_at']
    search_fields = ['email', 'name']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_profile(self, obj):
        return hasattr(obj, 'profile')
    has_profile.boolean = True
    has_profile.short_description = 'Has Profile'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['linkedin_url', 'has_contact', 'activity_scraped', 'posts_discovered_count', 'scraped_at']
    search_fields = ['linkedin_url']
    list_filter = ['scraped_at', 'activity_scraped']
    readonly_fields = ['scraped_at', 'updated_at', 'activity_scraped_at']
    
    def has_contact(self, obj):
        return obj.contact is not None
    has_contact.boolean = True
    has_contact.short_description = 'Has Contact'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['short_url', 'comment_count', 'scraped', 'discovered_from', 'created_at']
    list_filter = ['scraped', 'created_at']
    search_fields = ['post_url']
    readonly_fields = ['created_at', 'updated_at', 'scraped_at']
    ordering = ['-comment_count', '-created_at']
    
    def short_url(self, obj):
        return obj.post_url[:80] + '...' if len(obj.post_url) > 80 else obj.post_url
    short_url.short_description = 'Post URL'
    
    def discovered_from(self, obj):
        if obj.discovered_from_profile:
            return obj.discovered_from_profile.linkedin_url[:50]
        return '-'
    discovered_from.short_description = 'Discovered From'


@admin.register(ScrapingSession)
class ScrapingSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'depth_level', 'posts_scraped', 'profiles_scraped', 'emails_collected', 'started_at']
    list_filter = ['status', 'started_at']
    readonly_fields = ['started_at', 'ended_at']
    ordering = ['-started_at']
