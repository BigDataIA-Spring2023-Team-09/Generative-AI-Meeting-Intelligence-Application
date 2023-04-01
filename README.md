# Generative AI Meeting Intelligence Application

# Introduction
This project is undertaken with the goal of building a Meeting Intelligence Application. The application allows users to upload audio recordings of the meeting. The Application then processes the audio file to generate the transcript of the meeting and store it in the s3 bucket. The user would be able to select and view the transcript file from a list of processed meetings. The user will also be able to ask questions and gain some insights about the selected meeting using GPT3.5 API.

# Architecture diagram
![deployment_architecture_diagram](https://user-images.githubusercontent.com/108916132/229265412-89f71db6-cfd3-4041-87f7-7e44f6504724.png)

### Files
```
📦 Generative-AI-Meeting-Intelligence-Application
├─ .gitignore
├─ Assignment 4 Damg.docx
├─ Presentation_demo.mp4
├─ README.md
├─ airflow
│  └─ app
│     └─ dags
│        ├─ adhoc.py
│        └─ batch.py
├─ deployment_architecture_diagram.png
├─ main.py
└─ streamlit
   ├─ Diarization.py
   ├─ Dockerfile
   ├─ Upload.py
   ├─ pages
   │  └─ Analyse.py
   └─ requirements.txt
```

* <code>Assignment 4 Damg.docx</code>: Documentation file
* <code>Presentation_demo.mp4</code>: Application demo video recording
* <code>adhoc.py</code>: This file contains the DAG implementation logic for user requested file upload. As the user uploads a file for transcription, AdHoc DAG gets fired up with the respective parameters.
* <code>batch.py</code>: This DAG is responsible to process all the audio files present in the 'Batch' folder of our S3 bucket on a daily basis. It is scheduled using Crontab and processes all the files altogether.
* <code>main.py</code>: This file contains the logic behind the application. This code was then modified to implement the DAGs. The code can be used to run the application locally, wihtout DAG implementation, and understand the actual flow of data between various API calls.
* <code>Diarization.py</code>: This script is designed to implement speaker diarization using the pyannote.audio package. 'pyannote.audio' is an open-source toolkit written in Python for speaker diarization. Based on PyTorch machine learning framework, it provides a set of trainable end-to-end neural building blocks that can be combined and jointly optimized to build speaker diarization pipelines. Make sure you run it using a GPU.
* <code>Dockfile</code>: This file is used to perform dockerization of the DAGs. Docker image is then deployed on GCP to make the DAGs publicly available.
* <code>Upload.py</code>: This is our streamlit application landing page where the user can upload their ausio files and trigger AdHoc DAG using a click of a button. User is provided with 2 language options to choose from.
* <code>Analyse.py</code>: The processed transcripts and generic question/answers are made available to the user to be viewed on this page. User can further ask custom follow-up questions using the GPT API.

**NOTE**: We have ommitted the diarization code from python scripts as of now for cloud deployment. In order to run the same locally, please clone the repository and un-comment the code.

### Application public link:
https://bigdataia-spring2023-team-09-generative--streamlitupload-gz42zd.streamlit.app/

### Airflow DAGs:
http://34.74.233.133:8080/

### Codelab document:
https://codelabs-preview.appspot.com/?file_id=1cpJE8thehalgEW_rJorXSqERJWhGMtsOiOgH1JZ6N1k#0

### Attestation:
WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK
Contribution:
* Ananthakrishnan Harikumar: 25%
* Harshit Mittal: 25%
* Lakshman Raaj Senthil Nathan: 25%
* Sruthi Bhaskar: 25%
