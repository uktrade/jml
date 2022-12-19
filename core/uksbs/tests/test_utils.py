from django.test import TestCase

from core.uksbs.utils import get_leave_details
from leavers.factories import LeavingRequestFactory


class TestGetLeaveDetails(TestCase):
    def test_leaver_unpaid(self):
        leaving_request = LeavingRequestFactory(
            leaver_paid_unpaid="unpaid",
        )
        result = get_leave_details(leaving_request=leaving_request)

        self.assertEqual(result["leaverPaidUnpaid"], "unpaid")
        self.assertEqual(result["annualLeavePaidOrDeducted"], None)
        self.assertEqual(result["annualLeaveUom"], None)
        self.assertEqual(result["annualLeaveDaysPaid"], 0)
        self.assertEqual(result["annualLeaveHoursPaid"], 0)
        self.assertEqual(result["annualLeaveDaysDeducted"], 0)
        self.assertEqual(result["annualLeaveHoursDeducted"], 0)
        self.assertEqual(result["flexiPaidOrDeducted"], None)
        self.assertEqual(result["flexiHoursPaid"], 0)
        self.assertEqual(result["flexiHoursDeducted"], 0)

    def test_leaver_paid_with_annual_leave_paid(self):
        leaving_request = LeavingRequestFactory(
            leaver_paid_unpaid="paid",
            annual_leave="paid",
            annual_leave_measurement="days",
            annual_number="3",
        )
        result = get_leave_details(leaving_request=leaving_request)

        self.assertEqual(result["leaverPaidUnpaid"], "paid")
        self.assertEqual(result["annualLeavePaidOrDeducted"], "paid")
        self.assertEqual(result["annualLeaveUom"], "days")
        self.assertEqual(result["annualLeaveDaysPaid"], "3")
        self.assertEqual(result["annualLeaveHoursPaid"], 0)
        self.assertEqual(result["annualLeaveDaysDeducted"], 0)
        self.assertEqual(result["annualLeaveHoursDeducted"], 0)
        self.assertEqual(result["flexiPaidOrDeducted"], None)
        self.assertEqual(result["flexiHoursPaid"], 0)
        self.assertEqual(result["flexiHoursDeducted"], 0)

    def test_leaver_paid_with_annual_leave_deducted(self):
        leaving_request = LeavingRequestFactory(
            leaver_paid_unpaid="paid",
            annual_leave="deducted",
            annual_leave_measurement="hours",
            annual_number="7",
        )
        result = get_leave_details(leaving_request=leaving_request)

        self.assertEqual(result["leaverPaidUnpaid"], "paid")
        self.assertEqual(result["annualLeavePaidOrDeducted"], "deducted")
        self.assertEqual(result["annualLeaveUom"], "hours")
        self.assertEqual(result["annualLeaveDaysPaid"], 0)
        self.assertEqual(result["annualLeaveHoursPaid"], 0)
        self.assertEqual(result["annualLeaveDaysDeducted"], 0)
        self.assertEqual(result["annualLeaveHoursDeducted"], "7")
        self.assertEqual(result["flexiPaidOrDeducted"], None)
        self.assertEqual(result["flexiHoursPaid"], 0)
        self.assertEqual(result["flexiHoursDeducted"], 0)

    def test_leaver_paid_with_flexi_leave_paid(self):
        leaving_request = LeavingRequestFactory(
            leaver_paid_unpaid="paid",
            flexi_leave="paid",
            flexi_number="6",
        )
        result = get_leave_details(leaving_request=leaving_request)

        self.assertEqual(result["leaverPaidUnpaid"], "paid")
        self.assertEqual(result["annualLeavePaidOrDeducted"], None)
        self.assertEqual(result["annualLeaveUom"], None)
        self.assertEqual(result["annualLeaveDaysPaid"], 0)
        self.assertEqual(result["annualLeaveHoursPaid"], 0)
        self.assertEqual(result["annualLeaveDaysDeducted"], 0)
        self.assertEqual(result["annualLeaveHoursDeducted"], 0)
        self.assertEqual(result["flexiPaidOrDeducted"], "paid")
        self.assertEqual(result["flexiHoursPaid"], "6")
        self.assertEqual(result["flexiHoursDeducted"], 0)

    def test_leaver_paid_with_flexi_leave_deducted(self):
        leaving_request = LeavingRequestFactory(
            leaver_paid_unpaid="paid",
            flexi_leave="deducted",
            flexi_number="2",
        )
        result = get_leave_details(leaving_request=leaving_request)

        self.assertEqual(result["leaverPaidUnpaid"], "paid")
        self.assertEqual(result["annualLeavePaidOrDeducted"], None)
        self.assertEqual(result["annualLeaveUom"], None)
        self.assertEqual(result["annualLeaveDaysPaid"], 0)
        self.assertEqual(result["annualLeaveHoursPaid"], 0)
        self.assertEqual(result["annualLeaveDaysDeducted"], 0)
        self.assertEqual(result["annualLeaveHoursDeducted"], 0)
        self.assertEqual(result["flexiPaidOrDeducted"], "deducted")
        self.assertEqual(result["flexiHoursPaid"], 0)
        self.assertEqual(result["flexiHoursDeducted"], "2")
