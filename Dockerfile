# syntax=docker/dockerfile:1

# base python image for custom image
FROM python:3.12.14-slim

# Upgrade pip
RUN pip install --upgrade pip
# create working directory and install pip dependencies
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# copy python project files from local to /hello-py image working directory
COPY . .


# run the flask server  
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
