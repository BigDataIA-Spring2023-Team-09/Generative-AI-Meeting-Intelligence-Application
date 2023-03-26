from io import BytesIO
import streamlit as st
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

s3client = boto3.client('s3', 
                        region_name='us-east-1',
                        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key=os.environ.get('AWS_SECRET_KEY')
                        )

user_bucket = os.environ.get('USER_BUCKET_NAME')

# Set page title
st.markdown("<h1 style='text-align: center;'>MODEL AS A SERVICE</h1>", unsafe_allow_html=True)
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

# Create a button to upload a file
if st.button('Upload'):
    if audio_file is None:
        st.write("Please upload a file")
        
    else:

        
        # specify the bucket and the file key
        file_key = f'current/{audio_file.name}'

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
            with open(audio_file.name, "rb") as f:
                s3client.upload_fileobj(f, str(user_bucket), f'unprocessed/{str(audio_file.name)}')

            # Remove the selected file
            audio_file = None

            st.write("File uploaded")