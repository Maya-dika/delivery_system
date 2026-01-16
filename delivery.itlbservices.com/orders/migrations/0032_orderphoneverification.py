from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0031_alter_order_effective_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderPhoneVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=32)),
                ('code', models.CharField(max_length=12)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('verified', 'Verified'), ('expired', 'Expired'), ('failed', 'Failed')], default='pending', max_length=16)),
                ('attempts', models.PositiveIntegerField(default=0)),
                ('expires_at', models.DateTimeField()),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_sent_at', models.DateTimeField(blank=True, null=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phone_verifications', to='orders.order')),
            ],
        ),
        migrations.AddIndex(
            model_name='orderphoneverification',
            index=models.Index(fields=['order', 'status'], name='orders_order_status_idx'),
        ),
    ]

