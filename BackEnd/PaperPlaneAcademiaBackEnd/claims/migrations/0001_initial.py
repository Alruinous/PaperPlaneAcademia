# Generated by Django 3.2 on 2024-12-23 09:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authors', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Claim',
            fields=[
                ('claim_id', models.AutoField(primary_key=True, serialize=False)),
                ('send_time', models.DateTimeField(auto_now_add=True)),
                ('process_time', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(default='Pending', max_length=50)),
                ('claim_author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='claim_author', to='authors.author')),
                ('claim_sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='claim_sender', to='users.user')),
            ],
        ),
    ]
