from typing import List, Optional, TypedDict


class DirectReport(TypedDict):
    OracleID: str
    EmployeeID: str
    Name: str
    Email: str
    NewManager: str
    NewManagerEmail: str
    Effectivedate: str  # 15/03/2022


class LeavingData(TypedDict):
    submitterName: str
    submitterEmail: str
    submitterOracleID: str
    submitterDate: str  # "16/03/2022 14:59"
    submitterSelectedLineManager: str
    submitterSelectedLineManagerEmail: str
    submitterSelectedLineManagerOracleID: str
    submitterSelectedLineManagerEmployeeNumber: str
    leaverName: str
    leaverEmail: str
    leaverOracleID: str
    leaverEmployeeNumber: str
    leaverPaidUnpaid: str
    leaverReasonForLeaving: str
    leaverLastDay: str
    annualLeaveUom: str
    annualLeavePaidOrDeducted: str
    annualLeaveDaysPaid: int
    annualLeaveHoursPaid: int
    annualLeaveDaysDeducted: int
    annualLeaveHoursDeducted: int
    flexiPaidOrDeducted: str
    flexiHoursPaid: int
    flexiHoursDeducted: int
    newCorrEmail: Optional[str]
    newCorrAddressLine1: Optional[str]
    newCorrAddressLine2: Optional[str]
    newCorrAddressLine3: Optional[str]
    newCorrCounty: Optional[str]
    newCorrPostcode: Optional[str]
    newCorrPhone: Optional[str]
    directReports: List[DirectReport]
