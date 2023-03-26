import os
import openai
import streamlit as st
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

# Retrieves the appropriate json file and extracts the default questions
def chatgpt_default_ques(transcript_file):

    trans_response = s3client.get_object(Bucket=user_bucket, Key=transcript_file)
    json_content = trans_response['Body'].read().decode('utf-8')
    questions = json_content.split('\"')[3]
    return questions

# Retrieves the appropriate json file and extracts the default answers
def chatgpt_default_ans(transcript_file):

    trans_response = s3client.get_object(Bucket=user_bucket, Key=transcript_file)
    json_content = trans_response['Body'].read().decode('utf-8')
    answers = json_content.split('\"')[7]
    return answers

# Retrieves the appropriate json file and extracts the transcript
def chatgpt_transcript(transcript_file):

    trans_response = s3client.get_object(Bucket=user_bucket, Key=transcript_file)
    json_content = trans_response['Body'].read().decode('utf-8')
    transcript = json_content.split('\"')[3]
    return transcript

def chatgpt_response(prompt):
    # Sending an API call to initiate chat completion through openai API
    response = openai.Completion.create(
    model="text-davinci-003",
    prompt=prompt,
    temperature=0.7,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    return response

# Call the list_objects_v2 method to list all the objects in the folder
response = s3client.list_objects_v2(Bucket=user_bucket, Prefix='current/')
processed_files =  []

# Print the object keys returned by the response
for obj in response.get('Contents', []):
    file_name = obj['Key']
    processed_files.append(str(file_name).split('/')[-1])

# Create a section for asking generic questions
st.header("Generic Questions")

# Call the list_objects_v2 method to list all the objects in the folder
response = s3client.list_objects_v2(Bucket=user_bucket, Prefix='current/')
file_list = []

# Print the object keys returned by the response
for obj in response.get('Contents', []):
    file_name = obj['Key']
    file_list.append(str(file_name).split('/')[-1])

audio_file = st.selectbox(
    'Select the Audio file : ',
    (file_list))
st.write('You selected :', audio_file)

if audio_file in processed_files and audio_file not in ['', 'Baby-Calm-Down_320(PaglaSongs).mp3', 'likeit_updated.wav']:

    # Splitting the file name to remove the extension
    audio_file = audio_file.split('.')[0]
    transcript_file = f'processed/{audio_file}'

    # Retrieves the appropriate json file and extracts the transcript
    transcript = chatgpt_transcript(transcript_file)

    # Create path to retrieve files
    default_ques = f'processed/{audio_file}_deafult_ques'

    # Retrieves the appropriate json file and extracts the default questions
    questions = chatgpt_default_ques(default_ques)

    # Retrieves the appropriate json file and extracts the default answers
    answers = chatgpt_default_ans(default_ques)

    st.write('Transcript')

    st.write(transcript)

    st.header("")

    st.write('Default questions')

    for i in questions.split('\\n'):
        st.write(i)

    for i in answers.split('\\n'):
        st.write(i)

    # Create a text box for manually entering a question
    user_input = st.text_input("Enter a question manually")
    
    if 'user_input_list' not in locals():
        user_input_list = []

    # user_ques = ''
    transcript_ext = transcript

    # Create a button to submit the question
    if st.button("Ask Question"):
        # Add user input to user_ques
        # user_ques += user_input + "\n"
        
        user_input_list.append(user_input)
        st.write(user_input_list)
        for i in user_input_list:
            # Update transcript_ext with new user_ques
            transcript_ext += f'  \n{i}'

        gpt_response = chatgpt_response(transcript_ext)
        # gpt_response = transcript_ext
        st.write(gpt_response['choices'][0]['text'])
        # print(transcript_ext)

    st.header("")