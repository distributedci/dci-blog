Title: Running Red Hat Best Practices for Kubernetes test suite with dci-openshift-app-agent
Date: 2022-05-06 10:00
Modified: 2024-08-14 10:00
Category: how-to
Tags: cnf-cert-suite, certsuite, k8s_best_practices_certsuite, dci-openshift-app-agent, certification, partners
Slug: cnf-cert-suite-with-dci-openshift-app-agent
Author: Ramon Perez
Github: ramperher
Summary: The dci-openshift-app-agent enables Cloud-Native Applications and Operators in OpenShift using the Red Hat Distributed CI service. It also includes the possibility of running a set of certification tools over the workloads deployed by this agent, including the Red Hat Best Practices for Kubernetes test suite (former CNF Cert Suite), which allows CNF Developers to test their CNFs readiness for certification. This blog post summarizes the main points to have in mind when running the certsuite with the dci-openshift-app-agent, also providing an example.

[TOC]

## Introduction

The [dci-openshift-app-agent](https://github.com/redhat-cip/dci-openshift-app-agent) supports the execution of multiple test suites to validate containers, virtual functions, Helm charts, and operators. These suites are built as Ansible roles, helping the partners on getting prepared for the Red Hat certifications or actually running the certification process on the workloads deployed via DCI.

One of the test suites included on `dci-openshift-app-agent` is the [Red Hat Best Practices for Kubernetes test suite](https://github.com/redhat-best-practices-for-k8s/certsuite) (also called certsuite), to simplify this set of testing tools. Thanks to this integration, it is possible to run the certification tools on a daily basis with the automation capabilities provided by DCI, validating that the tested workloads are ready for certification.

This blog post is useful for people getting familiar with  the usage of the certsuite using `dci-openshift-app-agent` as a tool to automate the whole process. We are going to focus mainly in 3 areas:

1. The code structure of the `dci-openshift-app-agent`, in terms of the integration of the certsuite, will be reviewed, focusing on the [k8s_best_practices_certsuite](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/k8s_best_practices_certsuite) role.
2. A practical example already defined on `dci-openshift-app-agent`, called [tnf_test_example](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/samples/tnf_test_example), will be presented, in order to see how to define a workload, based on containers and operators, that will be deployed on a running OpenShift cluster with DCI in order to be tested by the certsuite.
3. We will review the configuration needed to deploy the `tnf_test_example` and have it tested using the certsuite all via the `dci-openshift-app-agent`.

The targeted audience for this blog post is people that are used to using the certsuite and `dci-openshift-app-agent`. For a more general overview, please see the [following presentation](https://drive.google.com/file/d/1k_UUOb4tAeWOR5YBYEDQI-531C5L-IVx/view) (note it is based on former CNF Cert Suite, aka tnf, v3.2.0, so variables are different, but the philosophy is mostly the same). Also, please refer to the documentation for tools like dci-openshift-app-agent, the certsuite, etc. to get more particular details about them.

Note that this blog post is based on certsuite v5.2.2. Please check regularly the `k8s_best_practices_certsuite` role documentation to see what's new for the latest certsuite stable release, because the information you will see in this blog post may be different for different releases than v5.2.2.

## Code structure: the k8s_best_practices_certsuite role

This Ansible role, included on `dci-openshift-app-agent`, encapsulates the logic for the certsuite, based on the following assumptions regarding the certification suite:

- The configuration file used by the suite is reduced to the minimum, mainly using the auto-discovery capabilities to detect the resources under test.
- The suite is executed with a pre-built container, running the tests on DCI.

### Tasks executed

After deploying the workloads to be tested by the certsuite, in the DCI Red Hat `tests` phase, the main `k8s_best_practices_certsuite` role is executed if `do_certsuite` flag is set to `true`, following these steps sequentially on different stages:

- `pre-run` stage:
    - Detect if we are testing a pull request from certsuite repository or a stable branch, to select the proper certsuite container image.
        - If testing a pull request, the container image is built, based on the code included in the pull request. A customized DCI component is also created based on the latest commit SHA hash in the pull request.
        - If testing a stable branch, the container image is downloaded from Quay and the `certsuite` repo is cloned in a temporary folder.
    - Save images related to the certsuite execution in a provided local registry if we are in a disconnected environment.
- `tests` stage:
    - Generate the configuration file, based on a template, which takes care of filling the following fields (which are the ones currently supported on `k8s_best_practices_certsuite` role):
        - `targetNameSpaces`, including the namespaces from which the certification suite has to look for auto-discovery labels.
        - `podsUnderTestLabels`, defining the pod labels to be checked by the suite.
        - `operatorsUnderTestLabels`, defining the operator labels to be checked by the suite.
        - `targetCrdFilters`, including the CRDs under test.
        - `acceptedKernelTaints`, including the tainted modules.
        - `servicesignorelist`, including services to be ignored on certsuite tests.
    - Set proper authentication files in case Preflight is run within certsuite.
    - Run the certsuite with the correct parameters, being able to tune configurations like the location of the partner repository, the log level, the type of tests (intrusive or safe), etc.
    - Copy the log files generated in the execution in a log folder, to be uploaded to DCI afterwards. Four main files are gathered after the execution:
        - The generated configuration file.
        - The `claim.json` file provided by the certsuite as result execution.
        - The XML file containing the test results in JUnit format.
        - Log files containing the standard output and standard error from the execution of the certification suite.
        - A tar.gz file containing the summary of the execution, including the HTML web page with the report of the execution, also embedding the feedback provided by the partner if it exists.
    - If we are testing a stable branch, it confirms if what we have executed corresponds to what we have cloned from `certsuite` repository. This is useful to determine if, when testing HEAD branch, the latest changes are really present in Quay.
- `teardown` stage:
    - The environment is cleaned in the following way:
        - Clean the certsuite resources if desired (e.g. default namespaces, daemonsets, etc. created during the execution).
        - Delete the temporary directory.

### Variables to have in mind

The tasks executed on the `k8s_best_practices_certsuite` role rely on variables that allow DCI users to provide the configuration needed by `dci-openshift-app-agent` to run the certsuite properly.

The configuration does not include the deployment of the workloads (containers, operators, etc.), those steps are done in the `dci-openshift-app-agent` hooks. Then, these configurations for the certsuite act on top of the  workloads deployed in the hooks.

The main variables to have in mind, whose default values are [these](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/group_vars/all) for some generic variables, and [these](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/k8s_best_practices_certsuite/defaults/main.yml) for some specific variables related to the certification suite, are the following:

- Generic:
    - `do_certsuite`: boolean variable that activates or not the execution of the certsuite.

- Specific:
    - `kbpc_version`: allows to indicate the certsuite version to use, pointing to a specific release version or to the latest code released, referenced with `HEAD`. `HEAD` version (in the main branch) can be used, but is not guaranteed.
    - `kbpc_test_labels`: list of executed/skipped test suites by the certsuite, based on labelling system defined in the certsuite.
    - `kbpc_test_config`: complex variable used to fill the certsuite configuration file, allowing to test multiple resources on different namespaces, and including a list of elements composed by:
        - `namespace`: namespace in which we want to autodiscover workloads.
        - `targetpodlabels`: list of auto-discovery labels to consider by the certsuite for pod testing.
        - `targetoperatorlabels`: defines the operator labels to be checked by the suite.
        - `target_crds`: (optional) list of CRDs to be tested.
        - `exclude_connectivity_regexp`<sup>1</sup> (optional): a regex to exclude containers from the connectivity test.
    - `kbpc_accepted_kernel_taints`: allow-list for tainted modules. It must be composed of a list of elements called `module: "<module_name>"`.
    - `kbpc_services_ignore_list`: list of services to be ignored when running the certsuite.
    - `kbpc_allow_preflight_insecure`: allow insecure connections to registries when running Preflight.
    - `kbpc_non_intrusive_only`: controls whether intrusive tests are launched or not.
    - `kbpc_log_level`: log level applied during certsuite execution.
    - `kbpc_postrun_delete_resources`: boolean variable, to whether or not keep resources after the certsuite execution. Used for debugging purposes.
    - `kbpc_feedback`: allows you to include the feedback for the tests that require exceptions in the certification process.
    - `kbpc_kubeconfig`: path to your cluster's kubeconfig.
    - `kbpc_log_path`: path to save execution logs.
    - `kbpc_pullsecret`: pullsecret to be used on disconnected environments, or when running Preflight if required.
    - `kbpc_registry`: registry to be used on disconnected environments.
    - `kbpc_partner_creds`: file including partner credentials to access private registries.

    <sup>1</sup> The logic for this requires an implementation. See examples in the following section.

## Example: the tnf_test_example use case

Before executing the certsuite, it is needed to deploy the workloads and to label the pods and operators to test with the auto-discovery labels required by the certsuite. This can be done manually or programmatically. An example of this can be found in [tnf_test_example](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/samples/tnf_test_example).

This example deploys a couple of pods in two different namespaces, to be used with the CNF Test Suite in a multi-namespace scenario. It also allows the possibility of deploying an operator and a Helm chart to also test them with the certsuite.

The Deployment specification of this pod, obtained from [this repository](https://github.com/redhat-best-practices-for-k8s/certsuite-sample-workload/blob/main/test-target/local-pod-under-test.yaml), is a suitable one for passing all the test suites from the certsuite.

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
- `kbpc_test_config`: defining two elements, to deploy the workload in two different namespaces. In one of them, the operator to test is referenced. When showing an example of DCI job, the full definition of this variable will be provided.

## Running a DCI job

In this section, we will cover an example of execution of a DCI job launching `tnf_test_example` with the certsuite, also commenting some troubleshooting tips that you should have into account, extracted from [this presentation](https://drive.google.com/file/d/12Hyl5I_nm-1uF-ouCZgFVj9S7BPYleTF/view) about how to debug the certsuite with DCI (based on former CNF Cert Suite v4.0.0, but the logic behind this is mostly the same).

### What do you need to configure?

There are two main parts to be configured:

- The pipeline to launch `dci-openshift-app-agent`. For this, mainly, you need to check the `k8s_best_practices_certsuite` role variables that you may want to modify.
- The correct labelling of the workloads (deployed manually or through hooks) to be tested by the certsuite (both pods and operators). In `tnf_test_example`, you have a good example where you can see how these labels are defined in the workloads under test.

### Job checklist

When running a job launching the certsuite, you need to confirm that:

- Job is green.
    - If the job is not green, then fix the errors displayed by DCI in order to make it green.
    - Even though your job is green, there may be certsuite tests that are failing. You should review them to confirm the execution complies with your current workload status.
- Test results are displayed.
    - If they are not displayed (and probably, you will not see the log files in Files section, excepting `certsuite.log` and `certsuite-stdout.log`) - something has happened during the certsuite execution. Check these log files and see what happened.
- In Files section, you should see the following logs:
    - `certsuites_junit.xml`:
        - It contains the results of the certsuite execution.
        - You’ll see the passed, skipped and failed tests like this (better to see them on DCI GUI rather than in the XML file).
        - On each test, regardless of the result, if you check for more details, you will see the output, error messages, etc. to troubleshoot afterwards.
    - `certsuite.log` and `certsuite-stdout.log`:
        - They provide the output of certsuite execution, really useful to deeply troubleshoot the execution in case of problems.
        - We can tune the log level with `kbpc_log_level` variable.
        - In the first lines, we can see general information like the certsuite version used, the suites to be tested, etc., which is important to confirm that we are using the correct version and basic configuration.
        - The execution relies on a debug daemonset that performs the connection to the resources to be tested, so that you will see a lot of logs related to that.
    - `claim.json`:
        - This file includes context information related to the certsuite execution, including:
            - Autodiscovered resources, with all the information that certsuite has gathered from them.
            - Results of certification (similar to the JUnit file).
            - Configuration applied to run certsuite.
            - Log messages from nodes.
            - etc.
    - `tnf_config.yml`:
        - Configuration file used for certsuite execution.
        - It is built automatically based on tnf_config variable.
    - `<timestamp>-cnf-test-results.tar.gz`:
        - Report of certsuite execution, including the HTML report with the feedback defined by the partner if provided.

Up to this point, what happens if...

- ...tests are displayed but the workloads tested were not the expected ones? Then, read `tnf_config.yml` file and confirm you are testing what you want. If not, recheck `kbpc_test_config` variable and change it accordingly.
- ...tests are displayed but we have failed unit tests? Follow the log messages and troubleshoot.
- ...the job is still running and it is stuck on the certsuite execution? In this case, we would not be able to see the log files generated during the execution, as they are created just after finishing the execution (e.g. `certsuite-stdout.log` file is created by redirecting the output of the certsuite execution to that file). In this case, you will have to navigate to the source path where these files are created and then check them. This can be done in the following way:
    - Firstly, locate the temporary folder created in the job that contains the `certsuite` cloned repository. This can be found in [this task](https://www.distributed-ci.io/jobs/409a51bc-54e2-43d5-b2d3-30100a7ef7d4/jobStates?sort=date&task=fb97a616-8c4b-4d7a-8b76-8a0cddc1823f) from your `dci-openshift-app-agent` job. In this case, the folder is `/tmp/ansible.gvrzgvoa`, and it is saved in the jumphost. The output of the task should be something like this:

                TASK [redhatci.ocp.k8s_best_practices_certsuite : Create temporary directory for certsuite repository]
                task path: /usr/share/ansible/collections/ansible_collections/redhatci/ocp/roles/k8s_best_practices_certsuite/tasks/pre-run.yml:114
                changed: [jumphost] => {"changed": true, "gid": 1004, "group": "dciteam", "mode": "0700", "owner": "dciteam", "path": "/tmp/ansible.gvrzgvoa", "secontext": "unconfined_u:object_r:user_tmp_t:s0", "size": 6, "state": "directory", "uid": 1004}

    - Move to that folder and access to `result_files`. In this example, this would be: `$ cd /tmp/ansible.gvrzgvoa/result_files`.
    - Under that path, you should find `certsuite-stdout.log` file, which is updated during the CNF Cert execution (so list it with `$ tail certsuite-stdout.log`).
    - If the certsuite execution has finished, then the log files are copied in [this folder](https://www.distributed-ci.io/jobs/409a51bc-54e2-43d5-b2d3-30100a7ef7d4/jobStates?sort=date&task=f70bf04c-3677-4f8e-b8c8-64946610ce93), also temporary. In this job, it is `/tmp/dci_logs.hcw3_nj0`, and you can directly see the log files under that folder. The output of the task is:

                TASK [Job logs path]
                task path: /usr/share/dci-openshift-app-agent/plays/log-dir.yml:8
                ok: [jumphost] => {
                    "msg": "/tmp/dci_logs.hcw3_nj0"
                }

    - Remember that this temporary folder is deleted when the job finishes, but after that, the files are present in the Files section of the job, as explained before.

### Example of a correct DCI job running tnf_test_example with the certsuite

In order to execute an example of a DCI job, managed by `dci-openshift-app-agent`, making use of the `tnf_test_example` and running the certsuite, just follow these steps:

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

1. Run a DCI job using `dci-pipeline`, with the following pipeline (note this is an example, you should adapt it to your environment):

        ---
        -   name: tnf-test-cnf
            stage: cnf
            prev_stages: [ocp-upgrade, ocp]
            ansible_playbook: /usr/share/dci-openshift-app-agent/dci-openshift-app-agent.yml
            ansible_cfg: /var/lib/dci/pipelines/ansible.cfg
            ansible_inventory: /path/to/your/inventory
            dci_credentials: /etc/dci-openshift-app-agent/dci_credentials.yml
            configuration: "@QUEUE"
            ansible_extravars:
                dci_teardown_on_success: true
                dci_teardown_on_failure: true
                dci_cache_dir: /var/lib/dci-pipeline
                dci_config_dir: /var/lib/dci-openshift-app-agent/samples/tnf_test_example
                do_certsuite: true
                kbpc_test_labels: "common,telco,extended"
                kbpc_test_config:
                    -   namespace: "test-cnf"
                        targetpodlabels: [environment=test]
                        targetoperatorlabels: [operators.coreos.com/mongodb-enterprise.test-cnf=]
                        target_crds:
                            -   nameSuffix: "crdexamples.redhat-best-practices-for-k8s.com"
                                scalable: false
                        exclude_connectivity_regexp: ""
                    -   namespace: "production-cnf"
                        targetpodlabels: [environment=production]
                        targetoperatorlabels: []
                        target_crds:
                            -   nameSuffix: "crdexamples.redhat-best-practices-for-k8s.com"
                                scalable: false
                        exclude_connectivity_regexp: ""
                kbpc_non_intrusive_only: false
                kbpc_log_level: debug
                kbpc_accepted_kernel_taints:
                    -    module: "tls"
                kbpc_services_ignore_list:
                    -   operator-webhook
                    -   tnf-test-example-samplechart
            use_previous_topic: true
            components:
                -   tnf_test_example
            inputs:
                kubeconfig: kubeconfig_path
            success_tag: tnf-test-cnf-ok

> Please check [the DCI pipeline blog post](automate-dci-components.html) for more information regarding pipelines.

1. Check the status of the DCI job until it finishes.
1. Check the results.

Finally, you should have a DCI job like [this one (based on certsuite v5.2.2)](https://www.distributed-ci.io/jobs/409a51bc-54e2-43d5-b2d3-30100a7ef7d4/jobStates), which was executed in a disconnected environment. There, you can observe the results obtained. Mainly, you have to take care of the following:

- In the Tests section, you will see the results of the certsuite execution, in JUnit format, clearly viewing the tests that have passed, failed, or been skipped.
- In the Files section, you can see the logs generated during the execution, including `certsuite[-stdout].log` or `claim.json` files, useful for troubleshooting purposes.

## Conclusions

This blog post has summarized the details to keep in mind when automating the certsuite through the `dci-openshift-app-agent` on top of an OpenShift cluster.

For this purpose, we provide a full definition of the `k8s_best_practices_certsuite` role with the help of a workload composed by a deployment created in two different namespaces and an operator running in one of the testing namespaces.

Finally, the work finishes with an example of a DCI job that executes the certification over the workload, showing the main aspects to consider when checking the logs and the job status.

---
