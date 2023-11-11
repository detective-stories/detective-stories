from __future__ import annotations

from django.db import models


class Story(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=256)
    description = models.TextField()  # story description
    cover_prompt = models.CharField(max_length=1024)  # prompt for the cover image that will be shown with the story
    solution = models.TextField()  # story solution that will be shown after the story is solved

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # show agents that are linked to this story
    def agents(self):
        return Agent.objects.filter(story=self)

    def __str__(self):
        return f'{self.title} ({self.id})'


class Agent(models.Model):
    id = models.AutoField(primary_key=True)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    prompt = models.TextField()
