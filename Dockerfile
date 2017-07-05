FROM python:3.5
WORKDIR /usr/src/emailr

ADD . /emailr

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

# Exports the current directory to the Python path.
ENV PYTHONPATH .

# Tells Flask that it will be serving the app named emailr (as an
# environment variable).
ENV FLASK_APP emailr

# Turns on debugging mode (as an environment variable).
ENV FLASK_DEBUG false

COPY . .

# Runs the app by running flask (given that FLASK_APP is already set).
# Host needs to be set to 0.0.0.0 for Docker. That allows Docker to accept
# traffic from any port. Otherwise, it won't accept any traffic except from
# itself (the same container).
# Port is set to default TCP/IP port 80.
CMD [ "flask", "run", "--host=0.0.0.0", "--port=80" ]

# This is the build command. It builds the image using the docker file saved
# in the same directory ('.').
# docker build -t joggy-image .

# This is the run command. It exposes port 80. It uses the image from joggy-
# image, removes unnecessary containers ('--rm'), and names the running
# process as joggy-running.
# docker run -p 80:80 -it --rm --name joggy-running joggy-image
