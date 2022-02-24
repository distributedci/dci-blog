FROM registry.access.redhat.com/ubi8/python-36

LABEL name="DCI Blog"
LABEL version="0.1.0"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

ENV LANG en_US.UTF-8

WORKDIR /opt/blog
COPY requirements.txt /opt/blog
RUN python -m pip install --no-cache-dir --upgrade pip
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . /opt/blog
RUN python --version

EXPOSE 8000

CMD ["make", "serve"]