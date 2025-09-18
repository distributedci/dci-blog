Title: Running your pipelines with podman with dci-pipeline-podman
Date: 2025-09-18 10:00
Category: overview
Tags: deployment
Author: Pierre Blanc
Summary: This short post will describe a new feature in DCI, the way to run dci-pipeline with a Podman container. We will see how it is easy to install, configure and use it.

[TOC]

# Introduction

Dci-pipeline is a recommended way to deploy and test OpenShift with DCI.

This article is about using DCI via Podman. If you're not familiar with dci-pipeline, start by reading [the introduction](dci-pipeline.html), the [advanced post about dci-pipeline](expand-dci-pipeline-knowledge.html) provides also a wealth of interesting information.

Containers are gaining popularity because they make things easy to use and install.
Many people are asking for this feature, executing the DCI stuff in a container, whether it's for setting up OpenShift or running tests before deploying. I am very happy to present it to you today.

With the Podman image, you'll be able to use dci-pipeline:

- Without having to worry about the DCI installation prerequisites.
- On a system not supported by DCI, whether it's a beta version of RHEL, an older version of Ansible, or other.
- Without needing to keep up with DCI package updates.

Indeed, the DCI image is continually updated; it's rebuilt whenever a dependency is updated. See for yourself in [the quay registry](https://quay.io/repository/distributedci/dci-pipeline?tab=tags&tag=latest).

In the rest of the article, we'll see how to use this image and what its limitations are.

# Usage

To use the Podman version of dci-pipeline, you only need to install the RPM package `dci-pipeline-podman`.

If the RPM registry for DCI is not installed, download the one you need on [packages.distributed-ci.io](https://packages.distributed-ci.io/).

        # dnf -y install https://packages.distributed-ci.io/dci-release.el8.noarch.rpm

Then install the package.

        # dnf install -y dci-pipeline-podman

You don’t need to install Ansible or other DCI package on your server, everything is included in the Podman image with their latest version.

Using it is just as simple. The parameters are the same as for dci-pipeline. All arguments passed to the command are directly given to the version of dci-pipeline within the container.

        $ dci-pipeline-podman --help
        Usage: /usr/local/bin/dci-pipeline [<jobdef name>:<key>=<value>...] [<pipeline file>]

The command dci-pipeline-podman always gets the latest available version of the image, so you are all time up to date.

# Precaution

There's something you need to be careful about. The user's HOME directory is directly mounted into the `/var/lib/dci-openshift-agent/` directory within the container. This is how you can access the pipeline file.

This means you need to adjust any file paths in your pipeline files. Let's look at an example:

        cat ~/dev1/ocp-latest-pipeline.yaml
        - name: ocp-latest
          stage: openshift
          ansible_cfg: /var/lib/dci-openshift-agent/dev1/ansible.cfg
          ansible_extravars:
            dci_config_dirs:
              - /var/lib/dci-openshift-agent/dev1
          ansible_inventory: /var/lib/dci-openshift-agent/dev1/dev-hosts
          ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
          topic: OCP-4.14
          components:
            - ocp?tags:build:dev
          dci_credentials: /var/lib/dci-openshift-agent/.config/dci-pipeline/dev1.yml

Here, within the host's HOME directory, we have a `dev1` directory with all the configuration files. To launch the deployment, I just need to execute:

        $ dci-pipeline-podman /var/lib/dci-openshift-agent/dev1/ocp-latest-pipeline.yaml

By default, dci-pipeline-podman only mounts the user's home, but it is possible to use files outside, example in `/opt` or `/etc` with the optional variable CONTAINER_MOUNTED_PATHS in ~/.config/dci-pipeline/config.
Example: 
        cat ~/.config/dci-pipeline/config
        CONTAINER_MOUNTED_PATHS=(
          "/var/lib/dci"
          "/opt/cache"
          "/etc/firewalld"
          "/tmp"
        )


As of today, all tests have been carried out in a connected environment. We encountered some challenges in an disconnected environment, in particular because of SElinux. We are currently working on it and will update this article when the disconnected mode is fully functional.

# Conclusion

As explained, dci-pipeline-podman is the easiest way to deploy and test OpenShift with DCI using Podman.

In this blog post, we have seen how to adapt its pipeline files in order to use it with peace of mind as well as the current limitations of the tool.
