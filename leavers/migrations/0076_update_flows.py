from django.db import migrations


def update_workflows(apps, schema_editor):
    """
    Update Workflows to contain the new step.
    """
    from django_workflow_engine.executor import WorkflowExecutor
    from django_workflow_engine.utils import lookup_workflow

    Flow = apps.get_model("django_workflow_engine", "Flow")
    TaskRecord = apps.get_model("django_workflow_engine", "TaskRecord")

    for flow in Flow.objects.all().filter(
        workflow_name="leaving", finished__isnull=True
    ):
        # If setup_scheduled_tasks has been executed, then we need to add the new step.
        if not flow.tasks.filter(
            step_id="setup_scheduled_tasks", executed_at__isnull=False
        ).exists():
            break

        workflow = lookup_workflow(flow.workflow_name)

        new_step = None
        for step in workflow.steps:
            if step.step_id == "should_notify_comea_team":
                new_step = step
                break

        if new_step is None:
            raise Exception("Step not found")

        TaskRecord.objects.create(
            flow=flow,
            task_name=new_step.task_name,
            step_id=new_step.step_id,
            executed_by=None,
            executed_at=None,
            task_info=new_step.task_info or {},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0075_update_task_info"),
    ]

    operations = [
        migrations.RunPython(update_workflows, migrations.RunPython.noop),
    ]
