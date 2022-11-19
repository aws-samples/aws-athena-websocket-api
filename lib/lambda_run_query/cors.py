import json


# Allowed Origins for CORS
allowed_origins = ['http://localhost:3000']

# Util Global Returns
global_returns = {
    "Allow Origin Header": {"Access-Control-Allow-Origin" : "*"},
    "Missing Parameters": {"message": "Missing required request parameters: [queryid]. Optional: [format]"},
    "Invalid Format": {"message": "Format not supported. Available formats: [json, csv]."},
    "Invalid Parameters": {"message": "Invalid parameters. Check for required request parameters: [queryid]. Optional: [format]"},
    "Invalid Parameter Values": {"message": "Invalid parameter values. Must meet the following requirements. queryid: [77eefca2-f799-4ed8-bbb6-c4b6dfea1159]"},
    "Athena Query Failed": {"message": 'Unable to process the Athena  request.'},
    "Failed to write json": {"message": 'Failed to process json format request.'},
    "Failed to read csv": {"message": 'Unable to process this request.'},
}

