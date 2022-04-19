from django_workflow_engine.exceptions import WorkflowNotAuthError
from django_workflow_engine.executor import WorkflowExecutor
from django_workflow_engine.models import Flow

from core.celery import celery_app

logger = celery_app.log.get_default_logger()


@celery_app.task(bind=True)
def debug_task(self):
    logger.info("RUNNING debug_task")
    print("Request: {0!r}".format(self.request))


@celery_app.task(bind=True)
def progress_workflows(self):
    logger.info("RUNNING progress_workflows")
    in_progress_flows = Flow.objects.filter(finished__isnull=True)
    for flow in in_progress_flows:
        progress_workflow.delay(flow_pk=flow.pk)
    logger.info(f"Triggered {in_progress_flows.count()} workflows")


@celery_app.task(bind=True)
def progress_workflow(self, flow_pk: str):
    logger.info(f"RUNNING progress_workflow {flow_pk=}")
    # Get workflow from task
    flow: Flow = Flow.objects.get(pk=flow_pk)
    if not flow.is_complete:
        executor = WorkflowExecutor(flow)
        try:
            executor.run_flow(user=None)
        except WorkflowNotAuthError as e:
            logger.warning(f"{e}")
