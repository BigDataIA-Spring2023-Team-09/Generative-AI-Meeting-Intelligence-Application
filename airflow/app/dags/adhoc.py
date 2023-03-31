import boto3
from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from dotenv import load_dotenv
import os
from airflow.models import Variable
import io



import openai
import botocore
import json

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_KEY')
USER_BUCKET_NAME = Variable.get('USER_BUCKET_NAME')


s3client = boto3.client(
    's3',
    aws_access_key_id=Variable.get('AWS_ACCESS_KEY'),
    aws_secret_access_key=Variable.get('AWS_SECRET_KEY')

)


s3 = boto3.resource('s3', 
                    region_name = 'us-east-1',
                    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                    aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                    )

hf_token = os.environ.get('HF_TOKEN')

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 2, 22),
    'retries': 0
}


dag = DAG('adhoc',
          default_args=default_args,
          catchup=False
          )




def chatgpt_default_ques(**context):

    transcript_file = context['ti'].xcom_pull(key='transcript_file')
    

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


def write_transcript(**context):

    filename = context['ti'].xcom_pull(key='filename')
    updated_transcript = context['ti'].xcom_pull(key='transcript_list')
  
    file=filename.replace('.wav','').replace('.mp3','')
    s3client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='processed/' + file + '.txt', Body=str(updated_transcript))

    # Copy the file to the new directory
    s3client.copy_object(Bucket=os.environ.get('USER_BUCKET_NAME'),
                     CopySource=os.environ.get('USER_BUCKET_NAME')+'/current/'+filename,
                     Key='processed/'+filename)
    
    # Delete the original file
    s3client.delete_objects(Bucket=os.environ.get('USER_BUCKET_NAME'), Delete={'Objects': [{'Key': 'current/'+filename}]})

    context['ti'].xcom_push(key='transcript_file', value='processed/' + filename + ".txt")
    
    
    # chatgpt_default_ques('processed/' + file + ".txt")

def audio_to_whisper_api(**context):

    
    filename = context['ti'].xcom_pull(key='file_name')
    language = context['ti'].xcom_pull(key='language')

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


    context['ti'].xcom_push(key='filename', value=filename)
    context['ti'].xcom_push(key='transcript_list', value=transcript_list)
    

    # write_transcript(filename, transcript_list)

def read_audio_file_from_s3(**context):

    file_name = context['ti'].conf['file_name']
    language = context['ti'].conf['language']

    try:
        s3client.head_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='current/' + file_name)

        context['ti'].xcom_push(key='file_name', value=file_name)
        context['ti'].xcom_push(key='language', value=language)

        # audio_to_whisper_api(file_name, language)
        return True

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise

# def main():
#     read_audio_file_from_s3("plans.mp3", "English")

# if _name=="main_":
#     main()





with dag:
    read_audio = PythonOperator(
        task_id='read_audio_file_from_s3',
        python_callable=read_audio_file_from_s3,
        dag=dag
    )

    audio_to_whisper = PythonOperator(
        task_id='audio_to_whisper_api',
        python_callable=audio_to_whisper_api,
        dag=dag
    )

    transcript = PythonOperator(
        task_id='write_transcript',
        python_callable=write_transcript,
        dag=dag
    )

    chatgpt_ques = PythonOperator(
        task_id='chatgpt_default_ques',
        python_callable=chatgpt_default_ques,
        dag=dag
    )

read_audio >> audio_to_whisper
audio_to_whisper >> transcript
transcript >> chatgpt_ques