from django.db import models
from django.utils.timesince import timesince
from accounts.models import User

# Create your models here.

class Like(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Like by {self.created_by.username} on {self.created_at}"

class Comment(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    @property
    def time_since_updated(self):
        return timesince(self.updated_at) + " ago"
    
    @property
    def time_since_created(self):
        return timesince(self.created_at) + " ago"

    def __str__(self):
        return f"Comment by {self.created_by.username} on {self.created_at}"

class PostAttachment(models.Model):
    image = models.ImageField(upload_to="posts/attachments")
    video = models.FileField(upload_to="posts/videos", blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Attachment by {self.created_by.username} on {self.created_at}"

class Post(models.Model):

    ROLE = (
        ("only_me", "only_me"),
        ("public", "public"),
    )

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    likes = models.ManyToManyField(Like, blank=True)
    likes_count = models.IntegerField(default=0)
    comments = models.ManyToManyField(Comment, blank=True)
    comments_count = models.IntegerField(default=0)
    content = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE, default="public")
    attachments = models.ManyToManyField(PostAttachment, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    @property
    def time_since_created(self):
        return timesince(self.created_at) + " ago"
    
    @property
    def time_since_updated(self):
        return timesince(self.updated_at) + " ago"

    def __str__(self):
        return self.created_by.username + " - " + str(self.created_at)
