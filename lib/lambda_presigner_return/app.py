import os
import json
import time
import boto3
import logging
from botocore.client import Config
from botocore.exceptions import ClientError
import cors

# Global Parameters
params = {
    'Region': os.environ['pRegion'],
    'PreSignerExpireSeconds': "120",
    'DynamoTable': os.environ['pDynamoTableName']
}

dynamo_client = boto3.resource('dynamodb')

logger=logging.getLogger()
logger.setLevel(logging.INFO)

##################################################################
def delete_dynamo_item(table,con):
    table = dynamo_client.Table(table)
    try:
        response = table.delete_item(
            Key={
                'connectionId': con
            }
        )
    except ClientError as e:
            print(e.response['Error']['Message'])
        
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
                                        Params={'Bucket': bodyData["BucketName"],
                                                'Key': bodyData["ObjectName"]
                                               },
                                        ExpiresIn=int(params['PreSignerExpireSeconds'])
                                        )
        body = {'PreSignedUrl': url, 'ExpiresIn': params['PreSignerExpireSeconds']}
        response = {'statusCode': 200,
                    'body': (body),
                    'headers': cors.global_returns["Allow Origin Header"]}
        logger.info(f"[MESSAGE] Response for PreSignedURL: {response}")
    except Exception as e:
        logger.exception(f"[MESSAGE] Unable to generate URL: {str(e)}")
        response = {'statusCode': 502,
                    'body': 'Unable to generate PreSignedUrl',
                    'headers': cors.global_returns["Allow Origin Header"]}
    return response
##################################################################
def lambda_handler(event, context):
    logger.info(f"[MESSAGE] Event: {event}")

    connectionId = event['ConnectionId']
    endpointURL = event['EndpointURL']
    
    api_client = boto3.client('apigatewaymanagementapi',endpoint_url=endpointURL)
    ############## MAIN GET ##################################################
    if (event['QueryExecution'] is not None and
            'QueryExecutionId' in event['QueryExecution']):

        output = event["body"]["job"]["QueryExecution"]["ResultConfiguration"]["OutputLocation"].split("/",3)
        absolute = output[-1]
        bucket = output[-2]
        
        # Get S3 pre-signer
        s3_response = signed_get_url({"body":
                                            json.dumps({"ObjectName": absolute,"BucketName": bucket })
                                        })
        try:
            api_client.post_to_connection(ConnectionId=connectionId, Data=json.dumps({'pre-signed-url': s3_response['body']['PreSignedUrl'] }))
            response = {"statusCode": 200,"body": "Data Sent"}
            
            #successfully sent the pre-signed url#deleting the connection
            api_client.delete_connection(ConnectionId=connectionId)
            
        except Exception as e:
            logger.exception(f"Unable to send the message: {str(e)}")
            if e.statusCode == 410:
                print('Found stale connection, deleting connectionID:',connectionId)
                delete_dynamo_item(params["DynamoTable"],connectionId)
            response = {'statusCode': 502,
                        'body': 'Unable to generate PreSignedUrl',
                        'headers': cors.global_returns["Allow Origin Header"]}
        return response
    ##### OPTIONS via Servers #####
    else:
        return {"statusCode": 403,
                "body": json.dumps({"messsage": "Forbidden"})
        }