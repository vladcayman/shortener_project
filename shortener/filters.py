import django_filters
from django.db.models import Q

from .models import Link

class LinkFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search", label="Search")

    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("clicks_count", "clicks_count"),
        )
    )

    class Meta:
        model = Link
        fields = ("category", "tags", "is_alive")

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(original_url__icontains=value)
            | Q(title__icontains=value)
            | Q(short_code__icontains=value)
        )