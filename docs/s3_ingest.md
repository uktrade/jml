## Staff SSO files
Files containing a full extract of data in the staff SSO system will be delivered twice a day, to the JML S3 bucket in the file key format `data-flow-exports/StaffSSOUsersPipeline/TIMESTAMP/full_ingestion.jsonl.gz`. The delivery time is not guaranteed, as data flow produces these files as part of its pipeline scheduler. The pipeline to produce this file is scheduled to begin at 00.00 UTC and 12.00 UTC every day, however due to the number of pipelines in data flow it can sometimes take hours to obtain a free worker to produce the staff SSO file. The file generated at 12.00 UTC will usually be delivered quickly after the scheduled start time, as most pipelines in data flow are scheduled to run overnight

### File format
The file delivered will be a gzip compressed jsonl file, containing 1 line per entry in the staff SSO system. Using jsonl means the file can be streamed from S3 and read 1 line at a time in a similar way to a CSV file. If using the `smart_open` package to read the file, the file will be automatically decompressed when it detects a `.gz` file extension.

### File contents
The contents of this file will be the same json structure produced by the activity stream API, this is an example of the output
```
{"published": "2024-09-04T14:58:05.864Z", "object": {"id": "dit:StaffSSO:User:d1966051-cabc-40f2-8b56-16d42e30971f", "type": "dit:StaffSSO:User", "name": "Mr. Ernest Ramos DDS", "dit:StaffSSO:User:userId": "d1966051-cabc-40f2-8b56-16d42e30971f", "dit:StaffSSO:User:emailUserId": "ograham@example.net", "dit:StaffSSO:User:contactEmailAddress": "kaylamiller@example.com", "dit:StaffSSO:User:joined": "2024-09-04T14:58:05.867Z", "dit:StaffSSO:User:lastAccessed": "2024-09-04T14:58:05.867Z", "dit:StaffSSO:User:permittedApplications": [], "dit:StaffSSO:User:status": "inactive", "dit:StaffSSO:User:becameInactiveOn": "2024-09-04T14:58:05.867Z", "dit:firstName": "Roberta", "dit:lastName": "Brown", "dit:emailAddress": ["jlee@example.net"]}}
```