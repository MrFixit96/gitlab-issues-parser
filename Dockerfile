FROM python:3-slim

LABEL maintainer="James Anderton <janderton@hashicorp.com>"
LABEL description="This is a mediator script that will receive a webhook sent from a GitLab Issue being created. It will parse the json payload, looking for the object_attributes[description] field. In this field it will trigger on KEYWORD:Value pairs and separate them for use in a POST request. Finally It will print out the equivalent Curl request for debugging use."


COPY src/requirements.txt .
RUN apt update && apt install -y build-essential && \
    pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false $BUILD_DEPS \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY src/* /app/
#RUN python setup.py egg_info && \
#    pip install gitlab-issues-parser

ENV APP_PORT=8080
EXPOSE 8080

RUN useradd -r -d /app flask
RUN echo "uwsgi --http :"${APP_PORT}" --wsgi-file app.py --callable app --processes 4 --threads 2 --stats 127.0.0.1:9191" > /app/run.sh && \
    chmod +x /app/run.sh && \
    chown flask:flask /app/run.sh

USER flask
ENTRYPOINT ["/bin/sh", "-c" ]
CMD ["/app/run.sh"]
#ENTRYPOINT ["flask", "run"]
#CMD ["gitlab-issues-parser:app"]
