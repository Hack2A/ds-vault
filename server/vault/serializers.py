from rest_framework import serializers


class StoreItemSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    body = serializers.CharField()
    is_adv = serializers.BooleanField(default=False)
    seed_phrase = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        if attrs.get('is_adv') and not attrs.get('seed_phrase', '').strip():
            raise serializers.ValidationError(
                {"seed_phrase": "seed_phrase is required for advanced mode."}
            )
        return attrs
