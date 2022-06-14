
# Emails

| Email name | Template ID Environment Variable | Context/Notes |
| ----- | ----- | ----- |
| Leaver Thank You Email | TEMPLATE_ID_LEAVER_THANK_YOU_EMAIL |  |
| UKSBS Line Manager Mismatch Email | ??? |  |
| Line Manager Notification Email | TEMPLATE_ID_LINE_MANAGER_NOTIFICATION_EMAIL |  |
| Line Manager Reminder Email | TEMPLATE_ID_LINE_MANAGER_REMINDER_EMAIL |  |
| Line Manager Thank You Email | TEMPLATE_ID_LINE_MANAGER_THANKYOU_EMAIL |  |
| CSU4 Leaver Notification Email | TEMPLATE_ID_CSU4_EMAIL |  |
| OCS Leaver Notification Email | TEMPLATE_ID_OCS_LEAVER_EMAIL |  |
| OCS Leaver OAB Locker Email | TEMPLATE_ID_OCS_OAB_LOCKER_EMAIL |  |
| ROSA Leaver Reminder Email | TEMPLATE_ID_ROSA_LEAVER_REMINDER_EMAIL |  |
| ROSA Line Manager Reminder Email | TEMPLATE_ID_ROSA_LINE_MANAGER_REMINDER_EMAIL |  |
| Security Team building pass Leaver Email | ??? |  |
| Security Team building pass Leaver Reminder Email | ??? |  |
| Security Team ROSA Kit Leaver Email | ??? |  |
| Security Team ROSA Kit Leaver Reminder Email | ??? |  |
| SRE Reminder Email | TEMPLATE_ID_SRE_REMINDER_EMAIL |  |

## When do we send emails?

### When a leaver self reports
- Send the leaver the **Leaver Thank You Email**.
- Send the line manager the **Line Manager Notification Email**.
- Send the line manager the **Line Manager Reminder Email** (on some frequency).

### When a line manager confirms a leaving request
- Send the line manager the **Line Manager Thank You Email**.

## Reminder Email Matrix
### Reminder 
- 2 weeks away - Send 2 weeks before the leaving date
- Daily for last week - Send daily for the week leading to up to the leaving date
- Last working day - Send on the leaver's last working day
- Leaving date - Send on the day of the leaving date
- Daily after leaving date - Send daily after the leaving date

| Email | 2 weeks away | Daily for last week | Last working day | Leaving date | Daily after leaving date |
| ----- | ----- | ----- | ----- | ----- | ----- |
| Line Manager Reminder Email | X | X |  | X | X |
| ROSA Leaver Reminder Email | X | X |  | X | X |
| ROSA Line Manager Reminder Email | X | X |  | X | X |
| Security Team building pass Leaver Reminder Email |  |  | ? | ? | ? |
| Security Team ROSA Kit Leaver Reminder Email |  |  | ? | ? | ? |
| SRE Reminder Email |  |  | ? | ? | ? |
