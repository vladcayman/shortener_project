from rest_framework import serializers
from .models import Category, Tag, Link

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]

class LinkSerializer(serializers.ModelSerializer):
    category = CategorySerializer(required=False, allow_null=True)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Link
        fields = [
            "id", "original_url", "short_code", "title",
            "category", "tags",
            "clicks_count", "is_alive", "last_check_status",
            "last_checked_at", "created_at",
        ]
        read_only_fields = ["short_code", "clicks_count", "is_alive",
                            "last_check_status", "last_checked_at", "created_at"]

    def _get_or_create_category(self, category_data, user):
        if not category_data:
            return None
        obj, _ = Category.objects.get_or_create(user=user, name=category_data["name"])
        return obj

    def _get_or_create_tags(self, tags_data, user):
        tags = []
        for item in tags_data or []:
            obj, _ = Tag.objects.get_or_create(user=user, name=item["name"])
            tags.append(obj)
        return tags

    def create(self, validated_data):
        user = self.context["request"].user
        cat_data = validated_data.pop("category", None)
        tags_data = validated_data.pop("tags", [])
        link = Link.objects.create(owner=user, **validated_data)
        link.category = self._get_or_create_category(cat_data, user) if user.is_authenticated else None
        link.save()
        if user.is_authenticated:
            link.tags.set(self._get_or_create_tags(tags_data, user))
        return link

    def update(self, instance, validated_data):
        user = self.context["request"].user
        cat_data = validated_data.pop("category", None)
        tags_data = validated_data.pop("tags", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)

        if cat_data is not None:
            instance.category = self._get_or_create_category(cat_data, user) if user.is_authenticated else None

        instance.save()

        if tags_data is not None and user.is_authenticated:
            instance.tags.set(self._get_or_create_tags(tags_data, user))

        return instance

class PublicShortenSerializer(serializers.Serializer):
    original_url = serializers.URLField(max_length=1000)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)