from django.db.models.query import QuerySet
from django_workflow_engine.exceptions import WorkflowNotAuthError
from django_workflow_engine.executor import WorkflowExecutor
from django_workflow_engine.models import Flow

from activity_stream.utils import ingest_activity_stream
from celery import shared_task
from config.celery import celery_app
from core.people_data.utils import ingest_people_data
from core.people_finder.utils import ingest_people_finder
from core.service_now.utils import ingest_service_now
from core.utils.staff_index import (
    index_sso_users,
    update_all_staff_documents_with_a_uuid,
)

logger = celery_app.log.get_default_logger()


@celery_app.task(bind=True)
def debug_task(self):
    logger.info("RUNNING debug_task")
    print("Request: {0!r}".format(self.request))


@celery_app.task(bind=True)
def progress_workflows(self):
    logger.info("RUNNING progress_workflows")
    in_progress_flows: QuerySet[Flow] = Flow.objects.filter(finished__isnull=True)
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


@celery_app.task(bind=True)
def staff_document_uuid_task(self, flow_pk: str):
    update_all_staff_documents_with_a_uuid()


ingest_activity_stream_task = shared_task(ingest_activity_stream)
index_sso_users_task = shared_task(index_sso_users)
ingest_people_data_task = shared_task(ingest_people_data)
ingest_people_finder_task = shared_task(ingest_people_finder)
ingest_service_now_task = shared_task(ingest_service_now)
