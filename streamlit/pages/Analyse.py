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

def chatgpt_api_call(my_transcript, ques_list, ans_list, count):

    my_dict={
        "questions":ques_list,
        "answers":ans_list
    }

    custom_response = openai.Completion.create(
        model="text-davinci-003",
        prompt=str(my_transcript) + '\n' + str(my_dict) + '\n' + "Given this meeting transcript, and question/answers, answer the last question. Don't return the question again.",
        max_tokens=1000,
        temperature=0
    )
    
    return custom_response["choices"][0]["text"]

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
    updated_transcript = []
    trans_response = s3client.get_object(Bucket=user_bucket, Key=transcript_file)
    transcript = trans_response['Body'].read().decode('utf-8')
    transcript=transcript.replace('[','').replace(']','').replace('", ','').replace('"','').replace('\'','').replace('\\n, ','\\n')
    updated_transcript = transcript.split('\\n')
    # del updated_transcript[-1]
    
    return updated_transcript

# Set page title
st.markdown("<h1 style='text-align: center;'>Transcribe audio file</h1>", unsafe_allow_html=True)
st.header("")

# Call the list_objects_v2 method to list all the objects in the folder
response = s3client.list_objects_v2(Bucket=user_bucket, Prefix='processed/')
file_list = []

transcript=[]

if 'new_query' not in st.session_state:
    st.session_state.new_query='not new'
    st.session_state.user_ques=[]
    st.session_state.user_ans=[]

# Print the object keys returned by the response
for obj in response.get('Contents', []):
    if (".wav" in obj['Key']):
        file_name = obj['Key']
        file_list.append(str(file_name).split('/')[-1])

audio_file = st.selectbox(
    'Select the Audio file :',
    (file_list))
st.write('You selected :', audio_file)

if ((audio_file!="") and (audio_file!="No options to select.")):
    transcript_file = f'processed/{audio_file.split(".")[0]}'+'.txt'

st.header("")

# Create a button to upload a file
if st.button('View transcription'):
    if (transcript_file=='processed/'):
        st.write("Please select a file")
    else:

        st.subheader("Meeting transcript")

        transcript = chatgpt_transcript(transcript_file)
        for i in range(len(transcript)):
            # st.text(transcript[i])
            st.text_area("transcript", value=transcript[i], label_visibility="hidden")

        answers = chatgpt_default_ans(f'processed/{audio_file.split(".")[0]}'+'.txt'+'_default_ques')

        st.subheader("")

        st.subheader('Meeting details')

        # Display some example questions
        default_ques = ["1. What is this meeting about?", "2. How many speakers are there in the conversation?", "3. What are the minutes of this meeting?"]
        default_ans=[]

        default_ans.append(answers.split('\\nA2:')[0].replace("\\nA1:","").replace("\\n",""))
        answers=answers.split('\\nA2:')[1]
        default_ans.append(answers.split('\\nA3:')[0].replace("\\nA2:",""))
        default_ans.append(answers.split('\\nA3:')[1].replace("\\nA3:","").replace("\\n",'\n'))

        for i in range(0,3):
            st.write(default_ques[i])
            st.write(default_ans[i])

        st.session_state.new_query=''
        st.session_state.user_ques=[]
        st.session_state.user_ans=[]

# Create a text box for manually entering a question
user_input = st.text_input("Enter a question manually")

if st.button('Ask a question'):
    if (transcript_file=='processed/'):
        st.write("Please select a file")
    if (user_input==""):
        st.write("Please type-in a question")
    else:

        if st.session_state.user_ques==[]:
            st.session_state.user_ques.append(chatgpt_default_ques(f'processed/{audio_file.split(".")[0]}'+'.txt'+'_default_ques'))
            st.session_state.user_ans.append(chatgpt_default_ans(f'processed/{audio_file.split(".")[0]}'+'.txt'+'_default_ques'))

        count=len(st.session_state.user_ques)
        st.session_state.user_ques.append(f'\nQ{count+3}:'+user_input)

        st.write(chatgpt_api_call(transcript, st.session_state.user_ques, st.session_state.user_ans, count))

        st.session_state.user_ans.append(chatgpt_api_call(transcript, st.session_state.user_ques, st.session_state.user_ans, count))

        st.subheader("Meeting transcript")

        transcript = chatgpt_transcript(transcript_file)
        for i in range(len(transcript)):
            # st.text(transcript[i])
            st.text_area("transcript", value=transcript[i], label_visibility="hidden")

        answers = chatgpt_default_ans(f'processed/{audio_file.split(".")[0]}'+'.txt'+'_default_ques')

        st.subheader("")

        st.subheader('Meeting details')

        # Display some example questions
        default_ques = ["1. What is this meeting about?", "2. How many speakers are there in the conversation?", "3. What are the minutes of this meeting?"]
        default_ans=[]

        default_ans.append(answers.split('\\nA2:')[0].replace("\\nA1:","").replace("\\n",""))
        answers=answers.split('\\nA2:')[1]
        default_ans.append(answers.split('\\nA3:')[0].replace("\\nA2:",""))
        default_ans.append(answers.split('\\nA3:')[1].replace("\\nA3:","").replace("\\n",'\n'))

        for i in range(0,3):
            st.write(default_ques[i])
            st.write(default_ans[i])