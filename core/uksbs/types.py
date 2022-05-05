from typing import Any, List, Optional, TypedDict


class AccessToken(TypedDict):
    access_token: str
    expires_at: float
    expires_in: int
    scope: List[str]
    token_type: str


class PersonData(TypedDict):
    person_id: int
    username: Optional[Any]
    full_name: str
    first_name: str
    last_name: str
    employee_number: str
    department: str
    position: str
    email_address: str
    job_id: int
    work_phone: Optional[str]
    work_mobile: Optional[str]


class PersonHierarchyData(TypedDict):
    manager: List[PersonData]
    employee: List[PersonData]
    report: List[PersonData]


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
