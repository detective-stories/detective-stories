from django.contrib import admin

from stories.models import (
    Story,
    Agent,
    StoryCompletion,
    AgentInteraction,
    AgentInteractionMessage,
)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "prelude",
        "cover_image_url",
        "extensive_solution",
        "created_at",
        "updated_at",
    ]
    search_fields = ("title", "prelude")


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "story",
        "name",
        "background",
        "hidden",
        "alibi",
        "character",
        "relationships",
        "knowledge",
    ]
    search_fields = ("name", "background")


@admin.register(StoryCompletion)
class StoryCompletionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "story",
        "state",
        "created_at",
        "updated_at",
        "completed_at",
        "score",
    ]
    search_fields = ("user", "story")


@admin.register(AgentInteraction)
class AgentInteractionAdmin(admin.ModelAdmin):
    list_display = ["id", "story_completion", "agent"]
    search_fields = ("agent",)


@admin.register(AgentInteractionMessage)
class AgentInteractionMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "agent_interaction", "message", "role"]
    search_fields = ("agent_interaction", "role", "message")
