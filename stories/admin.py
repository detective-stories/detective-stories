from django.contrib import admin

from stories.models import Story, Agent


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'description', 'cover_prompt', 'solution',
        'created_at', 'updated_at',
    ]
    search_fields = ('title', 'description')


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'story', 'name', 'prompt',
    ]
    search_fields = ('name', 'prompt')
