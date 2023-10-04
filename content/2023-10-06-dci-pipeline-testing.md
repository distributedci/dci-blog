Title: Practical examples of dci-pipeline usage to speed up your OCP cluster testing
Date: 2023-10-06 10:00
Category: divulgation
Tags: dci, dci-pipeline, testing
Slug: dci-pipeline-testing
Author: Ramon Perez
Github: ramperher
Summary: This blog post presents practical examples of dci-pipeline usage that can be useful when dealing with testing and troubleshooting of OCP clusters and workloads deployed on top of it with DCI.

[TOC]

# Introduction

We have been talking about dci-pipeline in different blog posts already published here. Starting with a [soft introduction](dci-pipeline.html) about this tool, continuing with some tips to [expand your knowledge](expand-dci-pipeline-knowledge.html) to a higher level, and now it takes the time to put into practice all what you've learned with all these resources (and of course, don't forget [the official documentation](https://doc.distributed-ci.io/dci-pipeline)!).

This blog post will show you practical examples about the usage of dci-pipeline, including tools such as `dci-queue`, `dci-pipeline-schedule` and `dci-pipeline-check`, so that you can have some useful references for your future interactions with dci-pipeline.

# Environment used for the examples

For the commands to be presented in this blog post, let's assume we have the following resources available:

- A couple of queue management systems, built with `dci-queue`. Remember you can quickly set them up by following [this blog post](dci-queue.html). Let's suppose each queue has two resources available, and that `queue1` is the default queue (i.e. `DCI_QUEUE` environment variable is configured to point to `queue1`).

        $ dci-queue list queue1
        Resources on the queue1 pool: cluster1 cluster2
        Available resources on the queue1 pool:
        Executing commands on the queue1 pool:
        Queued commands on the queue1 pool:

        $ dci-queue list queue2
        Resources on the queue2 pool: cluster3 cluster4
        Available resources on the queue2 pool:
        Executing commands on the queue2 pool:
        Queued commands on the queue2 pool:

- An OCP installation pipeline, placed in `PIPELINES_DIR`, variable which points to the directory where `dci-pipeline-check|schedule` will retrieve the pipelines. The pipeline can be something like this:

        $ cat ocp-vanilla-pipeline.yml
        - name: openshift-vanilla
          stage: ocp
          ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
          ansible_inventory: /etc/dci-pipeline/inventory
          dci_credentials: /etc/dci-openshift-agent/dci_credentials.yml
          topic: OCP-4.12
          ansible_extravars:
            variable: value
            dci_config_dirs:
              - /var/lib/dci/hook-example
          components:
            - ocp
          outputs:
            kubeconfig: "kubeconfig"

In this example, we're deploying the latest OCP 4.12 release available, exposing an extravars called `variable` and the `kubeconfig` as output. Also, we're using `dci_config_dirs` variable to include a directory from which we will load [hooks](customizable-ansible-hooks.html).

- A couple of CNF deployment pipelines, again placed in `PIPELINES_DIR`.

        $ cat cnf1-pipeline.yaml
        - name: first-cnf
          stage: cnf
          prev_stages: [ocp]
          ansible_playbook: /usr/share/dci-openshift-app-agent/dci-openshift-app-agent.yml
          ansible_inventory: /etc/dci-pipeline/inventory-cnf1
          dci_credentials: /etc/dci-openshift-app-agent/dci_credentials.yml
          ansible_extravars:
            variable1: value1
          use_previous_topic: true
          components:
            - cnf1
          inputs:
            kubeconfig: kubeconfig_path

        $ cat cnf2-pipeline.yaml
        - name: second-cnf
          stage: cnf
          prev_stages: [ocp]
          ansible_playbook: /usr/share/dci-openshift-app-agent/dci-openshift-app-agent.yml
          ansible_inventory: /etc/dci-pipeline/inventory-cnf2
          dci_credentials: /etc/dci-openshift-app-agent/dci_credentials.yml
          ansible_extravars:
            variable2: value2
          use_previous_topic: true
          components:
            - cnf2
          inputs:
            kubeconfig: kubeconfig_path

Note that both pipelines requires an OCP installation to be launched, since they have `prev_stages: [ocp]`. They also inherit the topic used in the OCP installation (in our case, OCP 4.12), and can also retrieve the `kubeconfig` exposed by the OCP installation pipeline by using the `inputs` field. Apart from this, each pipeline uses a different component, different extravars, and different inventories.

Just another thing: the pipeline names and the `name` field are different on purpose, just to clarify the syntax for the examples we'll see next.

# Running pipelines

Let's start with the simplest: just run a pipeline (or set of pipelines) that are already defined, using the stable version of the DCI agents and the hooks. For this, we have two options:

- `dci-pipeline` command can make the trick, but for this, you will need to explicitly set up the path where pipelines and inventories are placed.
- `dci-pipeline-schedule` command, which allows us to avoid specifying the paths for the pipeline files and inventories.

Let's see what we can do with this tool.

## Running an ocp pipeline

This is the simplest example we can have:

        $ dci-pipeline-schedule ocp-vanilla

With `dci-pipeline-schedule`, this is as simple as running the command by providing the pipeline file name, but removing `-pipeline.yml`. That's all. This will schedule a new job in your default queue, and will be launched in any resource available. If all resources are busy, this will be queued and assigned to the first available resource in the queue.

The very same instruction with `dci-pipeline` command would be the following (among other variables that can be used):

        $ dci-pipeline openshift-vanilla:ansible_inventory=/etc/dci-pipeline/inventory /path/to/ocp-vanilla-pipeline.yml

This is just to highlight the simplicity of using `dci-pipeline-schedule` instead of `dci-pipeline`. Then, for the remaining examples, we will make use of `dci-pipeline-schedule`, as it's simpler and more concise.

## Running an ocp pipeline on an already reserved cluster with some custom variables

This becomes more complicated, but not impossible :)

        $ DCI_QUEUE_RESOURCE=cluster2 dci-pipeline-schedule ocp-vanilla openshift-vanilla:ansible_extravars=dci_tags:daily,variable:another_value,dci_teardown_on_success:false

