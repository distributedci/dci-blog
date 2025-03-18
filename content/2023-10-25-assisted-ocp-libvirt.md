Title: OCP Assisted Install on Libvirt
Date: 2023-10-25 10:00
Category: howto
Tags: partners, libvirt, openshift, assisted
Slug: ocp-assisted-libirt-quick-start
Author: Bill Peck
Github: p3ck
Summary: A step by step guide on how to setup DCI Openshift agent on libvirt with Assisted Installs.

[TOC]

## Introduction

In previous blog posts, we have learned about the OCP on Libvirt project and the benefits it brings to us, with regards to the flexible deployment of OCP clusters where the nodes are virtual machines deployed on KVM.

If you remember, we started by commenting how to [set up a virtual development environment for OCP agent](libvirt-dev-env-for-ocp-agent.html), and then we continued by describing how to [use DCI to easily install an OCP cluster based on Libvirt in a single baremetal server](install-openshift-on-baremetal-using-dci.html).

Both of those blog entries explained how to do IPI installs in a virtual environment. This blog will cover using
the Assisted Installer in a virtual environment.

One of the biggest benefits to using the Assisted Installer mode of the DCI OCP agent is that it makes mixing virtual
and baremetal so easy. You can define a virtual control plane (3 masters) and bridge that to your cluster network
where you have 2 baremetal workers.

The entire process that I am going to go over in the blog is also recorded here:

<script async id="asciicast-612532" src="https://asciinema.org/a/612532.js"></script>

## System Prep

First step is installing RHEL-8 and subscribing it to RHN or Sattelite

    $ sudo subscription-manager register --auto-attach
    $ sudo subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
    $ sudo subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms
    $ sudo subscription-manager repos --enable ansible-2.9-for-rhel-8-x86_64-rpms
    $ sudo dnf -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
    $ sudo dnf -y install https://packages.distributed-ci.io/dci-release.el8.noarch.rpm
    $ sudo dnf -y install dci-openshift-agent

For the rest of the Instructions we will execute commands as the `dci-openshift-agent` user. This user was created
when you installed the `dci-openshift-agent` RPM. Set a password for the user to make it easier to setup SSH keys
and also allow you to SSH in as that user instead of root.

    $ sudo passwd dci-openshift-agent
    $ sudo su - dci-openshift-agent

## Disable SELinux

You will need to disable SELinux for now since it conflicts with the tool (sushy-tools) which is used to manage
the virtual machines.

    $ sudo setenforce 0
    $ sudo sed -i 's/^SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config

## Generate SSH keys

In order for the Ansible playbooks to execute properly we need to generate an SSH key and then install
the public keys in `authorized_keys` for both `dci-openshift-agent` and `root`.

    $ ssh-keygen
    $ ssh-copy-id localhost
    $ ssh-copy-id root@localhost

## Generate Inventory

The [Assisted Install inventory is fully documented](https://github.com/redhat-partner-solutions/crucible/blob/main/docs/inventory.md) but we provide common templates and a playbook to generate one. We are going to deploy just the
control_plane in this example, so just 3 masters with no workers. We will review it in the next section.

    $ pwd
    /var/lib/dci-openshift-agent
    $ cd samples/assisted_on_libvirt
    $ ansible-playbook -i dev/controlplane parse-template.yml
    $ sudo cp hosts /etc/dci-openshift-agent/hosts

## Review /etc/dci-openshift-agent/hosts

You will want to review the inventory file `/etc/dci-openshift-agent/hosts` and make sure it makes sense for your
environment. You will notice that the inventory gives you a great deal of flexibility on where different services
like NTP, web server cache, virtual host server, etc.. can be hosted and/or managed too.
In our example here everything is done on the Jumpbox. But you could separate these especially if you plan to
install more than one cluster and want to share resources.

One area that we needed to change was where the virtual hosts disks were stored, `images_dir`.
We have our extra disk space mounted on `/opt` and by default the config will use `/var/lib/libvirt/images`.

Here is the section that actually defines the virtual masters that will be deployed:

    # Describe the desired cluster members
    nodes:
      vars:
        bmc_user: "{{ VAULT_NODES_BMC_USER | mandatory }}"
        bmc_password: "{{ VAULT_NODES_BMC_PASSWORD | mandatory }}"
        bmc_address: "okd-master-1.home.pecknet.com:8082"
        vm_host: vm_host1
        vendor: KVM
        vm_spec:
          cpu_cores: 8
          ram_mib: 16384
          disk_size_gb: 150
        network_config:
          interfaces:
            - name: enp1s0
              mac: "{{ mac }}"
              addresses:
                ipv4:
                  - ip: "{{ ansible_host}}"
                    prefix: "25"
          dns_server_ips:
           - "10.60.0.1"
          routes: # optional
            - destination: 0.0.0.0/0
              address: "10.60.0.1"
              interface: enp1s0
      children:
        masters:
          vars:
            role: master
          hosts:
            dciokd-master-0:
              ansible_host: "10.60.0.100"
              mac: "DE:AD:BE:EF:C0:00"
            dciokd-master-1:
              ansible_host: "10.60.0.101"
              mac: "DE:AD:BE:EF:C0:01"
            dciokd-master-2:
              ansible_host: "10.60.0.102"
              mac: "DE:AD:BE:EF:C0:02"

## Review /etc/dci-openshift-agent/settings.yml

While the Inventory file describes what local resources to use the settings file describes what resources to consume
from DCI. This is where you will state which topic you are interested in. Topics correlate to which major release
of OCP, (4.11, 4.14, etc..). You can then further narrow down which component you will get, nightly, rc, or even a
specific version.

    dci_topic: OCP-4.12
    dci_components_by_query: ['name:4.12.15']

The DCI OCP Agent now supports many install methods and we need to make sure we specify that we are doing Assisted
Installs by having the following in settings as well.

    install_type: assisted

## Install RemoteCI

A RemoteCI is what allows the agent to authenticate with the DCI control server. You can create and get your
RemoteCI from the following url: [https://www.distributed-ci.io/remotecis](https://www.distributed-ci.io/remotecis)

The contents of that should be placed in `/etc/dci-openshift-agent/dcirc.sh` and look similar to this

    DCI_CLIENT_ID='remoteci/2049c5b4-4a57-4aad-8e1a-392101dd9cd6'
    DCI_API_SECRET='VERYLONGSECRETHERE.............................'
    DCI_CS_URL='https://api.distributed-ci.io/'
    export DCI_CLIENT_ID
    export DCI_API_SECRET
    export DCI_CS_URL

## Run the DCI Agent

Finally we are ready to run the agent. If everything is configured properly the following command will result in
a working OCP cluster running 4.12.15.

    $ dci-openshift-agent-ctl -s -- -v

You can review your jobs on the DCI control server as well at the following link: [https://www.distributed-ci.io/jobs](https://www.distributed-ci.io/jobs)

## Adding Workers

The next step would be to expand your Inventory and add baremetal workers. Stay tuned for another blog entry covering that.
