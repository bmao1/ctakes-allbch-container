#!/bin/bash

# May have to also set AWS key parameters here, potentially passed in as tags as well.
aws=/usr/local/bin/aws

s3_bucket=`$aws ec2 describe-tags --filters Name=key,Values=s3_bucket | jq --raw-output '.Tags[0].Value'`
s3_output_path=`$aws ec2 describe-tags --filters Name=key,Values=s3_out | jq --raw-output '.Tags[0].Value'`
keyId=$($aws secretsmanager get-secret-value --secret-id arn:aws:secretsmanager:us-east-1:718952877825:secret:master-fWTVY2 --output text --query SecretString | jq --raw-output '."bch-pl-lzprod-avl-dev-kms-s3"')

for fn in $1/*.json; do
    aws-encryption-cli --encrypt --input $fn --wrapping-keys key=$keyId --encryption-context purpose=test --metadata-output `basename $fn`.metadata --output $fn.encrypted
    $aws s3 cp $fn.encrypted s3://$s3_bucket/$s3_output_path/ --sse aws:kms --sse-kms-key-id $keyId
done

for fn in $1/*.csv; do
    aws-encryption-cli --encrypt --input $fn --wrapping-keys key=$keyId --encryption-context purpose=test --metadata-output `basename $fn`.metadata --output $fn.encrypted
    $aws s3 cp $fn.encrypted s3://$s3_bucket/$s3_output_path/ --sse aws:kms --sse-kms-key-id $keyId
done

