Title: Disconnected Environments: How To
Date: 2023-10-18 10:00
Category: howto
Tags: partners, topology, disconnected, restricted
Slug: disconnected-environments-quick-start
Author: Nacho Silla
Github: nsilla
Summary: A step by step guide on how to setup a DCI lab within a restricted network.

As we saw in our previous article ["Disconnected Environments: Overview"](disconnected-environments-overview.html), the Distributed CI (DCI) Agents may run in labs placed in restricted networks or, as we like to call them, disconnected environments.

This post will guide you through the setup of a disconnected environment ready to run the DCI Agents.

## A reminder

For the DCI automation to work, only the System Under Test is placed in a restricted network.

The SUT must have access to a set of downloadable resources, mostly container and OS images, which are replicated in mirroring systems placed in the same restricted network.

Then, there is the DCI Jumpbox, where all the automation, including that of mirroring the aforementioned resources, is run. This means te jumpbox must have access to the Internet in order to get the original resources.

Besides, the DCI Agents must be able to exchange data with the DCI Control Server.

So, wrapping up, **the SUT is placed in a restricted network and the jumpbox in a DMZ with access both to the Internet and the SUT.**

## Requirements

The registry host (usually the same as the jumpbox) must have access to the Internet and at least 100GB of disk space to host the disk and container images, as well as other resources we need to make available to the cluster nodes.

## Procedure

### Setting up an HTTP cache store

The first step is setting up an HTTP cache store in order to serve resources like the boot images.

