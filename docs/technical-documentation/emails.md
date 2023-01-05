
# Emails

## Leaver and Line Manager emails

| Email name                                                  | Template ID Environment Variable                      | Context/Notes |
| ----------                                                  | --------------------------------                      | ------------- |
| Leaver Thank You Email                                      | TEMPLATE_ID_LEAVER_THANK_YOU_EMAIL                    | This email is sent after the Leaver has informed the service that they are leaving. |
| Leaver not in UK SBS (HR) Email                             | TEMPLATE_ID_LEAVER_NOT_IN_UKSBS_HR_REMINDER           | ??? |
| Leaver not in UK SBS (LM) Email                             | TEMPLATE_ID_LEAVER_NOT_IN_UKSBS_LM_REMINDER           | ??? |
| UKSBS Line Manager Correction Email (UK SBS manager)        | TEMPLATE_ID_LINE_MANAGER_CORRECTION_EMAIL             | This email is sent to the listed Line Manager in UK SBS to request that they update the Line Manager to be the one that the Leaver selected |
| UKSBS Line Manager Correction Email (Offboarding team)      | TEMPLATE_ID_LINE_MANAGER_CORRECTION_HR_EMAIL          | This email is sent to the HR Offboarding team to request they update the Line Manager in UK SBS to be the one that the Leaver selected. |
| UKSBS Line Manager Correction Email (Reported Line Manager) | TEMPLATE_ID_LINE_MANAGER_CORRECTION_REPORTED_LM_EMAIL | This email is sent to the Line Manager that the Leaver selected to inform them that they are not the manager in UK SBS and that the HR team must fix this for them to be able to offboard the Leaver. |
| Line Manager Notification Email                             | TEMPLATE_ID_LINE_MANAGER_NOTIFICATION_EMAIL           | This email is sent to the Line Manager to inform them of the leaver and the actions they need to take. |
| Line Manager Reminder Email                                 | TEMPLATE_ID_LINE_MANAGER_REMINDER_EMAIL               | This email is sent to remind the Line Manager of the actions they need to take. |
| Line Manager Thank You Email                                | TEMPLATE_ID_LINE_MANAGER_THANKYOU_EMAIL               | This email is sent to the Line Manager once they have finished their journey. |
| Leaver Final Actions Email                                  | ???                                                   | This email is sent to the Leaver in their last working week to inform them of the actions they need to take. |
| Line Manager Final Actions Email                            | ???                                                   | This email is sent to the Line Manager in the leaver's last working week to inform them of the actions they need to take. |

### Leaver and Line Manager reminder logic

| Email | 2 weeks away | 1 week away (from last working day) | Daily for last week | Last working day | Leaving date | Daily after last working day | Daily after leaving date |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| Line Manager Reminder Email | X |  | X |  | X |  | X |
| Leaver Final Actions Email |  | X |  | X |  |  |  |
| Line Manager Final Actions Email |  | X |  | X |  |  |  |
| ROSA Leaver Reminder Email | X |  | X |  | X |  | X |
| ROSA Line Manager Reminder Email | X |  | X |  | X |  | X |

## Processor emails

These are notification emails sent to the processor:

| Email name | Template ID Environment Variable | Context/Notes |
| ----- | ----- | ----- |
| CLU4 Leaver Notification Email | TEMPLATE_ID_CLU4_EMAIL | This email is sent to CLU4 to inform them of the leaver. |
| Feetham Security Pass Office Leaver Notification Email | TEMPLATE_ID_FEETHAM_SECURITY_PASS_OFFICE_EMAIL | This email is sent to the Feetham Security Pass Office to inform them of the leaver and their reported assets. |
| IT Ops Leaver Notification Email | TEMPLATE_ID_IT_OPS_ASSET_EMAIL | This email is sent to the IT Ops team to inform them of the leaver and their reported assets. |
| OCS Leaver Notification Email | TEMPLATE_ID_OCS_LEAVER_EMAIL | This email is sent to OCS to inform them of the leaver. |
| OCS Leaver OAB Locker Email | TEMPLATE_ID_OCS_OAB_LOCKER_EMAIL | This email is sent to the OAB Locker team to inform them of the leaver. |
| OCS Leaver OAB Locker Email | TEMPLATE_ID_COMAEA_EMAIL | This email is sent to the OAB Locker team to inform them of the leaver. |

### Processor reminder logic

Once the Line Manager has processed a Leaving request, the following processors need to be informed and reminded to perform their tasks:

- Security building pass team
- Security ROSA kit team
- SRE team (no Line Manager emails)
- IT Ops team

Emails are sent at the following points:

| When | Condition | Purpose | Recipient |
| ----- | ----- | ----- | ----- |
| Day after the last working day | ALWAYS | Notification email to inform the Processor of the tasks | Processor |
| 2 days after the last working day | IF NOT PROCESSED | Notification email to inform the Line Manager of the tasks | Line Manager |
| On the leaving date | IF NOT PROCESSED | URGENT: Inform the Line Manager that the tasks need to be performed | Line Manager |
| 1 day after the leaving date | IF NOT PROCESSED | Inform the Processor that the tasks need to be performed | Processor |
| 2 days after the leaving date | IF NOT PROCESSED | Inform the Line Manager that the tasks need to be performed by end of the day otherwise escalation | Line Manager |
| 2 days after the leaving date | IF NOT PROCESSED | Inform the Processor that the tasks need to be performed by end of the day otherwise escalation | Processor |

#### Security building pass team
Only send these reminders if the Building pass hasn't been marked as destroyed.

#### Security ROSA kit team
Only send these reminders if the ROSA kit tasks haven't been marked as completed/closed.

#### SRE team
Only send these reminders if the SRE tasks haven't been marked as completed.
There is no need to send any of the emails to the Line Manager for SRE.

#### IT Ops team
Only send these reminders if the Leaver has assets that are considered "risky" (Laptop, mobile phone, etc).
