import aiohttp
import json
import os
#from flask import current_app
import re
import base64

## III Login user MFiles

async def login_user_for_mfiles():
    #print(1)
    #"username":"mRemit" "userpassword":"SzirD|8@"}
    request_data = {
        "requestid": 200001,
        "requesttype": "Login",
        "requestsrc": "Python External Layer for LLM",
        "requestdata": {
            "username": "mRemit",
            "userpassword": "SzirD|8@"
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://fileserv-admin.machint.com/login',
                json=request_data,
                headers={
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            ) as response:
                
                response_text = await response.text()
                
                final_response_from_mfiles = json.loads(response_text)
                
                if final_response_from_mfiles['response']['message'] == "User Loggedin Successfully":
                    return final_response_from_mfiles
                else:
                    return "Failed"
    except Exception as err:
        print(err)
        return "Failed"

## IV Save Image in MFiles directly files from another request

async def save_in_mfiles_using_directly_file(mfiles_user_details, actual_request_data, file):
    request_data = {
        'status': 1,
        "requestid": 200002,
        "requesttype": "Login",
        "requestsrc": "Python External Layer for LLM",
        "project_name": actual_request_data['request_data']['username']
    }
    
    try:
        
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()            
            form.add_field('file', aiohttp.payload.BytesPayload(file), 
                        #    filename=file.filename,
                        filename="1.jpg", 
                           content_type='application/octet-stream')
            
            for key, value in request_data.items():
                form.add_field(key, str(value))
            
                            
            # Make the POST request to MFiles API
            async with session.post(
                'https://fileserv-admin.machint.com/file-upload',
                data=form,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    "Authorization": f"Bearer {mfiles_user_details['jwt_token']}"
                }
            ) as response:
                response_text = await response.text()
                print("Response from MFiles:", response_text)
                final_response_from_mfiles = json.loads(response_text)
                #print(4)
                
                if final_response_from_mfiles['responsedata']['message'] == "File uploaded successfully":
                    return final_response_from_mfiles['responsedata']
                else:
                    return None
                
    except Exception as err:
        #print("Error for Save Image in MFiles:", err)
        return None

## IVA Save Image in MFiles directly files from another request

async def save_in_mfiles_using_file_path(mfiles_user_details, actual_request_data):
    request_data = {
        'status': 1,
        "requestid": 200002,
        "requesttype": "Login",
        "requestsrc": "Python External Layer for LLM",
        "project_name": actual_request_data['request_data']['username']
    }
    try:
        file_path = actual_request_data['request_data']['file_path']
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field('file', open(file_path, 'rb'), filename=os.path.basename(file_path))
            for key, value in request_data.items():
                form.add_field(key, str(value))
                
            async with session.post(
                'https://fileserv-admin.machint.com/file-upload',
                data=form,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    "Authorization": f"Bearer {mfiles_user_details['jwt_token']}"
                }
            ) as response:
                response_text = await response.text()
                #print("response for MFiles SAVE Files...>", response, type(response), response_text)
                final_response_from_mfiles = json.loads(response_text)
                if final_response_from_mfiles['responsedata']['message'] == "File uploaded successfully":
                    return final_response_from_mfiles['responsedata']
    except Exception as err:
        #print("error for Save Image in MFiles is ...>", err)
        return False

async def get_filename_from_content_disposition(headers):
    """
    Extracts filename from the content-disposition header.
    Returns None if the header is not present or if the filename could not be extracted.
    """
    if 'content-disposition' in headers:
        content_disposition = headers['content-disposition']
        match = re.search(r'filename="?([^"]+)"?', content_disposition)
        if match:
            return match.group(1)
    return None

## V Download Files from MFiles Locally