Depending on your environment, you may decide to run the HTTP store from a dedicated host, the jumpbox or the provision host (the later may not even be an option if you're running a deployment different than IPI).

Regardless of your target host, to set up the HTTP store:

1. Create the local filesystem directory that will store the resources:

        $ mkdir /opt/cache

1. Create the HTTP cache store pod

        $ podman run -d --pod new:web_cache \
        --name container-web_cache \
        --expose 8080 \
        --publish 8080:8080 \
        -v /opt/cache:/var/www/html:Z \
        --user root registry.access.redhat.com/ubi8/httpd-24

1. Create, enable and start the service unit for the HTTP store

        $ podman generate systemd --name web_cache --files
        $ systemctl enable pod-web-cache
        $ systemctl start pod-web_cache

1. Open the required firewall ports

        $ firewall-cmd --zone=public --add-service=http --permanent
        $ firewall-cmd --zone=public --add-service=http
        $ firewall-cmd --zone=public --add-service=https --permanent
        $ firewall-cmd --zone=public --add-service=https

### Setting up a local registry

For the local registry we'll deploy a Quay instance.

Similar to the web cache store, the local registry may run from a dedicated host, the local host, or even the provision host.

In this case, to have the registry up and running:

#### Redis

1. Log into the public Quay.io registry:

        $ podman login \
        -u "{{ rhn_user }}" \
        -p "{{ rhn_password }}" \
        --authfile=/tmp/authfile.json registry.redhat.io

1. Pull the Redis container image:

        $ podman pull \
        --authfile=/tmp/authfile.json \
        registry.redhat.io/rhel8/redis-6:latest

1. Create the Redis service system unit:

        $ cat > /lib/systemd/system/quay-redis.service << EOF
        [Unit]
        Description=Redis for DCI Quay container
        [Service]
        User=root
        Group=root
        Restart=always
        ExecStart=/usr/bin/podman run \
                          --log-level=debug \
                          --name quay-redis \
                          --publish 6379:6379 \
                          --pull=never \
                          --rm \
                          --env REDIS_PASSWORD={{ my_password }} \
                          registry.redhat.io/rhel8/redis-6:latest
        ExecStop=/usr/bin/podman stop --name quay-redis
        [Install]
        WantedBy=local.target
        EOF

1. Enable and start the Redis service system unit.:

        $ chmod 644 /lib/systemd/system/quay-redis.service
        $ systemctl daemon-reload
        $ systemctl enable quay-redis
        $ systemctl start quay-redis

1. Verify the Redis container exists

        $ podman container exists quay-redis

#### PostgreSQL

1. Create the database volume path:

        $ sudo mkdir /var/lib/postgres-quay

1. Pull the PostgreSQL image:

        $ podman pull \
        --authfile=/tmp/authfile.json \
        registry.redhat.io/rhel8/postgresql-10:1

1. Create the PostgreSQL service system unit:


        $ cat > /lib/systemd/system/quay-postgresql.service << EOF
        [Unit]
        Description=DCI PostgreSQL container
        [Service]
        User=root
        Group=root
        Restart=always
        ExecStart=/usr/bin/podman run \
                          --name quay-postgresql \
                          --publish 5432:5432 \
                          --pull=never \
                          --rm \
                          --env POSTGRESQL_USER=quayuser \
                          --env POSTGRESQL_PASSWORD=quaypass \
                          --env POSTGRESQL_DATABASE=quay \
                          --env POSTGRESQL_ADMIN_PASSWORD=adminpass \
                          --volume /var/lib/postgres-quay:/var/lib/pgsql/data:Z \
                          registry.redhat.io/rhel8/postgresql-10:1
        ExecStop=/usr/bin/podman stop --name quay-postgresql
        [Install]
        WantedBy=local.target
        EOF

1. Enable and start the PostgreSQL service system unit:

        $ chmod 644 /lib/systemd/system/quay-postgresql.service
        $ systemctl daemon-reload
        $ systemctl enable quay-postgresql
        $ systemctl start quay-postgresql

1. Verify the PostgreSQL container exists:

        $ podman container exists quay-postgresql

1. Create the pg-trgm extension if it does not exists:

        $ podman exet -it quay-postgresql /bin/bash -c \
        'echo "CREATE EXTENSION IF NOT EXISTS pg_trgm" | psql -d quay -U postgres'

#### Quay

1. Create the container storage directory:

        $ mkdir /opt/quay-storage

1. Create the config directory:

        $ mkdir /etc/dci-quay

1. Create the settings file:

    In the following example, make sure to replace the place holders:

    * **{{ redis_host }}:** the IP address or hostname of the host running Redis.
    * **{{ postgresql_host }}:** the IP address or hostname of the host running PostgreSQL.
    * **{{ quay_host }}:** The FQDN of the host running quay.

    In most of the cases all the three fields may be set to the same value.

        $ cat > /etc/dci-quay/config.yaml << EOF
        AUTHENTICATION_TYPE: Database
        AVATAR_KIND: local
        BITTORRENT_FILENAME_PEPPER:
        BUILDLOGS_REDIS:
            host: {{ redis_host }}
            port: 6379
            password: dci-quay
        DATABASE_SECRET_KEY:  59585822944572860422300245797329252092216890232781433740972562886064953508823
        DB_CONNECTION_ARGS:
            autorollback: true
            threadlocals: true
        DB_URI: postgresql://quayuser:quaypass@{{ postgresql_host }}:5432/quay
        DEFAULT_TAG_EXPIRATION: 2w
        DISTRIBUTED_STORAGE_CONFIG:
            default:
                - LocalStorage
                - storage_path: /datastorage/registry
        DISTRIBUTED_STORAGE_DEFAULT_LOCATIONS: []
        DISTRIBUTED_STORAGE_PREFERENCE:
            - default
        FEATURE_ACI_CONVERSION: false
        FEATURE_ACTION_LOG_ROTATION: false
        FEATURE_ANONYMOUS_ACCESS: true
        FEATURE_APP_REGISTRY: false
        FEATURE_APP_SPECIFIC_TOKENS: true
        FEATURE_BITBUCKET_BUILD: false
        FEATURE_BLACKLISTED_EMAILS: false
        FEATURE_BUILD_SUPPORT: false
        FEATURE_CHANGE_TAG_EXPIRATION: true
        FEATURE_DIRECT_LOGIN: true
        FEATURE_GITHUB_BUILD: false
        FEATURE_GITHUB_LOGIN: false
        FEATURE_GITLAB_BUILD: false
        FEATURE_GOOGLE_LOGIN: false
        FEATURE_INVITE_ONLY_USER_CREATION: false
        FEATURE_MAILING: false
        FEATURE_NONSUPERUSER_TEAM_SYNCING_SETUP: false
        FEATURE_PARTIAL_USER_AUTOCOMPLETE: true
        FEATURE_PROXY_STORAGE: false
        FEATURE_REPO_MIRROR: false
        FEATURE_REQUIRE_TEAM_INVITE: true
        -FEATURE_RESTRICTED_V1_PUSH: true
        FEATURE_SECURITY_NOTIFICATIONS: false
        FEATURE_SECURITY_SCANNER: false
        FEATURE_SIGNING: false
        FEATURE_STORAGE_REPLICATION: false
        FEATURE_TEAM_SYNCING: false
        FEATURE_USER_CREATION: true
        FEATURE_USER_LAST_ACCESSED: true
        FEATURE_USER_LOG_ACCESS: false
        FEATURE_USER_METADATA: false
        FEATURE_USER_RENAME: false
        FEATURE_USERNAME_CONFIRMATION: true
        FEATURE_USER_INITIALIZE: true
        FRESH_LOGIN_TIMEOUT: 10m
        GITHUB_LOGIN_CONFIG: {}
        GITHUB_TRIGGER_CONFIG: {}
        GITLAB_TRIGGER_KIND: {}
        GPG2_PRIVATE_KEY_FILENAME: signing-private.gpg
        GPG2_PUBLIC_KEY_FILENAME: signing-public.gpg
        LDAP_ALLOW_INSECURE_FALLBACK: false
        LDAP_EMAIL_ATTR: mail
        LDAP_UID_ATTR: uid
        LDAP_URI: ldap://localhost
        LOG_ARCHIVE_LOCATION: default
        LOGS_MODEL: database
        LOGS_MODEL_CONFIG: {}
        MAIL_DEFAULT_SENDER: support@quay.io
        MAIL_PORT: 587
        MAIL_USE_AUTH: false
        MAIL_USE_TLS: false
        PREFERRED_URL_SCHEME: https
        REGISTRY_TITLE: DCI Quay
        REGISTRY_TITLE_SHORT: DCI Quay
        REPO_MIRROR_INTERVAL: 30
        REPO_MIRROR_TLS_VERIFY: true
        SECRET_KEY: '110410580524531142193228496022510225071279848016335637714684060801342057139962'
        SEARCH_MAX_RESULT_PAGE_COUNT: 10
        SEARCH_RESULTS_PER_PAGE: 10
        SECURITY_SCANNER_INDEXING_INTERVAL: 30
        SERVER_HOSTNAME: {{ quay_hostname }}
        SETUP_COMPLETE: true
        TAG_EXPIRATION_OPTIONS:
            - 0s
            - 1d
            - 1w
            - 2w
            - 4w
        TEAM_RESYNC_STALE_TIME: 30m
        TESTING: false
        USE_CDN: false
        USER_EVENTS_REDIS:
            host: {{ redis_host }}
            port: 6379
            password: dci-quay
        USER_RECOVERY_TOKEN_LIFETIME: 30m
        USERFILES_LOCATION: default
        FEATURE_EXTENDED_REPOSITORY_NAMES: true
        CREATE_NAMESPACE_ON_PUSH: true
        CREATE_PRIVATE_REPO_ON_PUSH: false
        EOF

1. Set the name resolution for the Quay FQDN:

        $ echo {{ quay_host_ip }} {{ quay_hostname }} >> /etc/hosts

1. Copy your Quay TLS certificate and private key into /etc/dci-quay

1. Copy your Quay TLS certificate into /etc/pki/ca-trust/source/anchors and update the list of trusted certificates:

        $ update-ca-trust

1. Pull the quay image:

        $ podman pull \
        --authfile=/tmp/authfile.json \
        quay.io/projectquay/quay:latest

1. Create the Quay service system unit

        $ cat > /lib/systemd/system/dci-quay.service << EOF
        [Unit]
        Description=DCI Quay container
        Requires=quay-redis.service
        Requires=quay-postgresql.service
        [Service]
        User=root
        Group=root
        Restart=always
        ExecStart=/usr/bin/podman --log-level=debug run \
                          --rm \
                          --name dci-quay \
                          --publish 80:8080 \
                          --publish 443:8443 \
                          --volume /etc/dci-quay:/quay-registry/conf/stack \
                          quay.io/projectquay/quay:latest
        ExecStop=/usr/bin/podman stop --name dci-quay
        [Install]
        WantedBy=local.target
        EOF

1. Enable and start the Quay service system unit

        chmod 644 /lib/systemd/system/dci-quay.service
        systemctl daemon-reload
        systemctl enable dci-quay
        systemctl start dci-quay

1. Verify the Quay container exists

        $ podman container exists dci-quay

1. Create the initial user:

        $ curl https://{{ quay_hostname }}/api/v1/user/initialize \
        --insecure \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"username": "quayadmin", "password": "quaypass123", "email": "quayadmin@example.com", "access_token": true}'


