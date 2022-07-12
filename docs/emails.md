
# Emails

## Leaver and Line manager emails

| Email name | Template ID Environment Variable | Context/Notes |
| ----- | ----- | ----- |
| Leaver Thank You Email | TEMPLATE_ID_LEAVER_THANK_YOU_EMAIL | This email is sent after the Leaver has informed the service that they are leaving.|
| UKSBS Line Manager Mismatch Email | ??? | This email is used to help correct mismatching information between the Leaver service and UK SBS. |
| Leaver Final Actions Email | ??? | This email is sent to the Leaver in their last working week to inform them of the actions they need to take. |
| Line manager Final Actions Email | ??? | This email is sent to the Line manager in the leaver's last working week to inform them of the actions they need to take. |
| Line Manager Notification Email | TEMPLATE_ID_LINE_MANAGER_NOTIFICATION_EMAIL | This email is sent to the Line manager to inform them of the leaver and the actions they need to take. |
| Line Manager Reminder Email | TEMPLATE_ID_LINE_MANAGER_REMINDER_EMAIL | This email is sent to remind the Line manager of the actions they need to take. |
| Line Manager Thank You Email | TEMPLATE_ID_LINE_MANAGER_THANKYOU_EMAIL | This email is sent to the Line manager once they have finished their journey. |
| ROSA Leaver Reminder Email | TEMPLATE_ID_ROSA_LEAVER_REMINDER_EMAIL | This email is sent to the Leaver to remind them to return ROSA Kit |
| ROSA Line Manager Reminder Email | TEMPLATE_ID_ROSA_LINE_MANAGER_REMINDER_EMAIL | This email is sent to the Line manager to remind them to remind the leaver to return ROSA Kit |

### Leaver and Line manager reminder logic

| Email | 2 weeks away | 1 week away (from last working day) | Daily for last week | Last working day | Leaving date | Daily after last working day | Daily after leaving date |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| Line Manager Reminder Email | X |  | X |  | X |  | X |
| Leaver Final Actions Email |  | X |  | X |  |  |  |
| Line manager Final Actions Email |  | X |  | X |  |  |  |
| ROSA Leaver Reminder Email | X |  | X |  | X |  | X |
| ROSA Line Manager Reminder Email | X |  | X |  | X |  | X |

## Processor emails

These are notification emails sent to the processor:

| Email name | Template ID Environment Variable | Context/Notes |
| ----- | ----- | ----- |
| CSU4 Leaver Notification Email | TEMPLATE_ID_CSU4_EMAIL | This email is sent to CSU4 to inform them of the leaver. |
| OCS Leaver Notification Email | TEMPLATE_ID_OCS_LEAVER_EMAIL | This email is sent to OCS to inform them of the leaver. |
| OCS Leaver OAB Locker Email | TEMPLATE_ID_OCS_OAB_LOCKER_EMAIL | This email is sent to the OAB Locker team to inform them of the leaver. |
| SRE Reminder Email | TEMPLATE_ID_SRE_REMINDER_EMAIL |  |

### Processor reminder logic

Once the Line manager has processed a Leaving request, the following processors need to be informed and reminded to perform their tasks:

- Security building pass team
- Security ROSA kit team
- SRE team (no Line manager emails)
- IT Ops team

Emails are sent at the following points:

| When | Condition | Purpose | Recipient |
| ----- | ----- | ----- | ----- |
| Day after the last working day | ALWAYS | Notification email to inform the Processor of the tasks | Processor |
| 2 days after the last working day | IF NOT PROCESSED | Notification email to inform the Line manager of the tasks | Line manager |
| On the leaving date | IF NOT PROCESSED | URGENT: Inform the Line manager that the tasks need to be performed | Line manager |
| 1 day after the leaving date | IF NOT PROCESSED | Inform the Processor that the tasks need to be performed | Processor |
| 2 days after the leaving date | IF NOT PROCESSED | Inform the Line manager that the tasks need to be performed by end of the day otherwise escalation | Line manager |
| 2 days after the leaving date | IF NOT PROCESSED | Inform the Processor that the tasks need to be performed by end of the day otherwise escalation | Processor |

#### Security building pass team
Only send these reminders if the Building pass hasn't been marked as destroyed.

#### Security ROSA kit team
Only send these reminders if the ROSA kit tasks haven't been marked as completed/closed.

#### SRE team
Only send these reminders if the SRE tasks haven't been marked as completed.
There is no need to send any of the emails to the Line manager for SRE.

#### IT Ops team
Only send these reminders if the Leaver has assets that are considered "risky" (Laptop, mobile phone, etc).
