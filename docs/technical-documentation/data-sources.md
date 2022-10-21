# Data Sources

## Internal systems

### People Finder (Digital Workspace)

- want the people finder data
- rest api with hawk authentication
- ingest it all in one go daily
  - 1 request per page `R(n / page_size)`
- activity_stream/staff_sso.py

### Activity Stream

- want the sso data
- rest api with hawk authentication
- ingest it all in one go daily
  - 1 request per 1000 hits (paged) `R(n / 1000)`
- core/people_finder/client.py

### Data Workspace

- want the people data report
- connection/copy or the table/database
- 1 query per person `Q(n)`
- core/people_data/interfaces.py

## External systems

### UKSBS

- requests are made as part of the leavers journey
  - hierarchy (line manager) `R(n)`
  - hierarchy (line reports) `R(n)`
  - while loop:
    - try get leaver `R(n)`
  - while loop:
    - try get leavers line manager `R(n)`
  - post to uksbs `R(n)`

range = `R(5n)` -> `R(inf(n))`

### ServiceNow

- want the equipment data
- rest api
- ingest it all in one go daily
- 2 request per person `R(2n)`
- core/service_now/utils.py
