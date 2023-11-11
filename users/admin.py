from django.contrib import admin

from users.models import Location
from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'user_id', 'username', 'first_name', 'last_name', 
        'language_code', 'deep_link',
        'created_at', 'updated_at', "is_blocked_bot",
    ]
    list_filter = ["is_blocked_bot", ]
    search_fields = ('username', 'user_id')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'created_at']
