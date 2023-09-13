Title: Expand your dci-pipeline knowledge
Date: 2023-09-14 10:00
Category: divulgation
Tags: dci, dci-pipeline, testing
Slug: expand-dci-pipeline-knowledge
Author: Ramon Perez, Pierre Blanc
Github: ramperher, pierreblanc
Summary: This blog post continues the overview of dci-pipeline and related testing tools, focusing on some useful features that can really help you when addressing testing and troubleshooting with DCI jobs.

[TOC]

# Introduction

If you remember from old blog posts, [we already commented about dci-pipeline](dci-pipeline.html), describing what are the key benefits from using it, how to install it and how to use it, and reporting the basics about this useful tool. If you haven't read this first dci-pipeline introductory blog post, I advise you to do so before reading this one. Remember dci-pipeline is meant to be the recommended way of launching DCI jobs, instead of using the old scripts included in the agents.

In this blog post, we will continue addressing dci-pipeline tool, but referring to more advanced features and tools that can really help you when dealing with testing and troubleshooting of OCP clusters with DCI.

All the features described in this blog post are defined in [the official documentation](https://doc.distributed-ci.io/dci-pipeline).

# Clarification in some concepts

## Variable precedence is also present

In the previous dci-pipeline blog post, we discussed the definition of variables in the pipelines and how to override the values in the command line.

But we may reach the point in which we have the same variable defined in different places (a pipeline, a defaults file, an inventory file, etc.). What happens in that case? Remember that Ansible applies the [variable precedence](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence) to determine what value should be used for a variable defined in different places, and the same happens for variables defined under ansible_extravars in the pipelines, since the DCI agents are based on Ansible playbooks.

As a general rule, the following priority order is followed in the typical places you will interact with when playing with DCI (from more to less priority):

- Command line
- Ansible extravars
- Inventory variables
- Default variables

## DCI components usage

We have a huge [blog post](https://blog.distributed-ci.io/using-dci-components-in-partner-hooks.html) talking about DCI components, where it is also explained how to use them, distinguishing between settings files and pipelines. Remember that in pipelines, we directly use the `components` variable, where we can declare the component we want to retrieve, using some query-based syntax to select a component based on a specific version or other attributes. That’s something different compared to settings files, where other variables were used for this same purpose (`dci_components`, `dci_components_by_query`...).

## Override inventory and Ansible config file

There are two variables can help you to solve issues such as properly defining the target hosts of your deployment (the case of `ansible_inventory`), or to instruct Ansible to look for Ansible roles used in your executions in a specific directory (thanks to `ansible_cfg`).

These two variables, called `ansible_inventory` and `ansible_cfg`, that allow you to modify the hosts inventory and the Ansible configuration file used for a given job, respectively. These variables are defined at the same level than variables like `name`, `stage` or `ansible_playbook`, for example with the default paths for dci-openshift-agent:

        - name: openshift-vanilla
          stage: ocp
          ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
          ansible_inventory: /etc/dci-openshift-agent/hosts
          ansible_cfg: /usr/share/dci-openshift-agent/ansible.cfg



## dci-openshift-agent? dci-openshift-app-agent?

Imagine you want to run a job with dci-openshift-agent to install an OCP cluster and also including a DCI component called a_component, and then, to run a workload on top of this cluster with dci-openshift-app-agent, referenced with a component called b_component. The way of naming these two components on each pipeline is exactly the same!

The key benefit from using dci-pipeline is that you can use the same source of information (pipelines), with the same fields and variables, to run your jobs with dci-openshift-agent or with dci-openshift-app-agent, depending on your needs.

Ultimately, utilizing dci-pipeline streamlines and simplifies your use cases and provides you with a straightforward means of reusing the utilized data.


# Testing tools used under dci-pipeline scope

## Convert settings to pipelines

If you are new on dci-pipeline and you have some experience with the old way of launching DCI jobs (i.e. using settings), then you may think that it would be interesting to be able to reuse what you did in the past instead of creating your new pipelines from scratch. Well, dci-pipeline allows you to achieve that.

And there are two ways of addressing this goal. The first one is by using `dci-agent-ctl` command. It is a thin layer on top of dci-pipeline to consume regular agent settings transparently. For example:

        $ dci-agent-ctl /etc/dci-openshift-agent/settings.yml /etc/dci-openshift-app-agent/settings.yml

In particular, it will translate the settings into pipelines and call dci-pipeline. For this, you need to create a settings file with `dci_name` variable and `dci_agent` pointing to the name of the agent (openshift/openshift-app).

The second way of addressing this challenge is for users that wants to use the parsing capabilities of `dci-agent-ctl` and just output the pipeline file without executing dci-pipeline. For this, you can use `dci-settings2pipeline`, like this:

        $ dci-settings2pipeline /etc/dci-openshift-agent/settings.yml /etc/dci-openshift-app-agent/settings.yml /tmp/pipelines.yml

You have more information about these two commands in the following [chapter](https://doc.distributed-ci.io/dci-pipeline/#dci-agent-ctl) in the dci-pipeline docs.

## dci-queue

It allows the user to execute commands consuming resources from pools. These pools are specific to the user executing the commands.

You can take a look to the [dci-queue blog post](https://blog.distributed-ci.io/dci-queue.html) and to the [official documentation](https://doc.distributed-ci.io/dci-pipeline/#dci-queue-command) to learn more about this tool.

## dci-pipeline-schedule

It is a wrapper to call dci-pipeline without specifying the paths for the pipeline files and the inventories.

So, for example, to do:

        $ dci-pipeline ~/pipelines/ocp-vanilla-pipeline.yml ~/pipelines/workload-pipeline.yml

You will just need to run the following:

        $ dci-pipeline-schedule ocp-vanilla workload

In the [dci-pipeline-schedule documentation](https://doc.distributed-ci.io/dci-pipeline/#dci-pipeline-schedule), you can find more details about variables required to make this work.

Also, you can also define the default `dci-queue` queue with the `DEFAULT_QUEUE` variable. To schedule on a specific `dci-queue` pool, use `-p` like this:

        $ dci-pipeline-schedule -p my-pool ocp-vanilla workload

## dci-pipeline-check

To test a Github/Gerrit change, with a specific pipeline, you can use `dci-pipeline-check` utility.

For example, we can test a Github pull request from the dci-labs/pipelines repository, with the `dci-queue` feature to select the queue to use:

        $ dci-pipeline-check https://github.com/dci-labs/pipelines/pull/6 -p my-pool ocp-4.10-vanilla workload

There are some considerations to this command to have in mind that you can find in the [docs](https://doc.distributed-ci.io/dci-pipeline/#dci-pipeline-check), Consider the following inquiries:

- How to properly interact with private repositories.
- How to use multiple accounts.
- How to vote in the changes based on the results of the DCI jobs (e.g. to avoid merging a change if the DCI job launched for that change is failing).

Also, you may have the case in which you want to test a change on `dci-openshift-app-agent`, and you have already deployed an OCP cluster. For this case, you can launch `dci-pipeline-check` in the following way, providing the kubeconfig as argument:

        $ dci-pipeline-check 26269 /path/to/kubeconfig workload

This bypasses the queue mechanism and directly launches the application pipelines on the OCP cluster.
if you are using dci-queue for the cluster, you can remove the resource for the queue during your tests to be sure nobody else will redeploy it.

# And there are even more to explore!

If you check the [dci-pipeline docs](https://doc.distributed-ci.io/dci-pipeline), you will find more and more features that may be interesting for you, depending on your case. For example, we can see features like:

- [Rebuild a pipeline](https://doc.distributed-ci.io/dci-pipeline/#how-to-rebuild-a-pipeline) (in case of a failure).
- [Compare components between two pipelines](https://doc.distributed-ci.io/dci-pipeline/#how-to-see-components-diff-between-two-pipelines).
- Special variables defined in the pipelines ([tagging and retrying](https://doc.distributed-ci.io/dci-pipeline/#tagging-and-retrying), [temporary directories](https://doc.distributed-ci.io/dci-pipeline/#instrument-the-pipeline-with-temporary-directories), [environment variables](https://doc.distributed-ci.io/dci-pipeline/#passing-environment-variables), [previous topic](https://doc.distributed-ci.io/dci-pipeline/#previous-topic)...)

So please don’t hesitate to check [the official documentation](https://doc.distributed-ci.io/dci-pipeline) to explore them and to enhance your testing capabilities with dci-pipeline!

# Typical issues you may encounter when transitioning towards pipelines

It’s true that the path to follow to move from settings to pipelines is not always easy. Here we leave some tips that, from our experience with partners, can be useful for you:

- Make sure you are using the correct user when dealing with dci-pipeline, with the correct permissions in the filesystem you’re targeting. Typically, it is better to use a new user, with sudo permissions, and include it in dci-pipeline/dci-openshift-agent/dci-openshift-app-agent groups in the machine where you’re launching DCI.
- Verify you’re able to run SSH in the target hosts with the different users that involve DCI.
- Take care of reviewing the files that are referenced in the pipelines, checking that they are following the correct format (e.g. the dci_credentials file, the inventory file, etc.).
- Make sure your Ansible configuration includes all the roles you’re launching in your DCI jobs.
- Rely on testing tools such as dci-queue, dci-pipeline-schedule and dci-pipeline-check to speed up testing.
- And of course: if it’s the first time you are going to use DCI, just start using dci-pipeline, it is the recommended way !

# Conclusion

This blog post has shown some more advanced topics under dci-pipeline’s umbrella that can be really useful when testing with DCI. Indeed we have seen how to use the components as well as the variable override. But also tools to transition to dci-pipeline with the migration script, the queue system and the execution of specific versions of code.

In future blog posts, we will emphasize some testing tools and include more practical examples to show you the power that they have.

# References

Note that all the information can be extracted from the [dci-pipeline repository](https://github.com/redhat-cip/dci-pipeline) or the [official documentation](https://doc.distributed-ci.io/dci-pipeline). Please refer to the docs provided there to find the latest updates.
