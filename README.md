
# ringcentral-survey-bot <!-- omit in toc -->

Example survey bot for ringcentral glip, created with [ringcentral-chatbot-framework](https://github.com/zxdong262/ringcentral-chatbot-python) and [ringcentral-chatbot-factory](https://github.com/zxdong262/ringcentral-chatbot-factory-py).

This simple bot use custom database wrapper(sqlite3), read [bot-logic.py](bot-logic.py) and [sqlite_custom.py](sqlite_custom.py) for more details.

![screenshots/screenshot.png](screenshots/screenshot.png)

## Table of contents <!-- omit in toc -->

- [Prerequisites](#prerequisites)
- [Development & Quick start](#development--quick-start)
- [Test bot](#test-bot)
- [Building and Deploying to AWS Lambda](#building-and-deploying-to-aws-lambda)
- [License](#license)

## Prerequisites

- Python3.6+ and Pip3
- Create the bot App: Login to [developer.ringcentral.com](https://developer.ringcentral.com) and create an `public` `Server/Bot` app with permissions: `ReadContacts, ReadMessages, ReadPresence, Contacts, ReadAccounts, SMS, InternalMessages, ReadCallLog, ReadCallRecording, WebhookSubscriptions, Glip`

## Development & Quick start

```bash

# use virtualenv
pip3 install virtualenv # might need sudo

# init virtual env
virtualenv venv --python=python3

# use env
source ./venv/bin/activate

# install deps
pip install -r requirements.txt

# run ngrok proxy
# since bot need https server,
# so we need a https proxy for ringcentral to visit our local server
./bin/proxy
# will show:
# Forwarding https://xxxxx.ngrok.io -> localhost:8989

# create env file
cp .sample.env .env
# then edit .env, set proper setting,
# and goto your ringcentral app setting page, set OAuth Redirect URI to https://https://xxxxx.ngrok.io/bot-oauth
RINGCENTRAL_BOT_SERVER=https://xxxxx.ngrok.io

## for bots auth required, get them from your ringcentral app page
RINGCENTRAL_BOT_CLIENT_ID=
RINGCENTRAL_BOT_CLIENT_SECRET=

# create custom bot config file
cp bot-logic.py config.py

# run local dev server
./bin/start
```

## Test bot

- Goto your ringcentral app's bot section, click 'Add to glip'
- Login to [https://glip-app.devtest.ringcentral.com](https://glip-app.devtest.ringcentral.com), find the bot by searching its name. Talk to the bot.
- Edit config.py to change bot bahavior and test in [https://glip-app.devtest.ringcentral.com](https://glip-app.devtest.ringcentral.com)

## Building and Deploying to AWS Lambda

AWS Lambda with API Gateway and DynamoDB would give us a flexible way to deploy the bot.

This requires Nodejs 8.10+/npm, recommend using [nvm](https://github.com/creationix/nvm) to install nodejs/npm.

*Be aware that AWS Lambda **ONLY works in linux** on an x64 architecture. For **non-linux os**, we need **docker** to build dependencies, should [install docker](https://docs.docker.com/docker-for-mac/) first.

Get an AWS account, create `aws_access_key_id` and `aws_secret_access_key` and place them in `~/.aws/credentials`, like this:

```bash
[default]
aws_access_key_id = <your aws_access_key_id>
aws_secret_access_key = <your aws_secret_access_key>
```

For more information, refer to [https://docs.aws.amazon.com/general/latest/gr/aws-security-credentials.html](https://docs.aws.amazon.com/general/latest/gr/aws-security-credentials.html)

```bash

# install serverless
npm i

# create serverless.yml
cp dev/lambda/serverless.sample.yml dev/lambda/serverless.yml
```

Edit `dev/lambda/serverless.yml`, and make sure you set the proper name and required env.

```yml
# you can define service wide environment variables here
  environment:
    ENV: production
    # ringcentral apps

    ## for bots auth, required
    RINGCENTRAL_BOT_CLIENT_ID:
    RINGCENTRAL_BOT_CLIENT_SECRET:

    ## for user auth, could be empty if do not need user auth
    RINGCENTRAL_USER_CLIENT_ID:
    RINGCENTRAL_USER_CLIENT_SECRET:

    ## common
    RINGCENTRAL_SERVER: https://platform.devtest.ringcentral.com
    RINGCENTRAL_BOT_SERVER: https://xxxxx.execute-api.us-east-1.amazonaws.com/dev

    # db
    DB_TYPE: dynamodb
    DYNAMODB_TABLE_PREFIX: ringcentral-bot
    DYNAMODB_REGION: us-east-1
    DYNAMODB_ReadCapacityUnits: 1
    DYNAMODB_WriteCapacityUnits: 1

```

Deploy to AWS Lambda with `bin/deploy`

```bash
# Run this cmd to deploy to AWS Lambda
bin/deploy
```

After successful deploy, you will get the https api url:

```bash
Service Information
service: ringcentral-bot
stage: dev
region: us-east-1
stack: ringcentral-bot-dev
api keys:
  None
endpoints:
  ANY - https://dddddd.execute-api.us-east-1.amazonaws.com/dev/{action+}
  GET - https://dddddd.execute-api.us-east-1.amazonaws.com/dev/
```

Relpace `RINGCENTRAL_BOT_SERVER: https://xxxxx.execute-api.us-east-1.amazonaws.com/dev` in serverless.yml with
`RINGCENTRAL_BOT_SERVER: https://dddddd.execute-api.us-east-1.amazonaws.com/dev`
 and run `bin/deploy` to deploy again.

Watch Lambda server log by run:

```bash
bin/watch
```

Do not forget to set your RingCentral app's redirect URL to Lambda's API Gateway URL, `https://dddddd.execute-api.us-east-1.amazonaws.com/dev/bot-oauth` for bot app.

## License

MIT
  