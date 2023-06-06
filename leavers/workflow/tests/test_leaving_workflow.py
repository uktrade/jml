from datetime import date, timedelta
from typing import Dict, List
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from django_workflow_engine.executor import WorkflowExecutor
from django_workflow_engine.models import Flow

from core.utils.staff_index import StaffDocument
from leavers.factories import LeaverInformationFactory, LeavingRequestFactory
from leavers.types import LeavingReason
from user.test.factories import UserFactory

STAFF_DOCUMENT = StaffDocument.from_dict(
    {
        "uuid": "",
        "available_in_staff_sso": True,
        "staff_sso_activity_stream_id": "1",
        "staff_sso_legacy_id": "123",
        "staff_sso_contact_email_address": "joe.bloggs@example.com",  # /PS-IGNORE
        "staff_sso_first_name": "Joe",  # /PS-IGNORE
        "staff_sso_last_name": "Bloggs",
        "staff_sso_email_user_id": "joe.bloggs@example.com",  # /PS-IGNORE
        "staff_sso_email_addresses": [
            "joe.bloggs@example.com",  # /PS-IGNORE
        ],
        "people_finder_directorate": "",
        "people_finder_first_name": "Joe",  # /PS-IGNORE
        "people_finder_grade": "Example Grade",
        "people_finder_job_title": "Job title",
        "people_finder_last_name": "Bloggs",
        "people_finder_phone": "0123456789",
        "people_finder_email": "joe.bloggs@example.com",  # /PS-IGNORE
        "people_finder_photo": "",
        "people_finder_photo_small": "",
    }
)


