FROM registry.access.redhat.com/ubi9/ubi-minimal:latest AS build-stage

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /opt/dci-blog
WORKDIR /opt/dci-blog
RUN /bin/uvx \
  --from pelican[markdown] \
  --with pelican-readtime \
  --with tzdata pelican \
  ./content -o ./output -s ./publishconf.py

FROM registry.access.redhat.com/ubi9/ubi-minimal:latest AS webserver

LABEL name="DCI BLOG"
LABEL version="0.1.0"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

RUN microdnf -y upgrade && \
  microdnf -y install nginx && \
  microdnf clean all

COPY --from=build-stage /opt/dci-blog/output /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN ln -sf /dev/stdout /var/log/nginx/access.log \
  && ln -sf /dev/stderr /var/log/nginx/error.log

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
