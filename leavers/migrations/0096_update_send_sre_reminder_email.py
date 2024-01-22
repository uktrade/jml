from django.conf import settings
from django.db import migrations


def update_workflows(apps, schema_editor):
    """
    Update send_sre_reminder emails to the new setting
    """

    Flow = apps.get_model("django_workflow_engine", "Flow")

    task_pks_to_update = []

    in_progress_flows = Flow.objects.all().filter(
        workflow_name="leaving",
        # Workflow is in progress
        finished__isnull=True,
        # Has a task with the send_sre_reminder step id
        tasks__step_id="send_sre_reminder",
    )
    for flow in in_progress_flows:
        send_sre_reminder_tasks = flow.tasks.filter(
            done=False,
            step_id="send_sre_reminder",
        )
        if not send_sre_reminder_tasks:
            # No tasks to update
            continue

        for send_sre_reminder_task in send_sre_reminder_tasks:
            task_info = send_sre_reminder_task.task_info
            if not task_info or "processor_emails" not in task_info:
                # Nothing to update
                continue
            if settings.SRE_EMAIL in task_info["processor_emails"]:
                # Already updated
                continue

            task_info["processor_emails"] = [
                settings.SRE_EMAIL,
            ]
            send_sre_reminder_task.task_info = task_info
            send_sre_reminder_task.save(update_fields=["task_info"])


class Migration(migrations.Migration):
    dependencies = [
        ("leavers", "0095_leavingrequest_cancelled"),
    ]

    operations = [
        migrations.RunPython(update_workflows, migrations.RunPython.noop),
    ]
