from django.db import migrations


def migrate_workflows(apps, schema_editor):
    """
    Migrate paused workflows
    """
    TaskRecord = apps.get_model("django_workflow_engine", "TaskRecord")
    TaskRecord.objects.all().filter(
        executed_at__isnull=True, step_id="setup_scheduled_tasks"
    ).exclude(task_name="basic_task").update(task_name="basic_task")


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0055_auto_20220823_1350"),
    ]

    operations = [
        migrations.RunPython(migrate_workflows, migrations.RunPython.noop),
    ]