Here, we are adding the following arguments:

- Firstly, we are instructing `dci-queue` to specifically use one of the resources from the default queue, `cluster2`. To avoid issues, you must reserve the resource beforehand; if not, if a new job is scheduled in that resource, that job will override your job. Remember you can use `dci-queue remove-resource` for that purpose.
- Then, we are providing some variables, by using the syntax `openshift-vanilla:ansible_extravars=<var1>:<value1>,<var2>:<value2>...`. Generally speaking, you need to use the value of the `name` field from your pipeline (in this case, `openshift-vanilla`), then specify what field of the pipeline you want to upload. In this case, we are providing new extravars (or even updating some of them, such as `variable`, already defined in the pipeline). Another way of doing the same is by defining each variable in a separate argument, something like `openshift-vanilla:ansible_extravars=<var1>:<value1> openshift-vanilla:ansible_extravars=<var2>:<value2>...`. Here, we don't need to use commas to separate the variables, but we need to use the structure `openshift-vanilla:ansible_extravars=` for each case.

Also, if you want to change a different field from the pipeline, you can also do it by following the same structure. For example, to update the inventory, you can do it by using `openshift-vanilla:ansible_inventory=/path/to/new/inventory`.

Note that the order of the arguments is not relevant. You can specify the custom variables firstly, then the pipeline to use (but always use `dci-pipeline-schedule` first or after env variables only).

## Running multiple pipelines, ocp and cnf

Now, we have the case where we want to execute multiple pipelines sequentially; in our case, the three pipelines we have defined previously. We can do it in the following way:

        $ dci-pipeline-schedule ocp-vanilla cnf1 cnf2

This implies that `ocp-vanilla` pipeline will be launched firstly, then `cnf1`, and then `cnf2`. Since `cnf1` and `cnf2` depends on an `ocp` job, if `ocp-vanilla` fails, `cnf1` and `cnf2` will not be launched, but if it passes, then both jobs will be launched sequentially; `cnf1` firstly, then `cnf2`, regardless of the result of `cnf1` job (since `cnf2` depends on `ocp` jobs, not on `cnf` jobs).

If you need to run it in a specific cluster, just use `DCI_QUEUE_RESOURCE` as done in the previous example.

And what about providing custom variables? Same syntax:

        $ dci-pipeline-schedule ocp-vanilla cnf1 cnf2 openshift-vanilla:ansible_extravars=dci_tags:daily first-cnf:ansible_inventory=/path/to/new/inventory

Here, we're providing a new extravars for the `ocp-vanilla` pipeline, and overriding `ansible_inventory` variable in `cnf1` pipeline. Again, to refer to the pipeline, you have to use the value of the `name` field from the pipeline; so, for `cnf1`, we use `first-cnf`. And again, the order of the arguments is not relevant.

## Scheduling a cnf job on top of a running cluster

Imagine you already have an up-and-running OCP cluster (e.g. with OCP 4.13), and you only want to run a CNF job (e.g. `cnf1`) in that cluster (e.g. `cluster2`). You can do it!

        $ DCI_QUEUE_RESOURCE=cluster2 dci-pipeline-schedule cnf1 first-cnf:ansible_extravars=kubeconfig_path:/path/to/cluster2/kubeconfig first-cnf:topic=OCP-4.13

For this case, you need to provide three variables:

