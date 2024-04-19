from django.conf import settings
from django.db.models.query import QuerySet
from django_workflow_engine.exceptions import WorkflowNotAuthError
from django_workflow_engine.executor import WorkflowExecutor
from django_workflow_engine.models import Flow

from activity_stream.utils import ingest_activity_stream
from config.celery import celery_app
from core.people_data.utils import ingest_people_data
from core.people_finder.utils import ingest_people_finder
from core.service_now.utils import ingest_service_now
from core.utils.staff_index import index_sso_users

logger = celery_app.log.get_default_logger()


@celery_app.task(bind=True)
def debug_task(self):
    logger.info("RUNNING debug_task")
    print("Request: {0!r}".format(self.request))


@celery_app.task(bind=True)
def progress_workflows(self):
    if not settings.RUN_DJANGO_WORKFLOWS:
        logger.info("RUNNING progress_workflows - disabled")
        return None

    logger.info("RUNNING progress_workflows")
    in_progress_flows: QuerySet[Flow] = Flow.objects.filter(finished__isnull=True)
    for flow in in_progress_flows:
        progress_workflow.delay(flow_pk=flow.pk)
    logger.info(f"Triggered {in_progress_flows.count()} workflows")


@celery_app.task(bind=True)
def progress_workflow(self, flow_pk: str):
    if not settings.RUN_DJANGO_WORKFLOWS:
        logger.info(f"RUNNING progress_workflow {flow_pk=} - disabled")
        return None

    logger.info(f"RUNNING progress_workflow {flow_pk=}")
    # Get workflow from task
    flow: Flow = Flow.objects.get(pk=flow_pk)
    request_cancelled = False
    if request := getattr(flow, "leaving_request"):
        request_cancelled = request.cancelled

    if not request_cancelled and not flow.is_complete:
        executor = WorkflowExecutor(flow)
        try:
            executor.run_flow(user=None)
        except WorkflowNotAuthError as e:
            logger.warning(f"{e}")


@celery_app.task(bind=True)
def ingest_activity_stream_task(self):
    logger.info("RUNNING ingest_activity_stream_task")
    ingest_activity_stream()


@celery_app.task(bind=True)
def index_sso_users_task(self):
    logger.info("RUNNING index_sso_users_task")
    index_sso_users()


@celery_app.task(bind=True)
def ingest_people_data_task(self):
    logger.info("RUNNING ingest_people_data_task")
    ingest_people_data()


@celery_app.task(bind=True)
def ingest_people_finder_task(self):
    logger.info("RUNNING ingest_people_finder_task")
    ingest_people_finder()


@celery_app.task(bind=True)
def ingest_service_now_task(self):
    service_now_online: bool = settings.SERVICE_NOW_ENABLE_ONLINE_PROCESS
    logger.info(f"RUNNING ingest_service_now_task {service_now_online=}")

    if service_now_online:
        ingest_service_now()
