Title: Running CNF Cert Suite certification with dci-openshift-app-agent
Date: 2022-05-06 10:00
Modified: 2023-05-18 10:00
Category: how-to
Tags: cnf-cert-suite, dci-openshift-app-agent, certification, partners
Slug: cnf-cert-suite-with-dci-openshift-app-agent
Author: Ramon Perez
Github: ramperher
Summary: The dci-openshift-app-agent enables Cloud-Native Applications and Operators in OpenShift using the Red Hat Distributed CI service. It also includes the possibility of running a set of certification tools over the workloads deployed by this agent, including the CNF Cert Suite, which allows CNF Developers to test their CNFs readiness for certification. This blog post summarizes the main points to have in mind when running CNF Cert Suite with the dci-openshift-app-agent, also providing an example.

[TOC]

## Introduction

The [dci-openshift-app-agent](https://github.com/redhat-cip/dci-openshift-app-agent) supports the execution of multiple test suites to validate containers, virtual functions, Helm charts, and operators. These suites are built as Ansible roles, helping the partners on getting prepared for the Red Hat certifications or actually running the certification process on the workloads deployed via DCI.

One of the test suites included on `dci-openshift-app-agent` is the CNF Cert Suite ([old](https://github.com/test-network-function/test-network-function) and [new](https://github.com/test-network-function/cnf-certification-test) repo), to simplify this set of testing tools. Thanks to this integration, it is possible to run the certification tools on a daily basis with the automation capabilities provided by DCI, validating that the tested workloads are ready for certification.

This blog post is useful for people getting familiar with  the usage of CNF Cert Suite using `dci-openshift-app-agent` as a tool to automate the whole process. We are going to focus mainly in 3 areas:

1. The code structure of the `dci-openshift-app-agent`, in terms of the integration of the CNF Cert Suite, will be reviewed, focusing on the [cnf-cert](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/roles/cnf-cert) role.
2. A practical example already defined on `dci-openshift-app-agent`, called [tnf_test_example](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/samples/tnf_test_example), will be presented, in order to see how to define a workload, based on containers and operators, that will be deployed on a running OpenShift cluster with DCI in order to be tested by CNF Cert Suite.
3. We will review the configuration needed to deploy the `tnf_test_example` and have it tested using the CNF Cert Suite all via the `dci-openshift-app-agent`.

The targeted audience for this blog post is people that are used to using CNF Cert Suite and `dci-openshift-app-agent`. For a more general overview, please see the [following presentation](https://drive.google.com/file/d/1k_UUOb4tAeWOR5YBYEDQI-531C5L-IVx/view) (based on CNF Cert Suite v3.2.0). Also, please refer to the documentation for tools like dci-openshift-app-agent, CNF Cert Suite, etc. to get more particular details about them.

Note that this blog post is based on CNF Cert Suite v4.2.4. Please check regularly the `cnf-cert` role documentation to see what's new for the latest CNF Cert Suite stable release, because the information you will see in this blog post may be different for different releases than v4.2.4.

## Code structure: the cnf-cert role

This Ansible role, included on `dci-openshift-app-agent`, encapsulates the logic for the CNF Cert Suite, based on the following assumptions regarding the certification suite:

- The configuration file used by the suite is reduced to the minimum, mainly using the auto-discovery capabilities to detect the resources under test.
- The suite is executed with a pre-built container, running the tests on DCI.

### Tasks executed

After deploying the workloads to be tested by CNF Cert Suite, in the DCI Red Hat `tests` phase, the main `cnf-cert` role is executed, following these steps sequentially on different stages:

- `pre-run` stage:
    - Save images related to CNF Cert Suite execution in a provided local registry if we are in a disconnected environment.
    - Create a temporary directory to clone `test-network-function` (TNF) repo.
    - Clone the correct TNF version, depending if we are testing a stable branch or a pull request from the CNF Cert Suite repository:
        - If testing a pull request, the container image is built, based on the code included in the pull request. A customized DCI component is also created based on the latest commit SHA hash in the pull request.
        - If testing a stable branch, download the container image from Quay.
- `tests` stage:
    - Generate the configuration file, based on a template, which takes care of filling the following fields (which are the ones currently supported on `dci-openshift-app-agent`):
        - `targetNameSpaces`, including the namespaces from which the certification suite has to look for auto-discovery labels.
        - `targetPodLabels` (for TNF versions until v4.2.2), defining the auto-discovery labels to be checked by the suite.
        - `podsUnderTestLabels` (for TNF versions from v4.2.3), defining the pod labels to be checked by the suite.
        - `operatorsUnderTestLabels` (for TNF versions from v4.2.3), defining the operator labels to be checked by the suite.
        - `targetCrdFilters`, including the CRDs under test.
        - `certifiedcontainerinfo`, including the container images to be tested by `affiliated-certification` test suite.
        - `acceptedKernelTaints`, including the tainted modules.
    - Set proper authentication files in case Preflight is run within TNF suite.
    - Run CNF Cert Suite with the correct parameters, being able to tune configurations like the location of the partner repository, the log level, the type of tests (intrusive or safe), etc.
        - Currently, labels are the preferred way of selecting/omitting the test suites, however legacy focus/skip arguments are still supported.
    - Copy the log files generated in the execution in a log folder, to be uploaded to DCI afterwards. Four main files are gathered after the execution:
        - The created configuration file.
        - The generated `claim.json` file by the CNF Cert Suite.
        - The XML file containing the test results in JUnit format.
        - A file called `dci-tnf-execution.log`, containing the standard output and standard error from the execution of the certification suite.
    - Check if the TNF execution finished correctly or not. In the second case, the DCI job fails.
- `post-run` stage:
    - The environment is cleaned in the following way:
        - Clean CNF Cert Suite resources if desired (e.g. default namespaces, daemonsets, etc. created during the execution).
        - Delete the temporary directory.
- `teardown` stage:
    - Remove PodSecurity-related labels if defined

### Variables to have in mind

The tasks executed on the `cnf-cert` role rely on variables that allow DCI users to provide the configuration needed by `dci-openshift-app-agent` to run the CNF Cert Suite properly.

The configuration does not include the deployment of the workloads (containers, operators, etc.), those steps are done in the `dci-openshift-app-agent` hooks. Then, these configurations for the CNF Cert Suite act on top of the  workloads deployed in the hooks.

The main variables to have in mind, whose default values are [these](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/group_vars/all) for some generic variables, and [these](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/roles/cnf-cert/defaults/main.yml) for some specific variables related to the certification suite, are the following:

- Generic:
    - `do_cnf_cert`: boolean variable that activates or not the execution of the CNF Cert Suite.
    - `dci_disconnected`: boolean variable that indicates if we are in a disconnected environment or not.
    - `dci_local_registry`: registry to be used on disconnected environments.
    - `partner_creds`: file including partner credentials to access private registries.
- Specific:
    - `test_network_function_version`: allows to indicate the CNF Cert Suite version to use, pointing to a specific release version or to the latest code released, referenced with `HEAD`. `HEAD` version (in the main branch) can be used, but is not guaranteed.
    - `tnf_labels`: list of executed/skipped test suites by the CNF Cert Suite, based on labelling system defined in CNF Cert Suite.
    - `tnf_suites` and `tnf_skip_suites`: they refer to the legacy way of defining the space-separated tests to execute and to skip.
    - `tnf_config`: complex variable used to fill the CNF Cert Suite configuration file, allowing to test multiple resources on different namespaces, and including a list of elements composed by:
        - `namespace`: namespace in which we want to autodiscover workloads.
        - `targetpodlabels`: list of auto-discovery labels to consider by the CNF Cert Suite for pod testing.
        - `targetoperatorlabels`: (for TNF versions from v4.2.3), defining the pod labels to be checked by the suite.
        - `target_crds`: (optional) list of CRDs to be tested.
        - `exclude_connectivity_regexp`<sup>1</sup> (optional): a regex to exclude containers from the connectivity test.
    - `accepted_kernel_taints`: allow-list for tainted modules. It must be composed of a list of elements called `module: "<module_name>"`.
    - `tnf_postrun_delete_resources`: boolean variable, to whether or not keep resources after the CNF Cert Suite execution. Used for debugging purposes.
    - `tnf_certified_container_info`: (optional) list of container images to be tested by `affiliated-certification` test suite.
    - `tnf_env_vars`: dictionary that allows to define environment variables used during CNF Cert Suite execution (such as `TNF_LOG_LEVEL`). It is empty by default and must be filled by the user. The cnf-cert role README includes an [example](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/roles/cnf-cert#example-of-tnf_env_vars-variable) about how to define this variable.

    <sup>1</sup> The logic for this requires an implementation. See examples in the following section.

## Example: the tnf_test_example use case

Before executing the CNF (Cloud-native network function) Cert Suite, it is needed to deploy the workloads and to label the pods and operators to test with the auto-discovery labels required by CNF Cert Suite. This can be done manually or programmatically. An example of this can be found in [tnf_test_example](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/samples/tnf_test_example).

This example deploys a couple of pods in two different namespaces, to be used with the CNF Test Suite in a multi-namespace scenario. It also allows the possibility of deploying an operator and a Helm chart to also test them with CNF Cert Suite.

The Deployment specification of this pod, obtained from [this repository](https://github.com/test-network-function/cnf-certification-test-partner/blob/main/test-target/local-pod-under-test.yaml), is a suitable one for passing all the test suites from the CNF Test Suite.

### Hooks implemented

Here are the steps on each hook for this example:

- `pre-run`:
    - Declare variables to be used in the hooks, related to the pod image, operator and Helm chart. These can be retrieved from `tnf_test_example` DCI component if provided in the settings/pipeline.
    - Clean resources if there are present in the cluster.
    - Install required RPM packages.
    - Mirror images for disconnected environments.
    - Prepare the operator and Helm chart (if defined) for disconnected environments.
    - Check StorageClass resources.
- `install`:
    - Deploy the testing resources. The full list of resources deployed can be checked in the `tnf_test_example` [README file](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/samples/tnf_test_example/README.md).
- `tests`:
    - Check found CalalogSource with `opcap`.
- `teardown`:
    - Delete the testing resources.

### Variables to have in mind

To deploy this example, it is needed to define the following variables in your pipelines:

- `dci_config_dir`: it must point to `"/var/lib/dci-openshift-app-agent/samples/tnf_test_example"`, place in which this example is defined. This variable allows to incorporate the hooks defined there to the execution of `dci-openshift-app-agent`.
- `components`: allows the selection of the `tnf_test_example` DCI component, which provides the pod image, the operator and the Helm chart to be tested.
    - If not provided, `tnf_app_image` must be provided, including the pod image.
- `tnf_config`: defining two elements, to deploy the workload in two different namespaces. In one of them, the operator to test is referenced. When showing an example of DCI job, the full definition of this variable will be provided.

## Running a DCI job

In this section, we will cover an example of execution of a DCI job launching `tnf_test_example` with CNF Cert Suite, also commenting some troubleshooting tips that you should have into account, extracted from [this presentation](https://drive.google.com/file/d/12Hyl5I_nm-1uF-ouCZgFVj9S7BPYleTF/view) about how to debug CNF Cert Suite with DCI (based on CNF Cert Suite v4.0.0).

### What do you need to configure?

There are two main parts to be configured:

- The settings to be provided to `dci-openshift-app-agent` (using pipelines or directly modifying the `settings.yml` file if using `dci-openshift-app-agent-ctl`). For this, mainly, you need to check the `cnf-cert` role variables that you may want to modify, especially focusing on `tnf_suites` variable.
- The correct labelling of the workloads (deployed manually or through hooks) to be tested by CNF Cert Suite (both pods and operators). In `tnf_test_example`, you have a good example where you can see how these labels are defined in the workloads under test.

### Job checklist

When running a job launching CNF Cert Suite, you need to confirm that:

- Job is green.
    - If the job is not green, then fix the errors displayed by DCI in order to make it green.
- Test results are displayed.
    - If they are not displayed (and probably, you will not see the log files in Files section, excepting `dci-tnf-execution.log`) - something has happened during tnf execution. Check `dci-tnf-execution.log` file and see what happened.
        - And what if `dci-tnf-execution.log` file is not provided? Then, something external to `dci-openshift-app-agent` configuration is happening; e.g. running `dci-openshift-app-agent-ctl` with a script that is wrongly using the variables to be provided to the agent. Check these kind of steps beforehand.
- In Files section, you should see the following logs:
    - `cnf-certification-tests_junit.xml`:
        - It contains the results of the tnf execution.
        - You’ll see the passed, skipped and failed tests like this (better to see them on DCI GUI rather than in the XML file).
        - On each test, regardless of the result, if you check for more details, you will see the output, error messages, etc. to troubleshoot afterwards.
    - `dci-tnf-execution.log`:
        - It provides the output of tnf execution, really useful to deeply troubleshoot the execution in case of problems.
        - We can tune the log level with `tnf_log_level` variable.
        - In the first lines, we can see general information like the tnf version used, the suites to be tested, etc., which is important to confirm that we are using the correct version and basic configuration.
        - The execution relies on a debug daemonset that performs the connection to the resources to be tested, so that you will see a lot of logs related to that.
    - `claim.json`:
        - This file includes context information related to the tnf execution, including:
            - Autodiscovered resources, with all the information that tnf has gathered from them.
            - Results of certification (similar to the JUnit file).
            - Configuration applied to run tnf.
            - Log messages from nodes.
            - etc.
    - `tnf_config.yml`:
        - Configuration file used for tnf execution.
        - It is built automatically based on tnf_config variable.

Up to this point, what happens if...

- ...tests are displayed but the workloads tested were not the expected ones? Then, read `tnf_config.yml` file and confirm you are testing what you want. If not, recheck `tnf_config` variable and change it accordingly.
- ...tests are displayed but we have failed unit tests? Follow the log messages and troubleshoot.
- ...the job is still running and it is stuck on CNF Cert Suite execution? In this case, we would not be able to see the log files generated during the execution, as they are created just after finishing the execution (e.g. `dci-tnf-execution.log` file is created by redirecting the output of CNF Cert Suite execution to that file). In this case, you will have to navigate to the source path where these files are created and then check them. This can be done in the following way:
    - Firstly, locate the temporary folder created in the job that contains the `cnf-certification-test` cloned repository. This can be found in [this task](https://www.distributed-ci.io/jobs/a4fbc0df-dc57-4d64-9f4e-cfe62886eb91/jobStates?sort=date&task=9e6a87d2-b5c7-4e1d-bf7c-4c60629a1a91) from your `dci-openshift-app-agent` job. In this case, the folder is `/tmp/ansible.q7ofnrge`, and it is saved in the jumphost.
    - Move to that folder and access to `cnf-certification-test` repo. In this example, this would be: `$ cd /tmp/ansible.q7ofnrge/cnf-certification-test`.
    - Under that path, you should find `dci-tnf-execution.log` file, which is updated during the CNF Cert execution (so list it with `$ tail dci-tnf-execution.log`), and also the `tnf_config.yml` file.
    - Remember that this temporary folder is deleted when the job finishes, but after that, the files are present in the Files section of the job, as explained before.

### Example of a correct DCI job running tnf_test_example with CNF Cert Suite

In order to execute an example of a DCI job, managed by `dci-openshift-app-agent`, making use of the `tnf_test_example` and running CNF Cert Suite, just follow these steps:

1. Confirm you have a cluster up and running:

        $ export KUBECONFIG=/var/lib/dci-openshift-app-agent/kubeconfig
        $ oc version
        Client Version: 4.11.0-0.nightly-2022-04-24-135651
        Kustomize Version: v4.5.4
        Server Version: 4.11.0-0.nightly-2022-04-24-135651
        Kubernetes Version: v1.23.3+d464c70

        $ oc get nodes
        NAME       STATUS   ROLES           AGE   VERSION
        master-0   Ready    master,worker   12h   v1.23.3+54654d2
        master-1   Ready    master,worker   12h   v1.23.3+54654d2
        master-2   Ready    master,worker   12h   v1.23.3+54654d2

1. Create a `settings.yml` file and place it in `/etc/dci-openshift-app-agent/settings.yml`, with the following content:

        $ cat /etc/dci-openshift-app-agent/settings.yml
        ---
        dci_tags: ["debug"]
        dci_config_dir: "/var/lib/dci-openshift-app-agent/samples/tnf_test_example"
        dci_components_by_query: ["type:tnf_test_example"]
        do_cnf_cert: true
        tnf_config:
            -   namespace: "test-cnf"
                targetpodlabels: [environment=test]
                targetoperatorlabels: [operators.coreos.com/mongodb-enterprise.test-cnf=]
                target_crds: ["crdexamples.test-network-function.com"]
                exclude_connectivity_regexp: ""
            -   namespace: "production-cnf"
                targetpodlabels: [environment=production]
                targetoperatorlabels: []
                target_crds: ["crdexamples.test-network-function.com"]
                exclude_connectivity_regexp: ""
        ...

> Note that you can also use pipelines and `dci-pipeline` instead of using settings and the `ctl` command, for a better user experience. Please check [the DCI pipeline blog post](automate-dci-components.html) for more information.

1. Run `dci-openshift-app-agent`:

        $ dci-openshift-app-agent-ctl -s -- -v

1. Check the status of the DCI job until it finishes.
1. Check the results.

Finally, you should have a DCI job like [this one (based on TNF v4.1.1)](https://www.distributed-ci.io/jobs/04d8713d-9480-4741-8f10-deabc13d746c/jobStates?sort=date), which was done in a connected environment. There, you can observe the results obtained. Mainly, you have to take care of the following:

- In the Tests section, you will see the results of the CNF Cert Suite execution, in JUnit format, clearly viewing the tests that have passed, failed, or been skipped.
- In the Files section, you can see the logs generated during the execution, including `dci-tnf-execution.log` or `claim.json` files, useful for troubleshooting purposes.

Note that, for this example, we have not modified the default values of variables like `test_network_function_version` or `tnf_labels`, so that we are using the latest stable version of CNF Cert Suite and running all the tests defined.

## Conclusions

This blog post has summarized the details to keep in mind when automating the CNF Cert Suite through the `dci-openshift-app-agent` on top of an OpenShift cluster.

For this purpose, we provide a full definition of the `cnf-cert` role with the help of a workload composed by a deployment created in two different namespaces and an operator running in one of the testing namespaces.

Finally, the work finishes with an example of a DCI job that executes the certification over the workload, showing the main aspects to consider when checking the logs and the job status.

---
