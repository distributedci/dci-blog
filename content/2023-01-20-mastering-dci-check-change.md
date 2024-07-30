Title: Mastering dci-check-change
Date: 2023-01-20 10:00
Modified: 2024-31-07 10:00
Category: how-to
Tags: dci-openshift-agent, dci-openshift-app-agent, developers, dci-check-change, prefixes
Slug: mastering-dci-check-change
Author: Ramon Perez
Github: ramperher
Summary: In previous blog posts, we have learned how to use dci-check-change to effectively test code changes on DCI agents. This blog post aims to bring this knowledge to the next level, learning about specific use cases that may be interesting for testing changes in particular scenarios.

[TOC]

## Introduction

In [this blog post](using-dci-check-change-to-test-your-changes.html), we have already reviewed `dci-check-change` utility to properly test changes submitted to the DCI agents, allowing its testing and validation prior to merge the changes in the master branch.

With that information, you should be already aware of the following:

- Changes in [softwarefactory-project.io](https://softwarefectory-project.io/r) related to DCI agents (both `dci-openshift-agent` and `dci-openshift-app-agent`) are automatically tested by default in one of our virtualized environments with IPI install type.
- The `dci-ci-bot` will include comments in your Gerrit change to track the status of the debug job launched, notifying if the job was successful or not. In case of not having a successful job, the bot will vote -1 and you will only be able to merge your change once fixing that (apart from having enough votes from external reviewers).
- You can force a manual check of the change by running `dci-check-change` in whatever environment to run a debug job including the code from the change. You can also configure the tool to vote/not vote after running the job.
- You can use hints to provide extra configuration in both cases (automatic and manual checks).

This blog post will cover advanced use cases where `dci-check-change` can be used to test complex scenarios like the following:

- Use prefixes to run the change in specific clusters and/or with specific settings.
- Use complex hints to tune the deployment and extra variables you may provide.
- Provide extra variables to your `dci-check-change` job that are not tracked in either settings or hints.
- Enable/disable voting when running `dci-check-change` in your lab.
- In case of having `dci-queue` installed, avoid its usage.

## Using prefixes with dci-check-change

In this [blog post](using-prefixes.html#other-commands-that-may-use-prefixes), we have already covered the basics about using prefixes with `dci-check-change`, to target specifics hosts/settings when running `dci-openshift-agent` or `dci-openshift-app-agent`.

Remember to do the following when trying to use `dci-check-change` with the support of prefixes (which is also documented in [DCI Development docs](https://docs.distributed-ci.io/dci-openshift-agent/docs/development/#testing-a-change)):

- There are two main arguments related to prefixes: `-p <prefix>`, which allows passing a `<prefix>` to `dci-openshift-agent`, and `-p2 <prefix2>`, which does the same with `<prefix2>` but using `dci-openshift-app-agent`.
- If you run something like `dci-check-change <change> -p <prefix> -p2 <prefix2>`, the hosts/settings from `<prefix>` will be used when running the `dci-openshift-agent` job, and on top of that cluster, `<prefix2>` settings would be used in `dci-openshift-app-agent` (because hosts file typically points to localhost in this agent, as we use the KUBECONFIG from the up-and-running cluster to interact with the proper cluster).
- You can run each agent isolatedly with `dci-check-change` and prefixes. However, note the following:
    - With `dci-openshift-agent`, it is enough by running `dci-check-change <dci-openshift-agent-change> -p <prefix>`.
    - But, with `dci-openshift-app-agent`, you need to include an extra argument: the path to find the KUBECONFIG of the cluster you want to use to run the job. So, it would result in: `dci-check-change <dci-openshift-app-agent-change> path/to/kubeconfig -p2 <prefix2>`
- Don't forget to correctly set up `USE_PREFIX` variable to activate the support of prefixes and `CONFIG_DIR` variable on each agent's config (`/etc/dci-openshift-agent/config` or `/etc/dci-openshift-app-agent/config`. It will be the source point from which the prefix logic in `dci-check-change` will start looking at the settings/hosts files related to the prefix you are providing on each case). It is highly recommended to make the value of this variable different on each agent, to avoid collisions.

> When we say `<change>`, remember we can only provide the URL to a specific change to `dci-check-change`, but we can test multiple changes at the same time by including `Depends-On:` or `Build-Depends:` dependencies to the change you are providing to `dci-check-change`, as stated [here](https://docs.distributed-ci.io/dci-openshift-agent/docs/development/#dependencies).

## Using complex hints

You already know that hints allow tunning the execution of the debug job that is run by `dci-check-change`. However, note that there are [different types of hints](https://docs.distributed-ci.io/dci-openshift-agent/docs/development/#hints) that allow you to apply different configurations. Here we will provide some tips for each hint currently available, together with some examples of Gerrit changes making use of them, which can be classified in two different ways:

- Deployment-related hints:
    - `Test-Hints`: this allows you to select a specific deployment to be run by `dci-openshift-agent`. By default, it will run a virtualized IPI deployment (`libvirt` type), but you can select many others, as you can see in the docs: `sno`, `assisted`, etc., or you can even omit the run of a check with `no-check`. This [Gerrit change example](https://softwarefactory-project.io/r/c/dci-openshift-agent/+/25624) runs a change with an `assisted` deployment, for instance.
    - `Test-Upgrade-Hint`: if activated, it runs an upgrade job after your base deployment, like in this [case](https://softwarefactory-project.io/r/c/dci-openshift-agent/+/26403).
    - `Test-App-Hints`: this allows you to select a specific deployment to be run by `dci-openshift-app-agent`, among the ones saved in its [samples folder](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/samples). By default, it runs `control_plane_example`, but you can also select `tnf_test_example` if you want to run a deployment that also performs [Red Hat Best Practices for Kubernetes test suite](cnf-cert-suite-with-dci-openshift-app-agent) over the workloads deployed. Here we have an [example](https://softwarefactory-project.io/r/c/dci-openshift-app-agent/+/27139) running this deployment, with extra arguments.
- Argument-related hints (in the examples provided above for deployment-related hints, you can see they combine them with the argument-related hints presented above):
    - These two hints, `Test-Args-Hints` and `Test-App-Args-Hints`, allow to provide extra variables to the jobs that are running with `dci-openshift-agent` and `dci-openshift-app-agent` respectively. These can be provided in two ways ([this change](https://softwarefactory-project.io/r/c/dci-openshift-app-agent/+/27139) previously commented has examples for both cases):
        - `-e <variable name>=<value>` for simple variables.
        - `-e {"<variable name>":"<variable value>"}` for complex variables like dictionaries, using a JSON format. Avoid the usage of whitespaces in this kind of structure, it may cause problems in the execution.
    - Also, we have `Test-Upgrade-Args-Hints` to pass extra variables to the upgrade job launched by `dci-openshift-agent`. You can also select the OCP topic you want to use as the start version with `Test-Upgrade-From-Topic-Hints` and `Test-Upgrade-To-Topic-Hints` for selecting the target version, in case you want to follow a custom upgrade path. For example, [this change](https://softwarefactory-project.io/r/c/dci-openshift-agent/+/26403) commented before runs an upgrade job from OCP 4.8.x (start version) to OCP 4.9.y (target version).

Also, do not forget to set up correctly the `SUPPORTED_HINTS` variable in your `/etc/dci-openshift-agent/config` file to activate/deactivate the hints that can be allowed in your lab. Depending on its value, this would imply that you can/cannot use some of the hints aforementioned.

By the way, if there's any debug job you want to run, where you have some hints configured in your change, and for that particular job you don't really want to use these hints, so that you only want to run the default scenario, then you can use `-f` argument like `dci-check-change -f <change>` to disobey hints.

## Provide extra variables without using prefixes or hints

If you don't want to rely on prefixes or hints to provide some specific variables to some jobs, you can directly pass extra variables to `dci-check-change` by appending `-e "<variable name>"="<value>"` for some simple cases. However, its usage is limited to really simple variables, so we recommend the usage of prefixes or hints for more complex cases.

## Vote? Or not vote?

If you follow the steps to [set up a continuous integration system to validate changes](https://docs.distributed-ci.io/dci-openshift-agent/docs/development/#continuous-integration), don't forget to set up the `DO_VOTE` variable in your `/etc/dci-openshift-agent/config` file, so that `dci-check-change` will vote when running the jobs, else it will not.

Also, you have `-n` argument in `dci-check-change` (e.g. `dci-check-change -n <change>`) to force the utility not to vote or comment on changes.

## Avoid dci-queue usage

This tip is a simple one. `dci-queue` is a great utility to properly manage a lab composed by different resources that can be used for testing. If you want to avoid `dci-queue` when using `dci-check-change`, you need to set up `NO_DCI_QUEUE` as an environment variable (always when `dci-queue` is available).

## Conclusion

To sum up, we have seen several examples of the power and flexibility that `dci-check-change` can bring us to test different, complex scenarios. Moreover, here we leave some recommendations related to the topics we have covered in this blog post:

- If you have different labs and/or configurations to be used when deploying a DCI job, we recommend to use prefixes together with `dci-check-change` to be able to validate changes under these different conditions.
- If you want to provide extra arguments to your debug jobs, we recommend the usage of hints, as they are adapted to each possible deployment (OCP installation, upgrade or workload deployment in an up-and-running cluster).
- Remember you have extra utilities like voting or avoiding the usage of `dci-queue` (if present) to really optimize your user experience.

We hope this blog post is useful for you to continue using `dci-check-change` when dealing with troubleshooting with some of the DCI agent changes. Do not hesitate to reach Telco CI team for whatever question you may have on this topic or to extend any topic covered here!

---
