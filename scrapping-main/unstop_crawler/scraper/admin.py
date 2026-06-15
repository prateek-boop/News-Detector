from django.contrib import admin
from .models import Hackathon, Competition, DevfolioHackathon

@admin.register(Hackathon)
class HackathonAdmin(admin.ModelAdmin):
    list_display = ['name', 'organizer', 'registered_count', 'scraped_at']
    list_filter = ['scraped_at', 'organizer']
    search_fields = ['name', 'organizer', 'url']
    readonly_fields = ['scraped_at', 'updated_at']
    ordering = ['-scraped_at']

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'organizer', 'registered_count', 'scraped_at']
    list_filter = ['scraped_at', 'organizer']
    search_fields = ['name', 'organizer', 'url']
    readonly_fields = ['scraped_at', 'updated_at']
    ordering = ['-scraped_at']

@admin.register(DevfolioHackathon)
class DevfolioHackathonAdmin(admin.ModelAdmin):
    list_display = ['name', 'organizer', 'status', 'participants_count', 'location', 'scraped_at']
    list_filter = ['status', 'scraped_at', 'organizer', 'mode']
    search_fields = ['name', 'organizer', 'url', 'location']
    readonly_fields = ['scraped_at', 'updated_at']
    ordering = ['-scraped_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'url', 'organizer', 'status')
        }),
        ('Participation Stats', {
            'fields': ('participants_count', 'projects_count')
        }),
        ('Event Details', {
            'fields': ('start_date', 'end_date', 'location', 'mode')
        }),
        ('Content', {
            'fields': ('about_content', 'prizes', 'themes')
        }),
        ('Contact & Links', {
            'fields': ('organizer_contact', 'official_website', 'important_dates')
        }),
        ('Timestamps', {
            'fields': ('scraped_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
