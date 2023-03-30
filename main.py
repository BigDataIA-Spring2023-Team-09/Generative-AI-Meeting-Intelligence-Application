from dotenv import load_dotenv
import os
import openai
import boto3
import botocore
import io
import json
import re
import smart_open

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

s3client = boto3.client('s3', 
                        region_name = 'us-east-1',
                        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                        )

s3 = boto3.resource('s3', 
                    region_name = 'us-east-1',
                    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                    aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                    )

os.environ['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY')
os.environ['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_KEY')

hf_token = os.environ.get('HF_TOKEN')

def chatgpt_default_ques(transcript_file):
    trans_response = s3client.get_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key=transcript_file)
    data = trans_response['Body'].read().decode('utf-8')

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=str(data) + '\n' + "Given this meeting transcript, i have 3 questions. Answer them in a Question/Answer format." + '\n' + "Q1: What is this meeting about?" + '\n' + "Q2: How many speakers are present?" + '\n' + "Q3: Give the minutes of meeting in 3 short points.",
        max_tokens=1000,
        temperature=0
    )
    
    ques_file=transcript_file.split('/')[1] + "_default_ques"

    my_ques = "Q1: What is this meeting about?" + '\n' + "Q2: How many speakers are present?" + '\n' + "Q3: Give the minutes of meeting in 3 short points."

    ques_data={
        'questions': my_ques,
        'answers': response["choices"][0]["text"]
    }
    json_data = json.dumps(ques_data)
    s3client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='processed/' + ques_file, Body=json_data)


def write_transcript(filename, updated_transcript):
    file=filename.replace('.wav','').replace('.mp3','')
    s3client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='processed/' + file + '.txt', Body=str(updated_transcript))

    # Copy the file to the new directory
    s3client.copy_object(Bucket=os.environ.get('USER_BUCKET_NAME'),
                     CopySource=os.environ.get('USER_BUCKET_NAME')+'/current/'+filename,
                     Key='processed/'+filename)
    
    # Delete the original file
    s3client.delete_objects(Bucket=os.environ.get('USER_BUCKET_NAME'), Delete={'Objects': [{'Key': 'current/'+filename}]})

    chatgpt_default_ques('processed/' + file + ".txt")

def audio_to_whisper_api(filename, language):
    response = s3client.get_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='current/'+filename)
    audio_file = io.BytesIO(response['Body'].read())
    audio_file.name = filename
    transcript_list=[]

    # Transcribe the audio file using the OpenAI API
    if (language=="English"):
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    else:
        transcript = openai.Audio.translate("whisper-1", audio_file)
    transcript_list.append(transcript["text"])
    write_transcript(filename, transcript_list)

def read_audio_file_from_s3(file_name, language):
    try:
        s3client.head_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='current/' + file_name)
        audio_to_whisper_api(file_name, language)
        return True

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise

def main():
    read_audio_file_from_s3("plans.mp3", "English")

if __name__=="__main__":
    main()