from django.db import migrations


def update_workflows(apps, schema_editor):
    """
    Update Workflows migrate away from the removed steps.
    """
    from django_workflow_engine.executor import WorkflowExecutor
    from django_workflow_engine.utils import lookup_workflow

    Flow = apps.get_model("django_workflow_engine", "Flow")
    TaskRecord = apps.get_model("django_workflow_engine", "TaskRecord")

    for flow in Flow.objects.all().filter(
        workflow_name="leaving", finished__isnull=True
    ):
        sre_tasks = flow.tasks.filter(
            step_id__in=["send_sre_notification", "send_sre_slack_message"],
            executed_at__isnull=True,
        )
        if not sre_tasks.exists():
            break

        workflow = lookup_workflow(flow.workflow_name)

        next_step = None
        for step in workflow.steps:
            if step.step_id == "have_sre_carried_out_leaving_tasks":
                next_step = step
                break

        if next_step is None:
            raise Exception("Step not found")

        TaskRecord.objects.create(
            flow=flow,
            task_name=next_step.task_name,
            step_id=next_step.step_id,
            executed_by=None,
            executed_at=None,
            task_info=next_step.task_info or {},
        )

        sre_tasks.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("leavers", "0085_leaverinformation_has_cirrus_kit"),
    ]
    run_before = [
        ("django_workflow_engine", "0008_remove_taskrecord_broke_flow"),
    ]

    operations = [
        migrations.RunPython(update_workflows, migrations.RunPython.noop),
    ]
