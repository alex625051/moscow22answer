# start by pulling the python image
FROM python:latest
# copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt
# switch working directory
WORKDIR /app
# install the dependencies and packages in the requirements file
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
RUN pip install psycopg2-binary
RUN pip install psycopg2
RUN pip install -r requirements.txt
# copy every content from the local file to the image
COPY . /app
# configure the container to run in an executed manner
ENTRYPOINT ["python"]
CMD ["app.py"]