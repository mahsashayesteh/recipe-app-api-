
from rest_framework import serializers
from core.models import Recipe, Tag, Ingredient

class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient"""

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_field = ['id']

class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags. """

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_field = ['id']



class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for list recipe. """
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
       model = Recipe
       fields = [
           'id', 'title', 'price', 'time_minutes', 'link', 'tags',
           'ingredients'
           ]
       read_only_field = ['id',]
    
    def _get_or_created_tags(self, tags, recipe):
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user = auth_user,
                **tag
            )
            
            recipe.tags.add(tag_obj)
    
    def _get_or_create_ingredients(self, ingredients, recipe):
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                user=auth_user, 
                **ingredient
            )
            recipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        ingredient = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_created_tags(tags, recipe)
        self._get_or_create_ingredients(ingredient, recipe)

        return recipe
    
    def update(self, instance, validated_data):
        """update recipe"""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_created_tags(tags, instance)
        
        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for details recipe. """
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description', 'image']

class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading image to recipes"""

    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_field = ['id']
        extra_kwargs = {'image':{'required':'True'}}

    


