# Joiners Movers Leavers prototype

## Setup

- Copy the example env file `cp .env.example .env`
- Copy the example local settings file `cp config/settings/local.example.py config/settings/local.py`
    - Configure env vars (talk to SRE for values)
- Install FE dependancies
    - `npm install` 
- Build local docker instance:
    - `make build`
    - `make migrate` or `make first-use` 
- Start the local docker instance `make up`

## Update requirements files

`make all-requirements`

## Environment Variables

| Environment variable                                     | Default                                    | Notes                                                               |
| ---------------------------------                        | ------------------------------------------ | ---------------------------------                                   |
| DEV_TOOLS_ENABLED                                        | false                                      | Set this value to "true" to enable Dev Tools and disable Authbroker |
| SLACK_API_TOKEN                                          | None                                       |                                                                     |
| SLACK_SRE_CHANNEL_ID                                     | None                                       |                                                                     |
| PEOPLE_FINDER_HAWK_ACCESS_ID                             |                                            |                                                                     |
| PEOPLE_FINDER_HAWK_SECRET_KEY                            |                                            |                                                                     |
| PEOPLE_FINDER_URL                                        |                                            |                                                                     |
| PEOPLE_FINDER_INTERFACE                                  |                                            |                                                                     |
| STAFF_SSO_ACTIVITY_STREAM_URL                            | None                                       |                                                                     |
| STAFF_SSO_ACTIVITY_STREAM_ID                             | None                                       |                                                                     |
| STAFF_SSO_ACTIVITY_STREAM_SECRET                         | None                                       |                                                                     |
| SERVICE_NOW_INTERFACE                                    | None                                       |                                                                     |
| SERVICE_NOW_API_URL                                      | None                                       |                                                                     |
| SERVICE_NOW_POST_LEAVER_REQUEST                          | None                                       |                                                                     |
| SERVICE_NOW_GET_ASSET_PATH                               | None                                       |                                                                     |
| SERVICE_NOW_GET_USER_PATH                                | None                                       |                                                                     |
| SERVICE_NOW_GET_DIRECTORATE_PATH                         | None                                       |                                                                     |
| SERVICE_NOW_DIT_DEPARTMENT_SYS_ID                        | None                                       |                                                                     |
| LEGACY_PEOPLE_FINDER_ES_INDEX                            | None                                       |                                                                     |
| LEGACY_PEOPLE_FINDER_ES_URL                              | None                                       |                                                                     |
| CSU4_EMAIL                                               | None                                       | Email address for the CSU4 Team                                     |
| OCS_EMAIL                                                | None                                       | Email address for the OCS Team                                      |
| SECURITY_TEAM_EMAIL                                      | None                                       | Email address for the Security Team                                 |
| SRE_EMAIL                                                | None                                       | Email address for the SRE Team                                      |
| GOVUK_NOTIFY_API_KEY                                     | None                                       |                                                                     |
| CSU4_EMAIL_TEMPLATE_ID                                   | None                                       |                                                                     |
| OCS_LEAVER_EMAIL_TEMPLATE_ID                             | None                                       |                                                                     |
| ROSA_LEAVER_REMINDER_EMAIL_TEMPLATE_ID                   | None                                       |                                                                     |
| ROSA_LINE_MANAGER_REMINDER_EMAIL_TEMPLATE_ID             | None                                       |                                                                     |
| SECURITY_TEAM_OFFBOARD_LEAVER_EMAIL_TEMPLATE_ID          | None                                       |                                                                     |
| SECURITY_TEAM_OFFBOARD_LEAVER_REMINDER_EMAIL_TEMPLATE_ID | None                                       |                                                                     |
| SRE_REMINDER_EMAIL_TEMPLATE_ID                           | None                                       |                                                                     |
| LINE_MANAGER_NOTIFICATION_EMAIL_TEMPLATE_ID              | None                                       |                                                                     |
| LINE_MANAGER_REMINDER_EMAIL_TEMPLATE_ID                  | None                                       |                                                                     |
| LINE_MANAGER_THANKYOU_EMAIL_TEMPLATE_ID                  | None                                       |                                                                     |
| LSD_ZENDESK_EMAIL                                        |                                            | LSD Team Zendesk email address                                      |
| LSD_ZENDESK_TOKEN                                        |                                            |                                                                     |
| LSD_ZENDESK_SUBDOMAIN                                    |                                            |                                                                     |
| SEARCH_HOST_URLS                                         |                                            |                                                                     |
| SEARCH_STAFF_INDEX_NAME                                  | staff                                      |                                                                     |
| INDEX_CURRENT_USER_MIDDLEWARE                            | false                                      |                                                                     |
| UKSBS_INTERFACE                                          | None                                       |                                                                     |
| UKSBS_API_URL                                            | None                                       |                                                                     |
| UKSBS_GET_PEOPLE_HIERARCHY                               | None                                       | UK SBS People Hierarchy path                                        |
| UKSBS_POST_LEAVER_SUBMISSION                             | None                                       |                                                                     |
