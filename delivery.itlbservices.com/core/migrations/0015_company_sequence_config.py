from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_alter_warehouse_warehouse_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='order_prefix',
            field=models.CharField(blank=True, default='', help_text='Optional static prefix for Orders (will be prepended before country code)', max_length=10),
        ),
        migrations.AddField(
            model_name='company',
            name='order_request_prefix',
            field=models.CharField(default='RQ', max_length=10),
        ),
        migrations.AddField(
            model_name='company',
            name='order_request_seq_length',
            field=models.PositiveIntegerField(default=5, help_text='Digits for Order Request sequence (excluding prefix)'),
        ),
        migrations.AddField(
            model_name='company',
            name='order_seq_length',
            field=models.PositiveIntegerField(default=6, help_text='Digits for Order sequence (excluding prefix)'),
        ),
    ]