- The cluster you want to use (remember to reserve it).
- The correct `kubeconfig_path`, pointing to the kubeconfig from the cluster you have up and running.
- The OCP topic related to the OCP version you're launching.

## Scheduling a job in a resource from a different queue

Now, we want to deploy a job in a resource from a different queue, e.g. `queue2`. How to do it? Just use `DCI_QUEUE` env var, and `dci-pipeline-schedule` will schedule the job in a free resource from that queue:

        $ DCI_QUEUE=queue2 dci-pipeline-schedule ocp-vanilla

## Selecting specific job stages to be run

In this case, let's suppose you want to launch specific stages from a job (i.e. pre-run, install, tests, teardown...). The DCI agents make use of `ansible_tags` for that purpose. For example, if you want to just launch the teardown for an OCP installation, you need to instruct `ansible_tags` in the following way (`job` and `dci` tags are used to create the job on DCI):

        $ dci-pipeline-schedule ocp-vanilla openshift-vanilla:ansible_tags=dci,job,success

And of course, you can combine this with the features presented before. If you want to pass some extravars, e.g. to make sure that you're deleting the existing resources:

        $ dci-pipeline-schedule ocp-vanilla openshift-vanilla:ansible_tags=dci,job,success openshift-vanilla:ansible_extravars=dci_teardown_on_success:true openshift-vanilla:ansible_extravars=dci_teardown_on_failure:true

For the opposite case (avoid running a particular stage), you can use then `ansible_skip_tags`. For example, if you want to run an OCP installation but without running the tests stage, you can do this:

        $ dci-pipeline-schedule ocp-vanilla openshift-vanilla:ansible_skip_tags=testing

Same format is followed for CNF jobs managed by `dci-openshift-app-agent`, but using the corresponding tags that are defined in that agent.

# Testing changes

Now, we have the case where we want to run a pipeline, but to test changes that have been made in any of the repositories that are under usage when launching the DCI job. The change may come from any of the DCI agents used ([`dci-openshift-agent`](https://softwarefactory-project.io/r/q/project:dci-openshift-agent+status:open) or [`dci-openshift-app-agent`](https://softwarefactory-project.io/r/q/project:dci-openshift-app-agent+status:open)), which are created in Gerrit, or by any private repository where you define hooks, pipelines, etc., where we typically use Github.

The tool to use for this case is `dci-pipeline-check`, which more or less follows the same syntax than `dci-pipeline-schedule`, but with some differences, mainly related to the definition of the change to check.

Note you also have available `dci-check-change`, but that's a different tool, not related to `dci-pipeline`, and it's mainly related to the testing of changes on DCI agents. You can check some information about it in these blog posts already published: [(1)](using-dci-check-change-to-test-your-changes.html) and [(2)](mastering-dci-check-change.html).

## Test a new deployment of OCP with a Gerrit change on a specific cluster

Imagine you have a change on `dci-openshift-agent`, created on Gerrit (id = 123456789), that you want to test on a specific cluster from your queue (e.g. `cluster2`). This can be done in the following way:

        $ DCI_QUEUE_RESOURCE=cluster2 dci-pipeline-check 123456789 ocp-vanilla

The only difference with `dci-pipeline-schedule` is that we're including, after the command, the ID of the change we want to test. The rest is exactly the same: you need to reserve your cluster to avoid issues with new jobs that may come (or if you don't need to select a specific resource, just remove `DCI_QUEUE_RESOURCE` and the job will be scheduled in any available resource), you can define custom variables, etc. But here, **the order matters**: the change ID must always come after the `dci-pipeline-check` command name.

## What about Github PRs?

For Github PRs, it's just the same, but you need to pass to `dci-pipeline-check` the URL of the PR:

        $ DCI_QUEUE_RESOURCE=cluster2 dci-pipeline-check https://github.com/<org>/<repo>/pull/<id> ocp-vanilla

## Test a cnf change on top of a running cluster

For this case, the format changes a little bit, compared to `dci-pipeline-schedule`, because you need to pass the kubeconfig path after the change reference. Also, note that you don't need to specify `DCI_QUEUE_RESOURCE` in this case, since the kubeconfig will always redirect you to the proper cluster (but don't forget to remove the resource from the queue to avoid issues, as usual). For example, to launch `cnf1` under these conditions:

        $ dci-pipeline-check <Gerrit change ID/Github PR URL> /path/to/kubeconfig cnf1

And again, everything we've explained before can be used here: you can define extravars, you can schedule multiple pipelines sequentially, you can use `ansible_tags` to execute specific stages, etc.

# Conclusion

We hope these examples are useful for you when dealing with OCP troubleshooting with `dci-pipeline`. If you need support on any of these cases, don't hesitate to reach us, we'll be glad to help!
