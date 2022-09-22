from django.db import migrations

from leavers.workflow.tasks import SkipCondition


def update_uksbs_task_info(apps, schema_editor):
    TaskRecord = apps.get_model("django_workflow_engine", "TaskRecord")

    # Defined in leavers/workflow/leaving.py::LeaversWorkflow step
    # "send_uksbs_leaver_details"
    task_info = {
        "skip_condition": SkipCondition.MANUALLY_OFFBOARDED_FROM_UKSBS.value,
    }

    for task_record in TaskRecord.objects.all().filter(
        executed_at__isnull=True, step_id="send_uksbs_leaver_details"
    ):
        if task_record.task_info == {}:
            task_record.task_info = task_info
            task_record.save()


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0057_leavingrequest_manually_offboarded_from_uksbs"),
    ]

    operations = [
        migrations.RunPython(update_uksbs_task_info, migrations.RunPython.noop),
    ]
