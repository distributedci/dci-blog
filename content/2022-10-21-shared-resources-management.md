Title: How to manage shared deployments in DCI
Date: 2022-10-21 09:30
Category: how-to
Tags: introduction, dci, ci, OpenShift, OCP, dci-queue
Slug: dci-queue
Author: Frédéric Lepied
Github: fredericlepied
Summary: dci-queue: a simple resource management system in DCI

[TOC]

## Introduction

When you work as a team (more than one person) on a DCI deployment or
when you have multiple setups, you need a resource management system
to automate resource allocation, to avoid conflicts or to avoid to
step on each other toes.

A resource management system allows to reserve a resource or to
consume resources in an automated way.

In DCI, there is such tool called `dci-queue`. It is a basic queue
management system. In this article, we are going to describe how to
use it.

## dci-queue

### Installation

`dci-queue` is part of the `dci-pipeline` rpm. Install it like this:

    :::shell-session
    $ sudo dnf install -y https://packages.distributed-ci.io/dci-release.el8.noarch.rpm
    $ sudo cat > /etc/yum.repos.d/ansible-runner.repo <<EOF
    [ansible-runner]
    name=Ansible Runner for EL 8 - $basearch
    baseurl=https://releases.ansible.com/ansible-runner/rpm/epel-8-x86_64/
    enabled=1
    gpgcheck=1
    gpgkey=https://releases.ansible.com/keys/RPM-GPG-KEY-ansible-release.pub
    EOF
    $ sudo dnf install -y dci-pipeline

### Initialization

`dci-queue` organizes resources in pools. Resources are symbolic names
that are transmitted to other tools like `dci-pipeline`,
`dci-openshift-agent-ctl` or any other command line tools.

To create a pool of resources named  `mypool`:

    :::shell-session
    $ dci-queue add-pool mypool

To add resources to the `mypool` pool:

    :::shell-session
    $ dci-queue add-resource mypool cluster1
    $ dci-queue add-resource mypool cluster2

To see the resources on the `mypool` pool, do:

    :::shell-session
    $ dci-queue list mypool
    Resources on the mypool pool: cluster1 cluster2
    Available resources on the mypool pool: cluster1 cluster2
    Executing commands on the mypool pool:
    Queued commands on the mypool pool:

### Usage

Then, to make use of one of the resources from the pool, `dci-queue`
is using the `schedule` sub-command to queue a command and then
`dci-queue` will pick one of the resources from the pool substituting
the `@RESOURCE` string on the command line. If there is no available
resource, `dci-queue` will wait for one to become available again.

For example, to use `dci-queue` with `dci-pipeline` we usually use
`@RESOURCE` to be passed as the inventory name:

    :::shell-session
    $ dci-queue schedule mypool dci-pipeline ocp-install:ansible_inventory=/path1/inventories/@RESOURCE \
       /path2/pipelines/ocp-install-pipeline.yml
    $ dci-queue list mypool
    Resources on the mypool pool: cluster1 cluster2
    Available resources on the mypool pool: cluster1 cluster2
    Executing commands on the mypool pool:
    Queued commands on the mypool pool:
     1: dci-pipeline ocp-install:ansible_inventory=/path1/inventories/@RESOURCE /path2/pipelines/ocp-install-pipeline.yml (wd: /tmp)

To use it with `dci-openshift-agent-ctl`, we usually use `@RESOURCE`
as the prefix. See [the article about prefixes](using-prefixes.html)
for more details about the usage of prefixes. Example:

    :::shell-session
    $ dci-queue schedule mypool --  dci-openshift-agent-ctl -p @RESOURCE -s
    $ dci-queue list mypool
    Resources on the mypool pool: cluster1 cluster2
    Available resources on the mypool pool: cluster1 cluster2
    Executing commands on the mypool pool:
    Queued commands on the mypool pool:
     2: dci-openshift-agent-ctl -p @RESOURCE -s (wd: /tmp)

When the command is executed by `dci-queue`, you see the `@RESOURCE`
string expanded with the right resource and the used resource is no
longer in the available resources:

    :::shell-session
    $ dci-queue list mypool
    Resources on the mypool pool: cluster1 cluster2
    Available resources on the mypool pool: cluster1
    Executing commands on the mypool pool:
     2 [cluster2]: dci-openshift-agent-ctl -p cluster2 -s (wd: /tmp)
    Queued commands on the mypool pool:

If you want to see the output from a running command, use the `log`
sub-command using the queue number:

    :::shell-session
    $ dci-queue log mypool 2 -f
    + cd /tmp
    + dci-openshift-agent-ctl -p cluster2 -s
    ...

To unschedule a job, you can do it like that:

    :::shell-session
    $ dci-queue unschedule mypool 2

### Booking and releasing a resource

When you want to book a resource to do manual work on a deployment,
you can use the `schedule` sub-command with the `-r`
option. `dci-queue` will then not put the resource in the pool after
the end of the command.

An alternative is to remove the resource from the pool passing the
reason to let others in team know why it was removed and at what
time. Example:

    :::shell-session
    $ dci-queue remove-resource mypool cluster1 "fred: need to do manual debug"
    $ dci-queue list mypool
    Resources on the mypool pool: cluster2
    Available resources on the mypool pool: cluster2
    Removed resources on the mypool pool:
     cluster1: fred: need to do manual debug [2022-10-16 23:02:47.945531]
    Executing commands on the mypool pool:
    Queued commands on the mypool pool:

Then, when the manual work is finished, you can put back the resource
in the pool:

    :::shell-session
    $ dci-queue add-resource mypool cluster1
    $ dci-queue list mypool
    Resources on the mypool pool: cluster1 cluster2
    Available resources on the mypool pool: cluster1 cluster2
    Executing commands on the mypool pool:
    Queued commands on the mypool pool:
