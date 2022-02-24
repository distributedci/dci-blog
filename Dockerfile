FROM registry.access.redhat.com/ubi8/python-36 as builder

LABEL name="DCI Blog"
LABEL version="0.1.0"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

ENV LANG en_US.UTF-8

COPY requirements.txt /opt/app-root/src
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt
COPY . /opt/app-root/src/
RUN make clean
RUN make html

FROM registry.access.redhat.com/ubi8/httpd-24
COPY --from=builder /opt/app-root/src/output /var/www/html

EXPOSE 8080