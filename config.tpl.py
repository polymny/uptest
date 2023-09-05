mailer = {
    "username": "$USERNAME",
    "password": "$PASSWORD",
    "host": "$HOST",
    "port": "$PORT",
    "dest": "$DEST",
}

urls = "$URLS".split(' ')

if "$S3_KEY" != "":
    s3 = {
        "endpoint": "$S3_ENDPOINT",
        "region": "S3_REGION",
        "key": "S3_KEY",
        "bucket": "S3_BUCKET",
        "secret": "S3_SECRET",
    }
