from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_company_sequence_config'),
    ]

    operations = [
        migrations.CreateModel(
            name='NumberSequence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=50)),
                ('last_number', models.PositiveIntegerField(default=0)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sequences', to='core.company')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='numbersequence',
            unique_together={('company', 'key')},
        ),
    ]

