FROM python:3.10.6

# Pull the base docker image of python with tag 3.9.13

RUN pip install --upgrade pip


WORKDIR /app
# Change the working dir inside the container - cd /app

COPY Upload.py requirements.txt ./
# Copy main.py as source cod and req.txt as dependency

RUN pip install -r requirements.txt
# Install the dependency

RUN pip install streamlit --upgrade

ADD pages /app/pages/

ADD pages/Analyse.py /app/pages/

### Container Env same as local at this point

EXPOSE 8002

CMD ["streamlit", "run", "Upload.py", "--server.port", "8002"]