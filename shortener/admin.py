from django.contrib import admin
from .models import Category, Tag, Link, ClickEvent


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "links_count")
    search_fields = ("name",)
    ordering = ("name",)

    def links_count(self, obj):
        return obj.links.count()

    links_count.short_description = "Кол-во ссылок"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "links_count")
    search_fields = ("name",)
    ordering = ("name",)

    def links_count(self, obj):
        return obj.links.count()

    links_count.short_description = "Кол-во ссылок"


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = (
        "short_code",
        "title",
        "original_url",
        "category",
        "clicks_count",
        "is_alive",
        "created_at",
    )
    list_filter = ("is_alive", "category", "tags", "created_at")
    search_fields = ("short_code", "title", "original_url")
    readonly_fields = ("clicks_count", "created_at")
    filter_horizontal = ("tags",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ("link", "occurred_at", "device_type", "os", "browser", "ip_address")
    search_fields = ("link__short_code", "link__original_url")
