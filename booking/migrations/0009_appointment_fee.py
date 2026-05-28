from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0008_remove_appointment_pain_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='fee',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
