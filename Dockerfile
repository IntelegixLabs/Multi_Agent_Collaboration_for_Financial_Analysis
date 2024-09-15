# init a base image (Alpine is small Linux distro)
FROM python:3.10.4
# update pip to minimize dependency errors 
RUN pip install --upgrade pip
# define the present working directory
WORKDIR /my-app
# copy the contents into the working dir
# run pip to install the dependencies of the flask app
COPY ./requirements.txt /my-app/requirements.txt

RUN pip install -r requirements.txt

COPY .env /my-app/.env
ADD . /my-app
# define the command to start the container
CMD ["python","template_for_api_marketplace.py"]