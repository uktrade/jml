import environ
from django.conf import settings

env = environ.Env()
env.read_env()


class EmailTemplatesSettings:
    LEAVER_THANK_YOU_EMAIL: str
    # UK SBS Correction emails
    LEAVER_NOT_IN_UKSBS_HR_REMINDER: str
    LEAVER_NOT_IN_UKSBS_LM_REMINDER: str
    LINE_MANAGER_CORRECTION_EMAIL: str
    LINE_MANAGER_CORRECTION_HR_EMAIL: str
    LINE_MANAGER_CORRECTION_REPORTED_LM_EMAIL: str
    # Line Manager emails
    LINE_MANAGER_NOTIFICATION_EMAIL: str
    LINE_MANAGER_REMINDER_EMAIL: str
    LINE_MANAGER_THANKYOU_EMAIL: str
    LINE_MANAGER_OFFLINE_SERVICE_NOW_EMAIL: str
    # Procesor emails
    CLU4_EMAIL: str
    FEETHAM_SECURITY_PASS_OFFICE_EMAIL: str
    IT_OPS_ASSET_EMAIL: str
    OCS_LEAVER_EMAIL: str
    OCS_OAB_LOCKER_EMAIL: str
    COMAEA_EMAIL: str
    # Procesor emails: Security Offboarding (Building Pass)
    SECURITY_TEAM_OFFBOARD_BP_LEAVER_EMAIL: str
    SECURITY_OFFBOARD_BP_REMINDER_DAY_AFTER_LWD: str
    SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LWD: str
    SECURITY_OFFBOARD_BP_REMINDER_ON_LD: str
    SECURITY_OFFBOARD_BP_REMINDER_ONE_DAY_AFTER_LD: str
    SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_LM: str
    SECURITY_OFFBOARD_BP_REMINDER_TWO_DAYS_AFTER_LD_PROC: str
    # Procesor emails: Security Offboarding (Rosa Kit)
    SECURITY_TEAM_OFFBOARD_RK_LEAVER_EMAIL: str
    SECURITY_OFFBOARD_RK_REMINDER_DAY_AFTER_LWD: str
    SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LWD: str
    SECURITY_OFFBOARD_RK_REMINDER_ON_LD: str
    SECURITY_OFFBOARD_RK_REMINDER_ONE_DAY_AFTER_LD: str
    SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_LM: str
    SECURITY_OFFBOARD_RK_REMINDER_TWO_DAYS_AFTER_LD_PROC: str
    # Procesor emails: SRE
    SRE_NOTIFICATION: str
    SRE_REMINDER_DAY_AFTER_LWD: str
    SRE_REMINDER_ONE_DAY_AFTER_LD: str
    SRE_REMINDER_TWO_DAYS_AFTER_LD_PROC: str
    # Incomplete leaver in pay cut off period
    LEAVER_IN_PAY_CUT_OFF_HR_EMAIL: str

    def __getattr__(self, attr):
        setting_name = "TEMPLATE_ID_" + attr
        setting_value = env(setting_name, default=None)

        if setting_value:
            return setting_value

        if hasattr(settings, setting_name):
            return getattr(settings, setting_name)

        raise AttributeError(
            f"Setting 'TEMPLATE_ID_{attr}' is not defined, please add it to "
            "the environment variables"
        )


email_template_settings = EmailTemplatesSettings()
