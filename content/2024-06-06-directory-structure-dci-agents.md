Title: Directory structure built on OCP DCI agents
Date: 2024-06-06 10:00
Category: divulgation
Tags: dci, dci-openshift-agent, dci-openshift-app-agent, dci-pipeline, directory-structure
Slug: directory-structure-dci-agents
Author: Ramon Perez
Github: ramperher
Summary: This blog post aims to guide DCI users on locating the resources provided by our DCI agents (dci-openshift-agent, dci-openshift-app-agent, and dci-pipeline) on the server used to launch these agents. It also includes an explanation of each piece of installed code. Having this information clearly described is crucial for troubleshooting, as it helps users know where to look in the DCI agents' code.

[TOC]

# Introduction

Some DCI users may not clearly understand how the agents' code is structured once they are installed in their servers, so they take long time to locate the resources they would need to check during the usage of the DCI agents or during troubleshooting.

Currently, the README documentation of each agent explains what are the files that are installed and their location in the server. Based on that information, this blog post will help users to understand why these files are placed in these locations and their roles in the execution process.

The projects covered on this blog post are the following:

- [dci-openshift-agent](https://github.com/redhat-cip/dci-openshift-agent)
- [dci-openshift-app-agent](https://github.com/redhat-cip/dci-openshift-app-agent)
- [dci-pipeline](https://github.com/redhat-cip/dci-pipeline)

# General concepts

If you look at the GitHub repositories mentioned earlier, you will see a clear directory structure, but these files are not placed in the same directory once onboarded in the server where you install the DCI agents.

Remember that these DCI agents are all packaged and available as RPMs, so you eventually install the DCI agents using the RPM. If you take a look at each project's repository, you will find a `.spec` file, which contains the instructions used by `rpmbuild` to generate the RPM.

In the case of `dci-pipeline`, the `.spec` file directly includes the [commands](https://github.com/redhat-cip/dci-pipeline/blob/master/dci-pipeline.spec) that are launched to place each folder/file in the correct destination. However, for `dci-openshift-agent` [(1)](https://github.com/redhat-cip/dci-openshift-agent/blob/master/dci-openshift-agent.spec) and `dci-openshift-app-agent` [(2)](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/dci-openshift-app-agent.spec), you can also find a Makefile for each case: [(1)](https://github.com/redhat-cip/dci-openshift-agent/blob/master/Makefile), [(2)](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/Makefile), which is eventually called in the `.spec` file to run the installation steps.

In addition to placing files and folders in the server, each RPM also holds instructions to create system users with sudo permissions and system groups, or to create system services. These features and utilities are beyond the scope of this blog post; we will just concentrate on files and folders that directly impact DCI users when dealing with the execution of DCI jobs.

So, let's delve into the project structure of each agent, checking the meaning of the most important files and folders provided, and identifying their location after installing the RPM on your server.

# dci-openshift-agent

From the [README](https://github.com/redhat-cip/dci-openshift-agent/?tab=readme-ov-file#folders-and-files-location), you will have some introductory information regarding the places where folders and files are located. Here, we will expand this information:

- `/etc/dci-openshift-agent`: this directory contains configuration files placed by the RPM, primarily templates, but you can save here a `config` file to declare environment variables to be consumed by the agent. Templates you can find here are:
    - `dcirc.sh.dist` file, which is a template of the `dcirc.sh` file you need to use to save your DCI credentials (based on your DCI's remote-ci) when running DCI jobs.
    - `hooks` it is a directory that acts as a placeholder for partner hooks that you can use as base to build your own customized hooks.
    - `settings.yml` file, with a standard setup to launch the agent with the legacy mode. If you still have some settings file and you want to transform them to `dci-pipeline`'s format, take a look below at [dci-pipeline](#dci-pipeline) section to see how to do this.
- `/usr/share/dci-openshift-agent/`: this directory contains:
    - The main Ansible logic that drives this agent, composed by:
        - The `dci-openshift-agent.yml` playbook, which is the entry point to launch an OCP installation with DCI.
        - All the playbooks used during the agent execution, saved in the `plays` folder. You will see there are no roles in this project, and it is because we are importing the [redhatci-ocp collection](https://github.com/redhatci/ansible-collection-redhatci-ocp).
        - Files for the Ansible configuration (`ansible.cfg`) and the provision of default values for variables (`group_vars` folder).
    - Other interesting artifacts, that you can find in the `utils` folder (e.g. [cleanup scripts](https://github.com/redhat-cip/dci-openshift-agent/tree/master/utils/cleanup-scripts)).
- `/var/lib/dci-openshift-agent`: under the `samples` directory, you will find some examples that you can use in your labs, referring to useful deployments (such as [deploying Assisted on libvirt](https://github.com/redhat-cip/dci-openshift-agent/tree/master/samples/assisted_on_libvirt)) or extra utilities (like a [local registry deployment](https://github.com/redhat-cip/dci-openshift-agent/tree/master/samples/roles/local-registry)).

# dci-openshift-app-agent

The structure of `dci-openshift-app-agent` is quite similar to `dci-openshift-agent`'s one, but it focuses on the deployment of workloads, or running processes, on top of an already deployed OCP cluster. In the [README](https://github.com/redhat-cip/dci-openshift-app-agent?tab=readme-ov-file#folders-and-files-location), you can find some information, but here we provide the differences compared with `dci-openshift-agent`:

- `/etc/dci-openshift-app-agent`: serves as a directory to place the required configuration files for this agent. Here, you will find the presence of `dcirc.sh.dist` or `settings.yml` files and `hooks` folder, with the same meaning than in `dci-openshift-agent`, but here we can also fild a `hosts.yml` file, which is typically used as-is when running `dci-openshift-app-agent`, since the hosts file points to `localhost` and the agent relies on the cluster's kubeconfig file to interact with the cluster resources. You can place here a `config` file to define environment variables to be consumed by the agent.
- `/usr/share/dci-openshift-app-agent/`: it holds the Ansible configuration and playbooks, having `ansible.cfg` file for the Ansible configuration, `dci-openshift-app-agent.yml` main playbook, `group_vars` folder for defining default values to variables, and `plays` folder containing the playbooks that are used in the agent. Then, similarly to `dci-openshift-agent`, there is an `utilities` folder to place some utils, such as an [internal registry](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/utilities/internal-registry).
- `/var/lib/dci-openshift-app-agent`: it provides a `samples` folder with examples of workloads that you can launch with this agent; for example, `control_plane_example`, a [very simple workload](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/samples/control_plane_example) based on a webserver deployment, or `tnf_test_example`, a [set of resources](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/samples/tnf_test_example) that are suitable for CNF Certification using the [Red Hat Best Practices Test Suite for Kubernetes](https://github.com/test-network-function/cnf-certification-test).

# dci-pipeline

The case of `dci-pipeline` differs from the agents as it's not an "agent" at all; it provides a set of tools to enable the deployment of pipelines to run DCI jobs. In the [README](https://github.com/redhat-cip/dci-pipeline?tab=readme-ov-file#folders-and-files-location), you can find a review of the files and folders you can find here. Details are below:

- `/etc/dci-pipeline`: in this case, it just contains an empty `pipeline.yml` file to serve as a template. Typically you will create a folder in a separate repo to save your pipelines and use them from there. But also, this folder can be used to hold a `config` file with some interesting variables to be consumed by `dci-pipeline`, e.g. `PIPELINES_DIR` variable pointing to the location of the pipelines (extracted from [here](https://github.com/redhat-cip/dci-pipeline/tree/master?tab=readme-ov-file#dci-pipeline-schedule)).
- `/usr/bin`: in this folder, you will find some executable files that serve as entry point for the main utilitie, (also with `podman` flavour, provided in this project. Some of these scripts come from `tools` folder, and others are generated from folders like `dciagent`, `dcipipeline` or `dciqueue`, and their podman flavours are located in `container` folder. These are:
    - `dci-pipeline`: standard way of launching pipelines with DCI. More documentation can be found [here](https://github.com/redhat-cip/dci-pipeline/tree/master?tab=readme-ov-file#dci-pipeline-command).
    - `dci-auto-launch`: this allows to automatically schedule pipelines based on strings in the description of Github's pull requests or Gerrit's reviews. It relies on a configuration file that can be found in `~/.config/dci-pipeline/auto.conf`. More details can be seen [here](https://github.com/redhat-cip/dci-pipeline/tree/master?tab=readme-ov-file#dci-auto-launch).
    - `dci-pipeline-schedule`: [wrapper](https://github.com/redhat-cip/dci-pipeline/tree/master?tab=readme-ov-file#dci-pipeline-schedule) to call `dci-pipeline` without specifying the paths for the pipeline files and the inventories.
    - `dci-pipeline-check`: [another wrapper](https://github.com/redhat-cip/dci-pipeline/tree/master?tab=readme-ov-file#dci-pipeline-check) to test a Github pull request or a Gerrit review with a specific pipeline.
    - `dci-queue`: this [command](/https://github.com/redhat-cip/dci-pipeline/tree/master?tab=readme-ov-file#dci-queue-command) allows you to execute commands consuming resources from pools, so that you can schedule calls to DCI pipeline that are eventually queued in a set of resources you have defined in advance.
    - `dci-agent-ctl`: as defined in the [README](https://github.com/redhat-cip/dci-pipeline/tree/master?tab=readme-ov-file#dci-agent-ctl), it is a thin layer on top of `dci-pipeline` to consume regular agent settings transparently.
    - `dci-rebuild-pipeline`: this command [rebuilds a pipeline](https://github.com/redhat-cip/dci-pipeline/tree/master?tab=readme-ov-file#how-to-rebuild-a-pipeline) based on a given DCI job, using the components extracted from that job.
    - `dci-settings2pipeline`: this allows you to run the parsing capabilities of `dci-agent-ctl` but without executing `dci-pipeline`, just outputing the pipeline file. More information [here](https://github.com/redhat-cip/dci-pipeline/tree/master?tab=readme-ov-file#dci-settings2pipeline).
    - `dci-diff-pipeline`: this [compares two jobs](https://github.com/redhat-cip/dci-pipeline/tree/master?tab=readme-ov-file#how-to-see-components-diff-between-two-pipelines) to check the differences in components between two jobs.
- `/usr/share/dci-pipeline`: you will find here some scripts that are placed in the `tools` folder from the repo, that can be use in standalone mode or using `podman` flavour (meant to be run from a podman container). Some of them are used by the scripts placed in `/usr/bin`. They are:
    - `alert`: send alerts to Google Chat and/or Slack from monitored repositories. This can be used, for example, to define webhooks which allows you to send alerts when a DCI job fails while testing PRs on specific repositories.
    - `common`: import environment variables that may be defined in `~/.config/dci-pipeline` (folder that is created when installing `dci-pipeline`) and `/etc/dci-pipeline` folders.
    - `dci-pipeline-helper`: called from `dci-pipeline-schedule` with the information from `dci-queue` to be able to expand the `@RESOURCE` and `@QUEUE` strings (more information about these two concepts can be found [here](https://github.com/redhat-cip/dci-pipeline/tree/master?tab=readme-ov-file#link-between-dci-pipeline-and-dci-queue-queue-and-resource)) with the right information and then call `dci-pipeline` with the right arguments.
    - `extract-dependencies`: this is used to extract the content from Github pull requests or Gerrit reviews that are included as dependencies of the change you are testing.
    - `get-config-entry`: used from scripts that interacts with Github/Gerrit repos to extract some configuration such as tokens or extra config.
    - `loop_until_failure` and `loop_until_success`: loops used by `dci-pipeline-check` logic.
    - `send_status`: send messages to Github PRs and Gerrit reviews regarding some status of the DCI pipeline execution that needs to be reported.
    - `send_comment`: send messages to Github PRs and Gerrit reviews to put a comment in the history of these PRs/reviews.
    - `test-runner`: utility that is called by `dci-pipeline-check` to properly translate the configuration and variables to adapt to the changes that are about to be tested, then calling `dci-pipeline` with the proper arguments.
    - `yaml2json`: transform a YAML input in JSON output.

# Conclusions

We hope this information is useful for you when dealing with any of `dci-openshift-agent`, `dci-openshift-app-agent` and `dci-pipeline` projects, to be able to easily locate the resources you may need to check when dealing with troubleshooting.
