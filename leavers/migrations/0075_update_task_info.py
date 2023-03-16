from django.db import migrations

from leavers.workflow.tasks import SkipCondition


def update_task_info(apps, schema_editor):
    """
    Update task info so skip_condition takes a list instead of a string.
    """

    TaskRecord = apps.get_model("django_workflow_engine", "TaskRecord")

    for task_record in TaskRecord.objects.all().filter(executed_at__isnull=True):
        if "skip_condition" in task_record.task_info:
            task_record.task_info["skip_conditions"] = [
                task_record.task_info["skip_condition"]
            ]
            del task_record.task_info["skip_condition"]
            task_record.save()


class Migration(migrations.Migration):
    dependencies = [
        ("leavers", "0074_alter_leavingrequest_reason_for_leaving"),
    ]
    run_before = [
        ("django_workflow_engine", "0008_remove_taskrecord_broke_flow"),
    ]

    operations = [
        migrations.RunPython(update_task_info, migrations.RunPython.noop),
    ]
