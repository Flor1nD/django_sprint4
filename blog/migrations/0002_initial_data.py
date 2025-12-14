from django.db import migrations


def create_initial_categories(apps, schema_editor):
    Category = apps.get_model('blog', 'Category')

    categories = [
        {
            'title': 'Путешествия',
            'description': 'Статьи о путешествиях и приключениях',
            'slug': 'travel',
            'is_published': True,
        },
        {
            'title': 'Технологии',
            'description': 'Новости и статьи о технологиях',
            'slug': 'technology',
            'is_published': True,
        },
        {
            'title': 'Кулинария',
            'description': 'Рецепты и кулинарные советы',
            'slug': 'cooking',
            'is_published': True,
        },
        {
            'title': 'Спорт',
            'description': 'Новости и статьи о спорте',
            'slug': 'sports',
            'is_published': True,
        },
        {
            'title': 'Искусство',
            'description': 'Статьи об искусстве и культуре',
            'slug': 'art',
            'is_published': True,
        },
    ]

    for category_data in categories:
        Category.objects.get_or_create(**category_data)


def create_initial_locations(apps, schema_editor):
    Location = apps.get_model('blog', 'Location')

    locations = [
        {'name': 'Москва', 'is_published': True},
        {'name': 'Санкт-Петербург', 'is_published': True},
        {'name': 'Новосибирск', 'is_published': True},
        {'name': 'Екатеринбург', 'is_published': True},
        {'name': 'Казань', 'is_published': True},
        {'name': 'Нижний Новгород', 'is_published': True},
        {'name': 'Челябинск', 'is_published': True},
        {'name': 'Самара', 'is_published': True},
        {'name': 'Омск', 'is_published': True},
        {'name': 'Ростов-на-Дону', 'is_published': True},
    ]

    for location_data in locations:
        Location.objects.get_or_create(**location_data)


class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_categories),
        migrations.RunPython(create_initial_locations),
    ]