async def download_files_from_mfiles_to_desired_folder(file_name):
    
    try:
        login_user_details = await login_user_for_mfiles()
        
        if login_user_details is not None and isinstance(login_user_details, dict):
            #print(login_user_details['response']['jwt_token'])
            params = {
                "file_name": file_name,
                "project_name": "mRemit"
            }
            #print("params in download file", params)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://fileserv-admin.machint.com/get-uploaded-file',
                    params=params,
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        "Authorization": f"Bearer {login_user_details['response']['jwt_token']}"
                    }
                ) as response:
                    #print("response from mfiles", response)
                    if response.status == 200:
                        
                       data =  await response.read()
                       return base64.b64encode(data).decode('utf-8')
                       #return data
                        
                        
                    else:
                        
                        return  None
        
    except Exception as err:
        return  None


## I Main Function to Login in to MFiles and Save File directly

async def save_file_in_mfiles(request_data, file):
    
    login_user_details = await login_user_for_mfiles()
    
    if login_user_details is not None and isinstance(login_user_details, dict):
        save_files = await save_in_mfiles_using_directly_file(login_user_details['response'], request_data, file)
        if save_files is not None and isinstance(save_files, dict):
            return save_files
        else:
            return None
    else:
        return None

## II Main Function to Login in to MFiles and Save File directly using File Path

async def save_file_with_filepath_in_mfiles(request_data):
    login_user_details = await login_user_for_mfiles(request_data)
    #print("login user details...>", login_user_details)
    if login_user_details is not None and isinstance(login_user_details, dict):
        save_files = await save_in_mfiles_using_file_path(login_user_details['response'], request_data)
        if save_files is not None and isinstance(save_files, dict):
            return save_files
        else:
            return "Failed"
    else:
        return "Failed"

async def get_currency(from_currency='', to_currency=''):
    # Initialize the default response structure
    rate_response = {
        "timestamp": None,
        "base": from_currency,
        "all_rates": [],
        "rate": None,
        "success": False
    }

    try:
        API_KEY = "08fdcc648ef878f5f43d2019ebfb3513"
        url = f"https://data.fixer.io/api/latest?access_key={API_KEY}"

        # Use aiohttp for asynchronous HTTP requests
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # Check if the response status is 200 (OK)
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if the data contains success = True
                    if data and data.get('success', False):
                        rates = data.get("rates", {})

                        # Ensure 'from_currency' and 'to_currency' exist in the response
                        if from_currency not in rates:
                            print(f"Error: Base currency '{from_currency}' not found in response rates.")
                            return rate_response

                        # Set the base and all rates
                        rate_response["base"] = data["base"]
                        rate_response["timestamp"] = data["timestamp"]
                        rate_response["all_rates"] = rates

                        # Calculate rate if 'to_currency' is provided and exists
                        if to_currency and to_currency in rates:
                            rate_response["rate"] = rates[to_currency]
                        else:
                            # Default rate when the target currency is not provided or found
                            rate_response["rate"] = 1.0

                        # Mark the operation as successful
                        rate_response["success"] = True
                        return rate_response
                    else:
                        print(f"Error: API response does not indicate success: {data}")
                        return rate_response
                else:
                    print(f"Error: Received non-200 response code {response.status} from the API.")
                    return rate_response
    except Exception as e:
        # Log any exceptions that occur during the API call
        print(f"Exception occurred while fetching currency data: {str(e)}")
        return rate_response

# async def get_currency(from_currency='',to_currency=''): 
#     rate = {"timestamp": None,"base": from_currency,"all_rates":[],"rate":None, "success":False}
#     try:
#         API_KEY = "8014d3f75c57de66c72f5efa73b5edb5"
#         url = f"https://data.fixer.io/api/latest?access_key={API_KEY}"
#         querystring = {"format":1,"base":from_currency}
#         async with aiohttp.ClientSession() as session:
#                 async with session.get(url, params=querystring, ) as response:
#                     #print("response from mfiles", response)
                    
#                     if response.status == 200:
#                         data = await response.json()
#                         if data and data.get('success', False):
#                             rates = data["rates"]
                            
#                             if to_currency:
#                                 rate = data["rates"].get(to_currency, 1)

#                             result = {"timestamp": data["timestamp"],"base": data["base"],"all_rates":rates,"rate":rate,"success":True}
#                             return result                          
#                         else:
#                             return rate
#                     else:                                             
#                         return rate
#     except Exception as E:                
#         return rate