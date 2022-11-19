# AWS Athena Websocket API

This project contains the source code to deploy the WebSocket API framework to access Athena table. It includes the following files and folders -

root
-    lib: lambda and state machine function code
-    resources: architecture diagram for the solution
-    template.yaml: Cloud Formation template to deploy the framework

The application uses several AWS resources, including Lambda functions, State Machine, IAM Role/Policy. These resources are defined in the template.yaml file in this project. You can update the template to add AWS resources through the same deployment process that updates your application code.

Prerequisites

    •	Access to an AWS account
    •	Permissions to create an AWS CloudFormation stack
    •	Permissions to create following resources: 
    •	AWS Glue catalog databases and tables
    •	An API Gateway
    •	Lambda function 
    •	IAM roles
    •	A Step Functions state machine
    •	SNS topic
    •	DynamoDB table

## Enable the WebSocket API
To enable the WebSocket API of API Gateway, complete the following steps: 

*	**Configure the Athena dataset.**

To make the data from the AWS COVID-19 data lake available in the Data Catalog in your AWS account, create a CloudFormation stack using the following [template](https://covid19-lake.s3.us-east-2.amazonaws.com/cfn/CovidLakeStack.template.json). If you’re signed in to your AWS account, the following page fills out most of the stack creation form for you. All you need to do is choose Create stack. For instructions on creating a CloudFormation stack, see [Getting started with AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/GettingStarted.html)

You can also use an existing Athena database to query, in which case you need to update the stack parameters in Step 3. 

*	**Sign in to the Athena console.**

If this is the first time you’re using Athena, you must specify a query result location on Amazon S3. For more information about querying and accessing the data from Athena, see [A public data lake for analysis of COVID-19 data.](https://aws.amazon.com/blogs/big-data/a-public-data-lake-for-analysis-of-covid-19-data/) 

## Deploy the application manually
The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda. It can also emulate your application's build environment and API.

To use the SAM CLI, you need the following tools.

* SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)

You may need the following for local testing.

Python 3 installed
To build and deploy your application for the first time, run the following in your shell:

```bash
sam deploy --guided
```

This command will build a docker image from a Dockerfile and then copy the source of your application inside the Docker image. It will then package and deploy your application to AWS, with a series of prompts:

* **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name. Type a new name or press enter for default name i.e. sam-app
* **AWS Region**: The AWS region you want to deploy your app to. default us-east-2
* **Parameter pAthenaWorkgroupName**: The Athena workgroup. default primary
* **Parameter pGlueDatabaseName**: Glue Catalog Database that would require permission to query. default covid-19
* **Parameter pBucketName**: Parameter that takes the bucket name to store Athena results
* **Parameter TableName**: DynamoDB table to capture the websocket connection state. default websocket_connections
* **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
* **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modified IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
* **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.


## Deploy the application on AWS console

Configure the WebSocket framework using the following [page](https://us-east-2.console.aws.amazon.com/lambda/home#/create/app?applicationId=arn:aws:serverlessrepo:us-east-2:461312420708:applications/aws-app-athena-websocket-integration). Update the parameters pBucketName with the S3 bucket(in Ohio region) that stores the Athena results and also update the database if you want to query an existing database. Check to button to acknowledge creation of IAM roles and click Deploy.

## Test the setup
To test the WebSocket API, you can use wscat, an open-source command line tool.

*	Install NPM.
*	Install wscat:

```bash
npm install -g wscat
```

*	On the console, connect to your published API endpoint by running the following command:

```bash
wscat -c wss://{YOUR-API-ID}.execute-api.{YOUR-REGION}.amazonaws.com/{STAGE}
```

*	To test the runquery function, send a JSON message like the following example. The function sends it back using the callback URL.

```bash
wscat -c wss://{YOUR-API-ID}.execute-api.{YOUR-REGION}.amazonaws.com/dev
connected (press CTRL+C to quit)
{"action":"runquery", "data":"SELECT * FROM \"covid-19\".country_codes limit 5"}
json
< {"pre-signed-url": "https://xxx-s3.amazonaws.com/athena_api_access_results/xxxxx.csv?"}
Json
```

## Clean up
To avoid incurring ongoing charges, delete the resources you provisioned by deleting the CloudFormation stacks CovidLakeStacks and serverlessrepo-AthenaWebSocketIntegration via the AWS CloudFormation console. 


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.


## License

This library is licensed under the MIT-0 License. See the LICENSE file.