@mock.patch(
    "leavers.workflow.tasks.CheckUKSBSLineManager.execute",
    return_value=(
        ["send_line_manager_correction_reminder"],
        False,
    ),
)
@mock.patch(
    "leavers.workflow.tasks.CheckUKSBSLeaver.execute",
    return_value=(
        ["send_leaver_not_in_uksbs_reminder"],
        False,
    ),
)
@mock.patch("core.notify.email")
@mock.patch("leavers.workflow.tasks.is_work_day_and_time", return_value=True)
class TestLeaversWorkflow(TestCase):
    """
    These tests the Leavers Workflow in it's current state

    Note: setup_scheduled_tasks is currently a `pause_task` which means that it
    will never run and always result in adding itself back to the Flow's tasks
    list.
    """

    # A mapping of Step IDs to possible target values
    TASK_TARGET_MAPPING: Dict[str, List[List[str]]] = {
        "setup_leaving": [
            ["send_leaver_thank_you_email"],
        ],
        "send_leaver_thank_you_email": [
            ["send_leaver_questionnaire_email"],
        ],
        "send_leaver_questionnaire_email": [
            ["check_uksbs_leaver"],
        ],
        "check_uksbs_leaver": [
            ["send_leaver_not_in_uksbs_reminder", "check_uksbs_line_manager"],
        ],
        "send_leaver_not_in_uksbs_reminder": [
            ["check_uksbs_leaver"],
        ],
        "check_uksbs_line_manager": [
            [
                "send_line_manager_missing_person_id_reminder",
                "send_line_manager_correction_reminder",
                "notify_line_manager",
            ],
        ],
        "send_line_manager_missing_person_id_reminder": [
            ["check_uksbs_line_manager"],
        ],
        "send_line_manager_correction_reminder": [
            ["check_uksbs_line_manager"],
        ],
        "notify_line_manager": [
            ["has_line_manager_completed"],
        ],
        "has_line_manager_completed": [
            ["send_line_manager_reminder", "thank_line_manager"],
        ],
        "send_line_manager_reminder": [
            ["has_line_manager_completed"],
        ],
        "thank_line_manager": [
            ["setup_scheduled_tasks"],
        ],
        "setup_scheduled_tasks": [
            ["setup_scheduled_tasks"],
            [
                "send_uksbs_leaver_details",
                "send_service_now_leaver_details",
                "send_feetham_leaver_details",
                "send_it_ops_leaver_details",
                "send_lsd_team_leaver_details",
                "notify_clu4_of_leaving",
                "notify_ocs_of_leaving",
                "notify_ocs_of_oab_locker",
                "notify_health_and_safety",
                "should_notify_comaea_team",
                "notify_business_continuity_team",
                "send_security_bp_notification",
                "send_security_rk_notification",
                "have_sre_carried_out_leaving_tasks",
                "has_line_manager_updated_service_now",
            ],
        ],
        "send_uksbs_leaver_details": [
            ["are_all_tasks_complete"],
        ],
        "send_service_now_leaver_details": [
            ["are_all_tasks_complete"],
        ],
        "send_feetham_leaver_details": [
            ["are_all_tasks_complete"],
        ],
        "send_it_ops_leaver_details": [
            ["are_all_tasks_complete"],
        ],
        "send_lsd_team_leaver_details": [
            ["are_all_tasks_complete"],
        ],
        "notify_clu4_of_leaving": [
            ["are_all_tasks_complete"],
        ],
        "notify_ocs_of_leaving": [
            ["are_all_tasks_complete"],
        ],
        "notify_ocs_of_oab_locker": [
            ["are_all_tasks_complete"],
        ],
        "notify_health_and_safety": [
            ["are_all_tasks_complete"],
        ],
        "should_notify_comaea_team": [
            ["notify_comaea_team"],
        ],
        "notify_comaea_team": [
            ["are_all_tasks_complete"],
        ],
        "notify_business_continuity_team": [
            ["are_all_tasks_complete"],
        ],
        "send_security_bp_notification": [
            ["have_security_carried_out_bp_leaving_tasks"],
        ],
        "have_security_carried_out_bp_leaving_tasks": [
            ["send_security_bp_reminder"],
            ["are_all_tasks_complete"],
        ],
        "send_security_bp_reminder": [
            ["have_security_carried_out_bp_leaving_tasks"],
        ],
        "send_security_rk_notification": [
            ["have_security_carried_out_rk_leaving_tasks"],
        ],
        "have_security_carried_out_rk_leaving_tasks": [
            ["send_security_rk_reminder"],
            ["are_all_tasks_complete"],
        ],
        "send_security_rk_reminder": [
            ["have_security_carried_out_rk_leaving_tasks"],
        ],
        "has_line_manager_updated_service_now": [
            ["send_line_manager_offline_service_now_reminder"],
            ["are_all_tasks_complete"],
        ],
        "send_line_manager_offline_service_now_reminder": [
            ["has_line_manager_updated_service_now"],
        ],
        "have_sre_carried_out_leaving_tasks": [
            ["send_sre_reminder"],
            ["are_all_tasks_complete"],
        ],
        "send_sre_reminder": [
            ["have_sre_carried_out_leaving_tasks"],
        ],
        "are_all_tasks_complete": [
            ["are_all_tasks_complete"],
            [],
        ],
    }

    def setUp(self):
        now = timezone.now()
        self.leaving_request = LeavingRequestFactory(
            leaving_date=now + timedelta(days=15),
            last_day=now + timedelta(days=12),
            leaver_complete=now,
            reason_for_leaving=LeavingReason.RESIGNATION.value,
            leaver_activitystream_user__employee_numbers=["123", "abc"],
        )
        self.leaving_request.processing_manager_activitystream_user = (
            self.leaving_request.manager_activitystream_user
        )
        self.leaving_request.save()
        self.leaving_request.processing_manager_activitystream_user.uksbs_person_id = (
            self.leaving_request.leaver_activitystream_user.uksbs_person_id + "manager"
        )
        self.leaving_request.processing_manager_activitystream_user.save()

        self.leaver_information = LeaverInformationFactory(
            leaving_request=self.leaving_request,
            leaver_date_of_birth=date(1990, 1, 1),
            dse_assets=[],
            cirrus_assets=[],
        )

        self.flow = Flow.objects.create(
            workflow_name="leaving",
            flow_name="test_flow",
            executed_by=UserFactory(),
        )
        self.flow.leaving_request = self.leaving_request
        self.flow.save()

        self.executor = WorkflowExecutor(self.flow)

    def check_tasks(self, expected_tasks: List[str]):
        self.assertEqual(
            [flow.step_id for flow in self.flow.tasks.all().order_by("started_at")],
            expected_tasks,
        )

    def run_leaver_not_in_uksbs(self, expected_tasks, mock_CheckUKSBSLeaver_execute):
        mock_CheckUKSBSLeaver_execute.return_value = (
            ["send_leaver_not_in_uksbs_reminder"],
            False,
        )
        self.executor.run_flow(user=None)
        expected_tasks += [
            "setup_leaving",
            "send_leaver_thank_you_email",
            "send_leaver_questionnaire_email",
            "check_uksbs_leaver",
            "send_leaver_not_in_uksbs_reminder",
        ]
        self.check_tasks(expected_tasks=expected_tasks)

    def run_leaver_in_uksbs_line_manager_person_id_missing(
        self,
        expected_tasks,
        mock_CheckUKSBSLeaver_execute,
        mock_CheckUKSBSLineManager_execute,
    ):
        mock_CheckUKSBSLeaver_execute.return_value = (
            ["check_uksbs_line_manager"],
            True,
        )
        mock_CheckUKSBSLineManager_execute.return_value = (
            ["send_line_manager_missing_person_id_reminder"],
            False,
        )
        self.executor.run_flow(user=None)
        self.executor.run_flow(user=None)
        expected_tasks += [
            "check_uksbs_line_manager",
            "send_line_manager_missing_person_id_reminder",
        ]

        self.check_tasks(expected_tasks=expected_tasks)

    def run_leaver_in_uksbs_line_manager_not_in_uksbs(
        self, expected_tasks, mock_CheckUKSBSLineManager_execute
    ):
        mock_CheckUKSBSLineManager_execute.return_value = (
            ["send_line_manager_correction_reminder"],
            True,
        )
        self.executor.run_flow(user=None)
        self.executor.run_flow(user=None)
        expected_tasks += [
            "send_line_manager_correction_reminder",
        ]

        self.check_tasks(expected_tasks=expected_tasks)

    def run_line_manger_in_uksbs(
        self, expected_tasks, mock_CheckUKSBSLineManager_execute
    ):
        mock_CheckUKSBSLineManager_execute.return_value = (
            ["notify_line_manager"],
            True,
        )
        self.executor.run_flow(user=None)
        self.executor.run_flow(user=None)
        expected_tasks += [
            "notify_line_manager",
            "has_line_manager_completed",
            "send_line_manager_reminder",
        ]
        self.check_tasks(expected_tasks=expected_tasks)

    def run_line_manger_completed_offboarding(
        self,
        expected_tasks,
        mock_get_staff_document_from_staff_index,
    ):
        mock_get_staff_document_from_staff_index.return_value = STAFF_DOCUMENT

        self.leaving_request.line_manager_complete = timezone.now()
        self.leaving_request.save(update_fields=["line_manager_complete"])

        self.executor.run_flow(user=None)
        self.executor.run_flow(user=None)
        expected_tasks += [
            "thank_line_manager",
            "setup_scheduled_tasks",
            "send_uksbs_leaver_details",
            "send_service_now_leaver_details",
            "send_feetham_leaver_details",
            "send_it_ops_leaver_details",
            "send_lsd_team_leaver_details",
            "notify_clu4_of_leaving",
            "notify_ocs_of_leaving",
            "notify_ocs_of_oab_locker",
            "notify_health_and_safety",
            "should_notify_comaea_team",
            "notify_business_continuity_team",
            "send_security_bp_notification",
            "send_security_rk_notification",
            "has_line_manager_updated_service_now",
            "have_sre_carried_out_leaving_tasks",
            "are_all_tasks_complete",
            "notify_comaea_team",
            "have_security_carried_out_bp_leaving_tasks",
            "have_security_carried_out_rk_leaving_tasks",
            "send_sre_reminder",
            "send_security_bp_reminder",
        ]

        self.check_tasks(expected_tasks=expected_tasks)

    @mock.patch(
        "leavers.utils.leaving_request.get_staff_document_from_staff_index",
        return_value=None,
    )
    def test_workflow(
        self,
        mock_get_staff_document_from_staff_index,
        mock_is_work_day_and_time,
        mock_email,
        mock_CheckUKSBSLeaver_execute,
        mock_CheckUKSBSLineManager_execute,
    ):
        expected_tasks: List[str] = []
        self.check_tasks(expected_tasks=expected_tasks)

        # Leaver is not in UK SBS
        self.run_leaver_not_in_uksbs(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLeaver_execute=mock_CheckUKSBSLeaver_execute,
        )

        # Leaver is in UK SBS and Line manager has a missing Person ID
        self.run_leaver_in_uksbs_line_manager_person_id_missing(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLeaver_execute=mock_CheckUKSBSLeaver_execute,
            mock_CheckUKSBSLineManager_execute=mock_CheckUKSBSLineManager_execute,
        )

        # Leaver is in UK SBS and Line manager is not in UK SBS
        self.run_leaver_in_uksbs_line_manager_not_in_uksbs(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLineManager_execute=mock_CheckUKSBSLineManager_execute,
        )

        # Line manager is in UK SBS, notified and hasn't completed the offboarding process
        self.run_line_manger_in_uksbs(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLineManager_execute=mock_CheckUKSBSLineManager_execute,
        )

        # Line manager has completed the offboarding process
        self.run_line_manger_completed_offboarding(
            expected_tasks=expected_tasks,
            mock_get_staff_document_from_staff_index=mock_get_staff_document_from_staff_index,
        )

        # Check to make sure all task targets are correct
        for task in self.flow.tasks.filter(executed_at__isnull=False).order_by(
            "started_at"
        ):
            task_targets: List[str] = [
                task_target.target_string for task_target in task.targets.all()
            ]
            self.assertTrue(
                task_targets in self.TASK_TARGET_MAPPING.get(task.step_id, [])
            )

    @mock.patch(
        "leavers.utils.leaving_request.get_staff_document_from_staff_index",
        return_value=None,
    )
    def test_workflow_with_pauses(
        self,
        mock_get_staff_document_from_staff_index,
        mock_is_work_day_and_time,
        mock_email,
        mock_CheckUKSBSLeaver_execute,
        mock_CheckUKSBSLineManager_execute,
    ):
        expected_tasks: List[str] = []
        self.check_tasks(expected_tasks=expected_tasks)

        # Leaver is not in UK SBS
        self.run_leaver_not_in_uksbs(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLeaver_execute=mock_CheckUKSBSLeaver_execute,
        )

        # Run a few more times without progression to make sure nothing odd happens.
        for _ in range(10):
            self.executor.run_flow(user=None)
            self.check_tasks(expected_tasks=expected_tasks)

        # Leaver is in UK SBS and Line manager has a missing Person ID
        self.run_leaver_in_uksbs_line_manager_person_id_missing(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLeaver_execute=mock_CheckUKSBSLeaver_execute,
            mock_CheckUKSBSLineManager_execute=mock_CheckUKSBSLineManager_execute,
        )

        # Run a few more times without progression to make sure nothing odd happens.
        for _ in range(10):
            self.executor.run_flow(user=None)
            self.check_tasks(expected_tasks=expected_tasks)

        # Leaver is in UK SBS and Line manager is not in UK SBS
        self.run_leaver_in_uksbs_line_manager_not_in_uksbs(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLeaver_execute=mock_CheckUKSBSLeaver_execute,
        )

        # Run a few more times without progression to make sure nothing odd happens.
        for _ in range(10):
            self.executor.run_flow(user=None)
            self.check_tasks(expected_tasks=expected_tasks)

        # Line manager is in UK SBS, notified and hasn't completed the
        # offboarding process
        self.run_line_manger_in_uksbs(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLineManager_execute=mock_CheckUKSBSLineManager_execute,
        )

        # Run a few more times without progression to make sure nothing odd happens.
        for _ in range(10):
            self.executor.run_flow(user=None)
            self.check_tasks(expected_tasks=expected_tasks)

        # Line manager has completed the offboarding process
        self.run_line_manger_completed_offboarding(
            expected_tasks=expected_tasks,
            mock_get_staff_document_from_staff_index=mock_get_staff_document_from_staff_index,
        )

        # Check to make sure all task targets are correct
        for task in self.flow.tasks.filter(executed_at__isnull=False).order_by(
            "started_at"
        ):
            task_targets: List[str] = [
                task_target.target_string for task_target in task.targets.all()
            ]
            self.assertTrue(
                task_targets in self.TASK_TARGET_MAPPING.get(task.step_id, [])
            )
