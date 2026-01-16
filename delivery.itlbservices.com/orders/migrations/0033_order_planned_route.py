from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0032_orderphoneverification'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='planned_route',
            field=models.JSONField(blank=True, default=list),
        ),
    ]

