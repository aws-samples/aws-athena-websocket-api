import os
import json
import time
import boto3
import logging
from botocore.client import Config
from botocore.exceptions import ClientError
import cors

logger=logging.getLogger()
logger.setLevel(logging.INFO)

states_client = boto3.client('stepfunctions')
athena_client = boto3.client('athena')

# Global Parameters
params = {
    'Region': os.environ['pRegion'],
    'BucketName': os.environ['pBucketName'],
    'OutputDir': os.environ['pOutputDir'],
    'WorkGroup': os.environ['pWorkGroup'],
    'PreSignerExpireSeconds': "120",
    'StateMachineARN': os.environ['pStepARN'],
    'Database': os.environ['pDatabase']
}


##################################################################
def run_query(client, query):
    """This function executes and sends the query request to Athena."""
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': params['Database']
        },
        ResultConfiguration={
            'OutputLocation': f's3://{params["BucketName"]}/{params["OutputDir"]}/'
        },
        WorkGroup=params["WorkGroup"]
    )
    return response
##################################################################
def validate_query(client, query_id):
    """
    This function validates whether the query request sent to Athena
    is processed and successful.
    """
        # Check state of fetch
    query_status = client.get_query_execution(QueryExecutionId=query_id)['QueryExecution']['Status']['State']

    # If (State: Failed, Cancelled)
    if query_status == 'FAILED' or query_status == 'CANCELLED':
        return None
        # Cant raise exception then user will see "Internal Server Error"
        #raise Exception(f"Athena query id: {query_id} Failed or was Cancelled")
    return query_status
##################################################################
def signed_get_url(event):
    """
    Function to generate the presigned GET url, that can be used to retrieve
    objects from s3 bucket. Required Bucket Name and Object Name to generate url.
    """
    s3 = boto3.client('s3', region_name=params['Region'], config=Config(signature_version='s3v4'))
    # User provided body with object info
    bodyData = json.loads(event['body'])
    try:
        url = s3.generate_presigned_url(ClientMethod='get_object',
                                        Params={'Bucket': params['BucketName'],
                                                'Key': bodyData["ObjectName"]
                                               },
                                        ExpiresIn=int(params['PreSignerExpireSeconds'])
                                        )
        body = {'PreSignedUrl': url, 'ExpiresIn': params['PreSignerExpireSeconds']}
        response = {'statusCode': 200,
                    'body': json.dumps(body),
                    'headers': cors.global_returns["Allow Origin Header"]}
        logger.info(f"[MESSAGE] Response for PreSignedURL: {response}")
    except Exception as e:
        logger.exception(f"[MESSAGE] Unable to generate URL: {str(e)}")
        response = {'statusCode': 502,
                    'body': 'Unable to generate PreSignedUrl',
                    'headers': cors.global_returns["Allow Origin Header"]}
    return response
##################################################################
def handler(event, context):
    logger.info(f"[MESSAGE] Event: {event}")
    logger.info(f"[MESSAGE] API Request Id: {event['requestContext']['requestId']}")
    logger.info(f"[MESSAGE] Lambda Request Id: {context.aws_request_id}")
    
    endpoint = 'https://{}/{}/'.format(event['requestContext']['domainName'],event['requestContext']['stage'])
    api_client = boto3.client('apigatewaymanagementapi',endpoint_url=endpoint)

    ############### MAIN GET ##################################################
    if event['requestContext']['apiId'] is not None:
        body = json.loads(event['body'])

        if body["data"] is None:
            return {"statusCode": 400,
                    "body": json.dumps(cors.global_returns["Missing SQL Query"]),
                    "headers": cors.global_returns["Allow Origin Header"]
            }
        else:
            query = body["data"]

        print('user query:',query)
        # Execution
        qexecute = run_query(athena_client, query)
        query_id = qexecute["QueryExecutionId"]
        logger.info(f"[MESSAGE] Query ID: {query_id}")

        qstate = validate_query(athena_client, query_id)
        logger.info(f"[MESSAGE] Query State: {qstate}")

        # If Athena query request Failed/Cancelled
        if qstate is None:
            return {"statusCode": 502,
                    "body": json.dumps(cors.global_returns["Athena Query Failed"]),
                    "headers": cors.global_returns["Allow Origin Header"]
            }
        elif qstate is 'Succeeded':
            # Get S3 pre-signer
            s3_response = signed_get_url({"body":
                                            json.dumps({"ObjectName":f'{params["OutputDir"]}/{query_id}.csv'})
                                        })
            api_client.post_to_connection(ConnectionId=connectionId, Data=json.dumps(s3_response))
            
            #successfully sent the pre-signed url#deleting the connection
            api_client.delete_connection(ConnectionId=connectionId)
            
            return s3_response
        else:
            response = {'statusCode': 200,
                    'body': json.dumps({"query_id":query_id,"message": "Query has been executed and in progress"}),
                    'headers': cors.global_returns["Allow Origin Header"]}
            print('queued response',response)
            #execute state machine
            connectionId = event['requestContext']['connectionId']
            
            states_client.start_execution(stateMachineArn=params["StateMachineARN"],
            input=json.dumps({"QueryExecution":{"QueryExecutionId":query_id},"ConnectionId": connectionId,"EndpointURL":endpoint}))
            
            return response
    ##### OPTIONS via Servers #####
    else:
        return {"statusCode": 403,
                "body": json.dumps({"messsage": "Forbidden"})
        }