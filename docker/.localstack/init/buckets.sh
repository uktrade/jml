#!/bin/bash
set -x

# Create the S3 bucket
awslocal s3 mb s3://jml.local
echo "jml.local S3 bucket created"

# Add files to the bucket
awslocal s3 cp /examples/people_data.jsonl s3://jml.local/data-flow/exports/local-development/ExportPeopleDataNewIdentityPipeline/20241106T143632/full_export.jsonl
echo "People Data file added to bucket"
awslocal s3 cp /examples/staff_sso.jsonl s3://jml.local/data-flow/exports/local-development/StaffSSOUsersPipeline/20241106T000000/full_ingestion.jsonl
echo "Staff SSO file added to bucket"

set +x
echo "S3 Configured"