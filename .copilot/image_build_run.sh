#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

# Add commands below to run inside the container after all the other buildpacks have been applied
export APP_ENV=dev
export DEBUG=True
export DJANGO_SETTINGS_MODULE=config.settings.test
export DATABASE_URL=psql://postgres:postgres@db:5432/leavers
export SECRET_KEY=do_not_use_this_in_production
export ALLOWED_HOSTS=localhost,localhost:8000
export REDIS_URL=redis://redis:6379
export DEV_TOOLS_ENABLED=true
export HAWK_INCOMING_ACCESS_KEY=xxx
export HAWK_INCOMING_SECRET_KEY=xxx
export AUTHBROKER_SCOPES='read write'
export AUTHBROKER_URL=https://sso.trade.gov.uk/
export AUTHBROKER_CLIENT_ID=xxx
export AUTHBROKER_CLIENT_SECRET=xxx
export GTM_CODE=None
export SLACK_API_TOKEN=xxx
export SLACK_SRE_CHANNEL_ID=xxx
export STAFF_SSO_ACTIVITY_STREAM_URL=xx
export STAFF_SSO_ACTIVITY_STREAM_ID=xxx
export STAFF_SSO_ACTIVITY_STREAM_SECRET=xxx
export SITE_URL=xxx
export PEOPLE_FINDER_URL=xxx
export PEOPLE_FINDER_INTERFACE=core.people_finder.interfaces.PeopleFinderStubbed
export PEOPLE_FINDER_HAWK_ACCESS_ID=some-sender
export PEOPLE_FINDER_HAWK_SECRET_KEY=a-long-complicated-secret
export LEGACY_PEOPLE_FINDER_ES_INDEX=xxx
export LEGACY_PEOPLE_FINDER_ES_URL=xxx
export SERVICE_NOW_INTERFACE=core.service_now.interfaces.ServiceNowStubbed
export SERVICE_NOW_API_URL=xxx
export SERVICE_NOW_POST_LEAVER_REQUEST=some/path
export SERVICE_NOW_GET_ASSET_PATH=some/path
export SERVICE_NOW_GET_USER_PATH=some/path
export SERVICE_NOW_GET_DIRECTORATE_PATH=some/path
export SERVICE_NOW_DIT_DEPARTMENT_SYS_ID=1234567890
export UKSBS_INTERFACE=core.uksbs.interfaces.UKSBSStubbed
export UKSBS_CLIENT_ID=xxx
export UKSBS_CLIENT_SECRET=xxx
export UKSBS_AUTHORISATION_URL=xxx
export UKSBS_TOKEN_URL=xxx
export UKSBS_HIERARCHY_API_URL=xxx
export UKSBS_GET_PEOPLE_HIERARCHY=some/path
export UKSBS_LEAVER_API_URL=xxx
export UKSBS_POST_LEAVER_SUBMISSION=some/path
export GOVUK_NOTIFY_API_KEY=xxx
export PEOPLE_DATA_INTERFACE=core.people_data.interfaces.PeopleDataStubbed
# export PEOPLE_DATA_POSTGRES_HOST=
# export PEOPLE_DATA_POSTGRES_DATABASE=
# export PEOPLE_DATA_POSTGRES_USERNAME=
# export PEOPLE_DATA_POSTGRES_PASSWORD=
export HELP_DESK_INTERFACE=help_desk_client.interfaces.HelpDeskStubbed
# export HELP_DESK_CREDS=
export LSD_HELP_DESK_LIVE=False
export GETADDRESS_TOKEN="xxx"
export JML_LEAVING_DIT_GUIDANCE_URL="https://example.com/leaving-dit-guidance/"
export DIT_LOANS_GUIDANCE_URL="https://example.com/loans-guidance/"
export RUN_DJANGO_WORKFLOWS=True

python manage.py collectstatic

