#!/bin/bash

set -eu

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <prefix>"
    exit 1
fi

PREFIX=$1

if [[ -e sources.zip ]]; then
    rm sources.zip
fi

echo "Packaging sources"
zip --quiet --exclude 'app/build/*' -r sources.zip app gradlew gradle build.gradle settings.gradle gradle.properties pipeline/buildspec.yaml

pipeline_stack_name="${PREFIX}-device-farm-demo-pipeline"
source_bucket=$(aws cloudformation describe-stacks \
    --output text \
    --stack-name ${pipeline_stack_name} \
    --query 'Stacks[0].Outputs[?OutputKey==`SourceBucket`].OutputValue')

echo "Pushing sources to ${source_bucket}"
aws s3 cp sources.zip s3://${source_bucket}/sources.zip
