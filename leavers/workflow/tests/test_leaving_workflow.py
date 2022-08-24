from datetime import date, timedelta
from typing import Dict, List
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from django_workflow_engine.executor import WorkflowExecutor
from django_workflow_engine.models import Flow

from leavers.factories import LeaverInformationFactory, LeavingRequestFactory
from user.test.factories import UserFactory


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
            ["check_uksbs_leaver"],
        ],
        "check_uksbs_leaver": [
            ["send_leaver_not_in_uksbs_reminder"],
            ["check_uksbs_line_manager"],
        ],
        "send_leaver_not_in_uksbs_reminder": [
            ["check_uksbs_leaver"],
        ],
        "check_uksbs_line_manager": [
            ["send_line_manager_correction_reminder"],
            ["notify_line_manager"],
        ],
        "send_line_manager_correction_reminder": [
            ["check_uksbs_line_manager"],
        ],
        "notify_line_manager": [
            ["has_line_manager_completed"],
        ],
        "has_line_manager_completed": [
            ["send_line_manager_reminder"],
            ["thank_line_manager"],
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
                "send_it_ops_leaver_details",
                "send_lsd_team_leaver_details",
                "notify_clu4_of_leaving",
                "notify_ocs_of_leaving",
                "notify_ocs_of_oab_locker",
                "send_security_bp_notification",
                "send_security_rk_notification",
                "send_sre_notification",
            ],
        ],
    }

    def setUp(self):
        now = timezone.now()
        self.leaving_request = LeavingRequestFactory(
            leaving_date=now + timedelta(days=15),
            last_day=now + timedelta(days=12),
            leaver_complete=now,
        )
        self.leaver_information = LeaverInformationFactory(
            leaving_request=self.leaving_request,
            leaver_date_of_birth=date(1990, 1, 1),
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
            "check_uksbs_leaver",
            "send_leaver_not_in_uksbs_reminder",
        ]
        self.check_tasks(expected_tasks=expected_tasks)

        # Return back to the check leaver task
        self.executor.run_flow(user=None)
        expected_tasks += [
            "check_uksbs_leaver",
        ]
        self.check_tasks(expected_tasks=expected_tasks)

    def run_leaver_in_uksb_line_manager_not_in_uksbs(
        self, expected_tasks, mock_CheckUKSBSLeaver_execute
    ):
        mock_CheckUKSBSLeaver_execute.return_value = (
            ["check_uksbs_line_manager"],
            True,
        )
        self.executor.run_flow(user=None)
        expected_tasks += [
            "check_uksbs_line_manager",
            "send_line_manager_correction_reminder",
        ]
        self.check_tasks(expected_tasks=expected_tasks)

        # Return back to the check line manager task
        self.executor.run_flow(user=None)
        expected_tasks += [
            "check_uksbs_line_manager",
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
        expected_tasks += [
            "notify_line_manager",
            "has_line_manager_completed",
            "send_line_manager_reminder",
        ]
        self.check_tasks(expected_tasks=expected_tasks)

        # Return back to the check line manager has completed task
        self.executor.run_flow(user=None)
        expected_tasks += [
            "has_line_manager_completed",
        ]
        self.check_tasks(expected_tasks=expected_tasks)

    def run_line_manger_completed_offboarding(self, expected_tasks):
        self.leaving_request.line_manager_complete = timezone.now()
        self.leaving_request.save(update_fields=["line_manager_complete"])

        self.executor.run_flow(user=None)
        expected_tasks += [
            "thank_line_manager",
            # Setup Scheduled Tasks is a paus_task so it will continuously
            # create a new task of itself
            "setup_scheduled_tasks",
            "setup_scheduled_tasks",
        ]
        self.check_tasks(expected_tasks=expected_tasks)

    def test_workflow(
        self,
        mock_email,
        mock_CheckUKSBSLeaver_execute,
        mock_CheckUKSBSLineManager_execute,
    ):
        expected_tasks: List[str] = []

        self.assertFalse(self.flow.tasks.all().exists())

        # Leaver is not in UK SBS
        self.run_leaver_not_in_uksbs(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLeaver_execute=mock_CheckUKSBSLeaver_execute,
        )

        # Leaver is in UK SBS and Line manager is not in UK SBS
        self.run_leaver_in_uksb_line_manager_not_in_uksbs(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLeaver_execute=mock_CheckUKSBSLeaver_execute,
        )

        # Line manager is in UK SBS, notified and hasn't completed the off-boarding process
        self.run_line_manger_in_uksbs(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLineManager_execute=mock_CheckUKSBSLineManager_execute,
        )

        # Line manager has completed the off-boarding process
        self.run_line_manger_completed_offboarding(
            expected_tasks=expected_tasks,
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

    def test_workflow_with_pauses(
        self,
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
            expected_tasks += [
                "send_leaver_not_in_uksbs_reminder",
            ]
            self.check_tasks(expected_tasks=expected_tasks)
            self.executor.run_flow(user=None)
            expected_tasks += [
                "check_uksbs_leaver",
            ]
            self.check_tasks(expected_tasks=expected_tasks)

        # Leaver is in UK SBS and Line manager is not in UK SBS
        self.run_leaver_in_uksb_line_manager_not_in_uksbs(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLeaver_execute=mock_CheckUKSBSLeaver_execute,
        )

        # Run a few more times without progression to make sure nothing odd happens.
        for _ in range(10):
            self.executor.run_flow(user=None)
            expected_tasks += [
                "send_line_manager_correction_reminder",
            ]
            self.check_tasks(expected_tasks=expected_tasks)
            self.executor.run_flow(user=None)
            expected_tasks += [
                "check_uksbs_line_manager",
            ]
            self.check_tasks(expected_tasks=expected_tasks)

        # Line manager is in UK SBS, notified and hasn't completed the
        # off-boarding process
        self.run_line_manger_in_uksbs(
            expected_tasks=expected_tasks,
            mock_CheckUKSBSLineManager_execute=mock_CheckUKSBSLineManager_execute,
        )

        # Run a few more times without progression to make sure nothing odd happens.
        for _ in range(10):
            self.executor.run_flow(user=None)
            expected_tasks += [
                "send_line_manager_reminder",
            ]
            self.check_tasks(expected_tasks=expected_tasks)
            self.executor.run_flow(user=None)
            expected_tasks += [
                "has_line_manager_completed",
            ]
            self.check_tasks(expected_tasks=expected_tasks)

        # Line manager has completed the off-boarding process
        self.run_line_manger_completed_offboarding(
            expected_tasks=expected_tasks,
        )

        # Run a few more times without progression to make sure nothing odd happens.
        for _ in range(10):
            self.executor.run_flow(user=None)
            expected_tasks += [
                "setup_scheduled_tasks",
            ]
            self.check_tasks(expected_tasks=expected_tasks)

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
