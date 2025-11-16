from django.conf import settings
from django.db import models
from django.utils import timezone

class Category(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("user", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name

class Tag(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tags"
    )
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ("user", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name

class Link(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="links",
    )
    original_url = models.URLField(max_length=1000)
    short_code = models.CharField(max_length=16, unique=True, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="links"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="links")
    clicks_count = models.PositiveIntegerField(default=0)
    is_alive = models.BooleanField(default=True)
    last_check_status = models.IntegerField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.short_code} → {self.original_url}"

class ClickEvent(models.Model):
    link = models.ForeignKey(Link, on_delete=models.CASCADE, related_name="clicks")
    occurred_at = models.DateTimeField(default=timezone.now)
    referrer = models.CharField(max_length=1000, blank=True)
    user_agent = models.CharField(max_length=1000, blank=True)
    device_type = models.CharField(max_length=16, blank=True)
    os = models.CharField(max_length=32, blank=True)
    browser = models.CharField(max_length=32, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-occurred_at"]