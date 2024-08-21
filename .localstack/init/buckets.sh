#!/bin/bash
set -x
awslocal s3 mb s3://jml.local

set +x
echo "S3 Configured"