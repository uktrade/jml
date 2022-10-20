# Joiners Movers Leavers service

## Developer notes
Notes that must be read and understood by developers working on the service.

### UK SBS Person ID
The person_id field that we get back from UK SBS must NOT be exposed to any end user of the service, it must also not be exposed in any logs on this service.
This field contains sensitive information that is only to be used for the purposes of getting Hierarchy data from the UK SBS API and submitting it back to UK SBS to inform them of a Leaver.

## Project Documentation

- [Environment Variables](./environment-variables.md)
- [Emails](./emails.md)
- [UK SBS](./uksbs.md)
