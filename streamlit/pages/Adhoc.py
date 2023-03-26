from io import BytesIO
import io
import json
import os
import openai
import streamlit as st
import tempfile
import boto3

user_bucket = os.environ.get('USER_BUCKET_NAME')

# Create a boto3 client for S3
s3client = boto3.client('s3', 
                        region_name='us-east-1',
                        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key=os.environ.get('AWS_SECRET_KEY')
                        )

# Accessing openai API through API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def chatgpt_default_ques(transcript_file):

    trans_response = s3client.get_object(Bucket=user_bucket, Key=transcript_file)
    json_content = trans_response['Body'].read().decode('utf-8')
    questions = json_content.split('\"')[3]
    return questions

def chatgpt_default_ans(transcript_file):

    trans_response = s3client.get_object(Bucket=user_bucket, Key=transcript_file)
    json_content = trans_response['Body'].read().decode('utf-8')
    answers = json_content.split('\"')[7]
    return answers

def chatgpt_transcript(transcript_file):

    trans_response = s3client.get_object(Bucket=user_bucket, Key=transcript_file)
    json_content = trans_response['Body'].read().decode('utf-8')
    transcript = json_content.split('\"')[3]
    return transcript

# Set page title
st.markdown("<h1 style='text-align: center;'>Transcribe audio file</h1>", unsafe_allow_html=True)
st.header("")

# Call the list_objects_v2 method to list all the objects in the folder
response = s3client.list_objects_v2(Bucket=user_bucket, Prefix='current/')
file_list = []

# Print the object keys returned by the response
for obj in response.get('Contents', []):
    file_name = obj['Key']
    file_list.append(str(file_name).split('/')[-1])


audio_file = st.selectbox(
    'Select the Audio file :',
    (file_list))
st.write('You selected :', audio_file)

transcript_file = f'processed/{audio_file}'

st.header("")

# Create a button to upload a file
if st.button('Transcribe'):
    if audio_file is None:
        st.write("Please upload a file")
        
    # else:

        # # # Set up the S3 and Transcribe clients
        # # transcribe = boto3.client('transcribe', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-west-2')

        # file_key = f'current/{audio_file}'

        # # # Download the audio file from S3 to a temporary file
        # # with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_audio_file:
        # #     with open('FILE_NAME', 'wb') as f:
        # #         s3client.download_fileobj(user_bucket, file_key, f)

        # #     # Transcribe the audio file using the Whisper API
        # #     transcript = openai.Audio.transcribe("whisper-1", tmp_audio_file.read())

        # # Download the audio file to a temporary file
        # with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_audio_file:
        #     tmp_audio_file.write(f.read())
        #     s3client.download_file(user_bucket, file_key, tmp_audio_file.name)
        #     tmp_audio_file.seek(0)
        #     audio_data = tmp_audio_file.read()

        # # Transcribing the audio file to get the transcript
        # with io.BytesIO(audio_data) as audio_file:
        #     audio_file.name = "audio.mp3"  # Set the file name manually
        #     transcript = openai.Audio.transcribe("whisper-1", audio_file)

        # st.write(transcript)


# Create a section for asking generic questions
st.header("Generic Questions")

# Display some example questions
st.write("1. Give me the summary.")
st.write("2. How many speakers are there in the conversation?")
st.write("3. What is the tone of the conversation?")

# Create a text box for manually entering a question
user_input = st.text_input("Enter a question manually")

# Create a button to submit the question
ask_button = st.button("Ask Question")

# List all objects in the bucket
response = s3client.list_objects_v2(Bucket=user_bucket)

# Print the name of each object
for obj in response['Contents']:
    st.write(obj['Key'])

st.header("")

st.write('transcript')

transcript = chatgpt_transcript('processed/plans')
st.write(transcript)

st.header("")

st.write('default ques')

questions = chatgpt_default_ques('processed/test_audio_deafult_ques')
st.write(questions)
for i in questions.split('\\n'):
    st.write(i)

answers = chatgpt_default_ans('processed/test_audio_deafult_ques')
for i in answers.split('\\n'):
    st.write(i)