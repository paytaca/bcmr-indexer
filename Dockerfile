FROM nikolaik/python-nodejs:python3.7-nodejs15-slim

COPY ./requirements.txt requirements.txt
RUN apt-key adv --refresh-keys --keyserver keyserver.ubuntu.com \
    && apt-get update \
    && apt-get install -y --no-install-recommends g++ \
    gettext \
    && pip install --upgrade pip \
    && pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt \
    && apt-get purge -y --auto-remove gcc

WORKDIR /app
COPY . /app

RUN npm install

RUN wget -O /usr/local/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/8ed92e8cab83cfed76ff012ed4a36cef74b28096/wait-for-it.sh && \
    chmod +x /usr/local/bin/wait-for-it.sh

EXPOSE 8000
ENTRYPOINT [ "/bin/sh", "entrypoint.sh" ]
CMD [ "supervisord", "-c", "/app/supervisord.conf", "--nodaemon" ]