### Install the skopeo tool

The skopeo tool is used to mirror container images into the local Quay registry we just set up:

        $ dnf install -y skopeo

### Adapting the Ansible inventory

The last step when working with disconnected environment will be adapting your inventory, so it contains all the data needed to access the local resources instead of resorting to the public ones as it would usually do.

Below you have a complete list of the variables you have to add to your inventory with their description and examples of use.

* **dci_disconnected:** the main variable that triggers the DCI agent actions specific to disconnected environments. It may be set in the settings, pipeline or inventory files.

        dci_disconnected=true

* **webserver_url:** the URL to the HTTP cache store where the resources not served through a container registry are served.

        webserver_url=http://jumpbox.dci.lab:8080

* **local_registry_host:** FQDN or IP address of the server acting as mirror:

        local_registry_host=jumpbox.dci.lab

* **local_registry_port:** Listening port for the registry server.

        local_registry_port=443

* **provision_cache_store:** path to the directory where the HTTP cache store resources are kept.

        provision_cache_store=/opt/cache

* **disconnected_registry_auths_file:** path to the file containing the authentication tokens for the local registry.

        disconnected_registry_auths_file=/etc/dci-openshift-agent/quay.json

* **disconnected_registry_mirrors_file:** file that contains the addition trust bundle and image content sources for the local registry. The contents of this file will be appended to the install-config.yml file

        disconnected_registry_mirrors_file=/etc/dci-openshift-agent/trust-bundle.yml

* **local_repo:** name of the repository to create in your registry.

        local_repo=ocp4/openshift4

## Conclusion

With all these settings in place in your inventory you're all set up to start running the DCI agents in your disconnected environment.

If you have some experience running DCI in connected environments, you'll notice the jobs in your disconnected environments take longer and have some more tasks displayed in the DCI Control Server log.

These are the tasks run to mirror resources from the Internet into your local web server and registry, as well as some configuration tasks needed on the OCP cluster, like setting the Image Content Source Policies to redirect the cluster to pull resources from your local registry.

Besides this, the operation of the DCI tools remains exactly the same and you can start running your *dci-openshift-[app-]agent-ctl* or *dci-pipeline-schedule* as usual.