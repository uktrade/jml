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
            continue

        for send_sre_reminder_task in send_sre_reminder_tasks:
            processor_emails = send_sre_reminder_task.task_info.get(
                "processor_emails",
                [],
            )
            if settings.SRE_EMAIL in processor_emails:
                # Already updated
                continue
            task_pks_to_update.append(send_sre_reminder_task.pk)

    task_pks_to_update = list(set(task_pks_to_update))
    Flow.objects.filter(tasks__pk__in=task_pks_to_update).update(
        task_info__processor_emails=[settings.SRE_EMAIL],
    )


class Migration(migrations.Migration):
    dependencies = [
        ("leavers", "0095_leavingrequest_cancelled"),
    ]

    operations = [
        migrations.RunPython(update_workflows, migrations.RunPython.noop),
    ]
