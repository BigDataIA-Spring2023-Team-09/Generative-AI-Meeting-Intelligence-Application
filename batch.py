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
from urllib.request import urlopen
from pyannote.audio import Audio

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
    file=filename.replace('.mp3','').replace('.wav','')
    s3client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='processed/' + file + '.txt', Body=str(updated_transcript))

    directory_path = 'batch/recording_segments/'

    bucket = s3.Bucket(os.environ.get('USER_BUCKET_NAME'))
    for obj in bucket.objects.filter(Prefix=directory_path):
        obj.delete()

    # Delete the directory itself
    bucket.objects.filter(Prefix=directory_path).delete()

    # Copy the file to the new directory
    s3client.copy_object(Bucket=os.environ.get('USER_BUCKET_NAME'),
                     CopySource=os.environ.get('USER_BUCKET_NAME')+'/batch/'+file+'.wav',
                     Key='processed/'+file+'.wav')
    
    # Delete the original file
    s3client.delete_objects(Bucket=os.environ.get('USER_BUCKET_NAME'), Delete={'Objects': [{'Key': 'batch/'+file+'.wav'}]})
    s3client.delete_objects(Bucket=os.environ.get('USER_BUCKET_NAME'), Delete={'Objects': [{'Key': 'batch/'+file+'_updated.wav'}]})

    chatgpt_default_ques('processed/' + file + ".txt")

def segmented_audio_to_whisper_api(speaker_labels_string, filename):
    counter=0
    response = s3client.list_objects(Bucket=os.environ.get('USER_BUCKET_NAME'), Prefix='batch/recording_segments/')
    transcripts = []

    # Get all the wav files and sort them by name
    wav_files = sorted([obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.wav')])
    
    for i, wav_file in enumerate(wav_files):
        response_audio = s3client.get_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='batch/recording_segments/'+str(i)+'.wav')
        audio_file = io.BytesIO(response_audio['Body'].read())
        audio_file.name = str(i)+'.wav'

        # Transcribe the audio file using the OpenAI API
        try:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            transcripts.append(transcript["text"])
        except:
            print("Segmented audio file is too short. Minimum audio length is 0.1 seconds. Please upload another file!")
            counter=1

    if (counter==0):
        updated_transcript=[]
        for i in range(min(len(speaker_labels_string), len(transcripts))):
            updated_transcript.append(speaker_labels_string[i]+":"+transcripts[i] + '\n')
        
        write_transcript(filename, updated_transcript)

def millisec(timeStr):
    spl = timeStr.split(":")
    s = (int)((int(spl[0]) * 60 * 60 + int(spl[1]) * 60 + float(spl[2]) )* 1000)
    return s

def speaker_diarization():
    response = s3client.list_objects(Bucket=os.environ.get('USER_BUCKET_NAME'), Prefix='batch/')
    
    for obj in response['Contents']:
        filename=obj['Key']
        file=filename.replace('.mp3','').replace('.wav','')

        spacermilli = 2000
        spacer = AudioSegment.silent(duration=spacermilli)

        response_read = s3client.get_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='batch/'+filename)
        mp3_file = io.BytesIO(response_read['Body'].read())
        mp3_file.name = 'batch/'+filename

        audio = AudioSegment.from_file(mp3_file)
        
        audio = spacer.append(audio, crossfade=0)

        # Create a byte stream to hold the output WAV data
        output_file = io.BytesIO()

        # Export the audio to the byte stream in WAV format
        audio.export(output_file, format="wav")

        # Reset the position of the byte stream to the beginning
        output_file.seek(0)

        # Upload the output WAV file to S3 using put_object
        s3client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='batch/' + file + '_updated.wav', Body=output_file)

        pipeline = Pipeline.from_pretrained('pyannote/speaker-diarization', use_auth_token=hf_token)

        response_updated = s3client.get_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='batch/' + file + '_updated.wav')
        wav_string = response_updated['Body'].read()
        wav_file = io.BytesIO(wav_string)
        wav_file.name = 'batch/' + file + '_updated.wav'

        wav_url = s3client.generate_presigned_url(ClientMethod='get_object',
            Params={
                'Bucket': os.environ.get('USER_BUCKET_NAME'),
                'Key': 'batch/' + file + '_updated.wav'
            },
            ExpiresIn=3600)
        aud=Audio()
        with urlopen(wav_url) as r:
            contents = r.read()
            contents_bytesio = io.BytesIO(contents)
            contents_bytesio.seek(0)
            waveform, sample_rate = aud(contents_bytesio)
            dz = pipeline({"waveform": waveform, "sample_rate": sample_rate})

        s3client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='batch/recording_segments/' + "diarization_" + file + ".txt", Body=str(dz))

        with smart_open.open('s3://'+os.environ.get('USER_BUCKET_NAME')+'/batch/recording_segments/'+"diarization_" + file + ".txt", 'rb') as f:
            speaker_labels = [line.split()[-1] for line in f]
        # s3client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='processed/' + file, Body=json_data)
        
        speaker_labels_string = [x.decode() for x in speaker_labels]

        with smart_open.open('s3://'+os.environ.get('USER_BUCKET_NAME')+'/batch/recording_segments/'+"diarization_" + file + ".txt", 'rb') as f:
            dzs = f.read().decode().splitlines()

        groups = []
        g = []
        lastend = 0

        for d in dzs:   
            if g and (g[0].split()[-1] != d.split()[-1]):      #same speaker
                groups.append(g)
                g = []
            
            g.append(d)
            
            end = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=d)[1]
            end = millisec(end)
            if (lastend > end):       #segment engulfed by a previous segment
                groups.append(g)
                g = [] 
            else:
                lastend = end
        if g:
            groups.append(g)

        audio = AudioSegment.from_wav(wav_file)
        gidx = -1
        for g in groups:
            start = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=g[0])[0]
            end = re.findall('[0-9]+:[0-9]+:[0-9]+\.[0-9]+', string=g[-1])[1]
            start = millisec(start) #- spacermilli
            end = millisec(end)  #- spacermilli
            gidx += 1

            segmented_file = io.BytesIO()

            # Export the audio to the byte stream in WAV format
            audio[start:end].export(segmented_file, format="wav")

            # Reset the position of the byte stream to the beginning
            segmented_file.seek(0)

            # Upload the output WAV file to S3 using put_object
            s3client.put_object(Bucket=os.environ.get('USER_BUCKET_NAME'), Key='batch/recording_segments/' + str(gidx) + '.wav', Body=segmented_file)

        del pipeline, spacer, audio, dz
        segmented_audio_to_whisper_api(speaker_labels_string, filename)

def read_audio_file_from_s3():
    try:
        response = s3client.list_objects(Bucket=os.environ.get('USER_BUCKET_NAME'), Prefix='batch/')
        if 'Contents' in response:
            speaker_diarization()
        return True
    except:
        return

def main():
    read_audio_file_from_s3()

if __name__=="__main__":
    main()