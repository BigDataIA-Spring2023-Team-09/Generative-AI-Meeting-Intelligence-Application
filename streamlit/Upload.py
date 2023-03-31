import streamlit as st
import os
import boto3
from dotenv import load_dotenv
# Note: you need to be using OpenAI Python v0.27.0 for the code below to work
# import Diarization
import requests
import requests

load_dotenv()



s3client = boto3.client('s3', 
                        region_name='us-east-1',
                        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key=os.environ.get('AWS_SECRET_KEY')
                        )

s3 = boto3.resource('s3', 
                    region_name = 'us-east-1',
                    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                    aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                    )

user_bucket = os.environ.get('USER_BUCKET_NAME')

os.environ['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY')
os.environ['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_KEY')

hf_token = os.environ.get('HF_TOKEN')

# Set page title
st.markdown("<h1 style='text-align: center;'>Meeting Intelligence Application</h1>", unsafe_allow_html=True)
st.header("")

# Create a file uploader to attach an audio file
audio_file = st.file_uploader("Attach an Audio File", type=["mp3", "wav"])

if audio_file:
    # Display some information about the file
    st.write("File Name:", audio_file.name)
    st.write("File Type:", audio_file.type)

else:
    st.write("No file uploaded.")

st.header("")

# Create a dropdown to select audio language
language = st.selectbox("Select audio language", ["English", "Other"])

# Create a button to upload a file
if st.button('Upload without DAG'):

    st.write('This performs diarization of the audio file and gives the lines spoken by different speakers but is not possible to host it on cloud.')

    # if audio_file is None:
    #     st.write("Please upload a file")
        
    # else:
    #     # specify the bucket and the file key
    #     file_key = f'processed/{audio_file.name}'

    #     # list all objects in the bucket with the given prefix
    #     response = s3client.list_objects_v2(Bucket=user_bucket, Prefix=file_key)

    #     # check if the file exists in the list of objects
    #     if 'Contents' in response:
    #         for obj in response['Contents']:
    #             if obj['Key'] == file_key:
    #                 st.write('File already exists. Please give another name.')
    #                 break
    #     else:
    #         # Upload the file to the unprocessed folder in S3 bucket
    #         with open(audio_file.name, "rb") as f:
    #             s3client.upload_fileobj(f, str(user_bucket), f'current/{str(audio_file.name)}')
    #         message=Diarization.read_audio_file_from_s3(audio_file.name, language)
    #         st.write(message)
    #         # Remove the selected file
    #         audio_file = None

if (st.button("Upload with DAG")):
    if audio_file is None:
        st.write("Please upload a file")

    else:
        # specify the bucket and the file key
        file_key = f'processed/{audio_file.name}'

        # list all objects in the bucket with the given prefix
        response = s3client.list_objects_v2(Bucket=user_bucket, Prefix=file_key)

        # check if the file exists in the list of objects
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'] == file_key:
                    st.write('File already exists. Please give another name.')
                    break
        else:
            # Upload the file to the unprocessed folder in S3 bucket
            with open(audio_file, "rb") as f:
                s3client.upload_fileobj(f, str(user_bucket), f'current/{str(audio_file.name)}')
            
            #Trigger DAG with file and language as parameters
            airflow_url = "http://34.74.233.133:8080/api/v1/dags/adhoc/dagRuns"
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "Authorization": "Basic YWlyZmxvdzQ6YWlyZmxvdzQ=",
            }
            json_data = {"conf" : {"file_name": audio_file.name, "language": language}}
            response = requests.post(airflow_url, headers=headers, json=json_data)
            if response.status_code == 200 or response.status_code == 201:
                response_json = response.json()
                st.write(
                    "DAG triggered successfully",
                    response_json["execution_date"],
                    response_json["dag_run_id"],
                )
            else:
                st.write(f"Error triggering DAG: {response.text}", None, None)

            # Remove the selected file
            audio_file = None

            st.write("File uploaded")