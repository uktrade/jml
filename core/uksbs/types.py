from typing import Any, List, Literal, Optional, TypedDict

ReasonForLeaving = Literal[
    "resignation",
    "end_of_contract",
    "retirement",
]


class AccessToken(TypedDict):
    access_token: str
    expires_at: float
    expires_in: int
    scope: List[str]
    token_type: str


class PersonData(TypedDict):
    # NEVER EXPOSE THIS FIELD
    person_id: str
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


class ServiceRequestDataContact(TypedDict):
    contactNumber: str
    contactType: Literal["EMPLOYEE"]
    contactTypePoint: Literal["EMAIL"]
    contactPrimaryFlag: Literal["Y", "N"]


class ServiceRequestData(TypedDict):
    problemSummary: str
    contacts: List[ServiceRequestDataContact]


class DirectReport(TypedDict):
    OracleID: str
    EmployeeID: str
    Name: str
    Email: str
    NewManager: str
    NewManagerEmail: str
    Effectivedate: str  # 15/03/2022


class TemplateData(TypedDict):
    additionalDirectReports: List[DirectReport]
    directReports: List[DirectReport]

    # Payroll Details
    leaverPaidUnpaid: str
    annualLeaveUom: Literal["days", "hours"]
    annualLeavePaidOrDeducted: Literal["paid", "deducted"]
    annualLeaveDaysPaid: str
    annualLeaveHoursPaid: str
    annualLeaveDaysDeducted: str
    annualLeaveHoursDeducted: str
    flexiPaidOrDeducted: Literal["paid", "deducted"]
    flexiHoursPaid: str
    flexiHoursDeducted: str

    # Leaver Details
    leaverName: str
    leaverEmail: str
    leaverOracleID: str
    leaverEmployeeNumber: str
    leaverReasonForLeaving: ReasonForLeaving
    leaverLastDay: str

    # Leaver Correspondance Details
    newCorrEmail: Optional[str]
    newCorrAddressLine1: Optional[str]
    newCorrAddressLine2: Optional[str]
    newCorrAddressLine3: Optional[str]
    newCorrCounty: Optional[str]
    newCorrPostcode: Optional[str]
    newCorrPhone: Optional[str]

    # Submitter Details
    submitterName: str
    submitterEmail: str
    submitterOracleID: str
    submitterDate: str
    submitterSelectedLineManager: str
    submitterSelectedLineManagerEmail: str
    submitterSelectedLineManagerOracleID: str
    submitterSelectedLineManagerEmployeeNumber: str


class LeavingData(TypedDict):
    serviceRequestData: ServiceRequestData
    templateData: TemplateData
