# from django.db.models.query import QuerySet
# from django_workflow_engine.exceptions import WorkflowNotAuthError
# from django_workflow_engine.executor import WorkflowExecutor
# from django_workflow_engine.models import Flow

# from activity_stream.utils import ingest_activity_stream
from config.celery import celery_app

# from core.people_finder.utils import ingest_people_finder
# from core.service_now.utils import ingest_service_now

logger = celery_app.log.get_default_logger()


@celery_app.task(bind=True)
def debug_task(self):
    logger.info("RUNNING debug_task")
    print("Request: {0!r}".format(self.request))


# @celery_app.task(bind=True)
# def progress_workflows(self):
#     logger.info("RUNNING progress_workflows")
#     in_progress_flows: QuerySet[Flow] = Flow.objects.filter(finished__isnull=True)
#     for flow in in_progress_flows:
#         progress_workflow.delay(flow_pk=flow.pk)
#     logger.info(f"Triggered {in_progress_flows.count()} workflows")


# @celery_app.task(bind=True)
# def progress_workflow(self, flow_pk: str):
#     logger.info(f"RUNNING progress_workflow {flow_pk=}")
#     # Get workflow from task
#     flow: Flow = Flow.objects.get(pk=flow_pk)
#     if not flow.is_complete:
#         executor = WorkflowExecutor(flow)
#         try:
#             executor.run_flow(user=None)
#         except WorkflowNotAuthError as e:
#             logger.warning(f"{e}")


# @celery_app.task(bind=True)
# def update_staff_search_index_from_activity_stream(self):
#     logger.info("RUNNING update_staff_search_index_from_activity_stream")
#     ingest_activity_stream()
#
#
# @celery_app.task(bind=True)
# def update_staff_search_index_from_people_finder(self):
#     logger.info("RUNNING update_staff_search_index_from_people_finder")
#     ingest_people_finder()
#
#
# @celery_app.task(bind=True)
# def update_staff_search_index_from_service_now(self):
#     logger.info("RUNNING update_staff_search_index_from_service_now")
#     ingest_service_now()
