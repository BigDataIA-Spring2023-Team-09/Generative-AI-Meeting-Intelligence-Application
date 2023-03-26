from dotenv import load_dotenv
import os
from pydub import AudioSegment
# Note: you need to be using OpenAI Python v0.27.0 for the code below to work
import openai
import boto3
import botocore
import io
import json
from pydub import AudioSegment
from pyannote.audio import Pipeline
import re
import smart_open

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

s3client = boto3.client('s3', 
                        region_name = 'us-east-1',
                        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                        )

os.environ['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY')
os.environ['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_KEY')

hf_token = os.environ.get('HF_TOKEN')

# def millisec(timeStr):
#     spl = timeStr.split(":")
#     s = (int)((int(spl[0]) * 60 * 60 + int(spl[1]) * 60 + float(spl[2]) )* 1000)
#     return s

# def speaker_diarization(aws_mp3_file):

#     filename=aws_mp3_file.split('/')[1].replace('.mp3','')

#     spacermilli = 2000
#     spacer = AudioSegment.silent(duration=spacermilli)

#     response = s3client.get_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key=aws_mp3_file)
#     mp3_file = io.BytesIO(response['Body'].read())
#     mp3_file.name = aws_mp3_file

#     audio = AudioSegment.from_file(mp3_file)
    
#     audio = spacer.append(audio, crossfade=0)
#     audio.export(filename+'_updated.wav', format="wav")

#     pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization', use_auth_token=hf_token)

#     response_updated = s3client.get_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='processed/' + filename + '_updated.wav')
#     wav_file = io.BytesIO(response_updated['Body'].read())
#     wav_file.name = 'processed/' + filename + '_updated.wav'

#     # Read WAV file from S3
#     with smart_open.open('s3://'+os.environ.get('USER_BUCKET_NAME')+'/processed/'+ plans_updated.wav', 'rb') as f:
#         wav_bytes = f.read()

#     # Convert bytes to file-like object
#     wav_file = io.BytesIO(wav_bytes)

#     # Set the file name (if needed)
#     wav_file.name = 'plans_updated.wav'

#     DEMO_FILE = {'uri': 'blabla', 'audio': "plans_updated.wav"} #######################################
#     dz = pipeline(DEMO_FILE)

#     s3client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='processed/' + "diarization_" + filename + ".txt", Body=str(dz))
    
#     with smart_open.open('s3://'+os.environ.get('USER_BUCKET_NAME')+'/processed/'+"diarization_" + filename + ".txt", 'rb') as f:
#         dzs = f.read().decode().splitlines()

#     groups = []
#     g = []
#     lastend = 0

#     for d in dzs:   
#         if g and (g[0].split()[-1] != d.split()[-1]):      #same speaker
#             groups.append(g)
#             g = []
        
#         g.append(d)
        
#         end = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=d)[1]
#         end = millisec(end)
#         if (lastend > end):       #segment engulfed by a previous segment
#             groups.append(g)
#             g = [] 
#         else:
#             lastend = end
#     if g:
#         groups.append(g)
#     print(*groups, sep='\n')

#     audio = AudioSegment.from_wav(wav_file)
#     gidx = -1
#     for g in groups:
#         start = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=g[0])[0]
#         end = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=g[-1])[1]
#         start = millisec(start) #- spacermilli
#         end = millisec(end)  #- spacermilli
#         print(start, end)
#         gidx += 1
#         audio[start:end].export(str(gidx) + '.wav', format='wav') ##############################

def chatgpt_default_ques(transcript_file):

    trans_response = s3client.get_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key=transcript_file)
    json_content = trans_response['Body'].read().decode('utf-8')
    data = json.loads(json_content)

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=str(data) + '\n' + "Given this meeting transcript, i have 3 questions. Answer them in a Question/Answer format." + '\n' + "Q1: What is this meeting about?" + '\n' + "Q2: How many speakers are present?" + '\n' + "Q3: Give the minutes of meeting in 3 short points.",
        max_tokens=1000,
        temperature=0
    )
    ques_file=transcript_file.split('/')[1] + "_deafult_ques"

    my_ques = "Q1: What is this meeting about?" + '\n' + "Q2: How many speakers are present?" + '\n' + "Q3: Give the minutes of meeting in 3 short points."

    data={
        'questions': my_ques,
        'answers': response["choices"][0]["text"]
    }
    json_data = json.dumps(data)
    s3client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='processed/' + ques_file, Body=json_data)

def write_transcript(filepath, my_transcript):
    filename = filepath.split('/')[1].replace('.mp3','')
    data={
        'meeting': my_transcript
    }
    json_data = json.dumps(data)

    s3client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='processed/' + filename, Body=json_data)

    chatgpt_default_ques('processed/' + filename)

def audio_to_whisper_api(filepath):
    response = s3client.get_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key=filepath)
    audio_file = io.BytesIO(response['Body'].read())
    audio_file.name = filepath

    # Transcribe the audio file using the OpenAI API
    transcript = openai.Audio.transcribe("whisper-1", audio_file)

    write_transcript(filepath, transcript["text"])

def read_audio_file_from_s3(file_name):
    try:
        s3client.head_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='current/' + file_name)
        aws_filepath = 'current/' + file_name
        # speaker_diarization(aws_filepath)
        audio_to_whisper_api(aws_filepath)
        return True

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise

def main():
    read_audio_file_from_s3("plans.mp3")
    # speaker_diarization("likeit.mp3")

if __name__=="__main__":
    main()