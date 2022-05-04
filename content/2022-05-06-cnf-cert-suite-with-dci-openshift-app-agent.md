Title: Running CNF Cert Suite certification with dci-openshift-app-agent
Date: 2022-05-06 10:00
Category: how-to
Tags: cnf-cert-suite, dci-openshift-app-agent, certification, partners
Slug: cnf-cert-suite-with-dci-openshift-app-agent
Authors: Ramon Perez
Summary: The dci-openshift-app-agent enables Cloud-Native Applications and Operators in OpenShift using Red Hat Distributed CI service. It also includes the possibility of running a set of certification tools over the workloads deployed by this agent, including the CNF Cert Suite, which allows CNF Developers to test their CNFs readiness for certification. This blog post summarizes the main points to have in mind when running CNF Cert Suite with the dci-openshift-app-agent, also providing an example.

## Introduction

The [dci-openshift-app-agent](https://github.com/redhat-cip/dci-openshift-app-agent) supports the execution of multiple test suites to validate containers, virtual functions, Helm charts, and operators. These suites are built as Ansible roles, helping the partners on getting prepared for the Red Hat certifications or actually running the certification process on the workloads deployed via DCI.

One of the test suites included on `dci-openshift-app-agent` is the CNF Cert Suite ([old](https://github.com/test-network-function/test-network-function) and [new](https://github.com/test-network-function/cnf-certification-test) repo), with the purpose of making the process of executing this set of testing tools easier. Thanks to this integration, it is possible to run the certification tools on a daily basis with the automation capabilities provided by DCI, validating that the tested workloads are ready for certification.

This blog post will be useful for people getting introduced to the usage of CNF Cert Suite, using `dci-openshift-app-agent` as a tool to automate the whole process. It is structured in the following way:

- Firstly, the code structure of the `dci-openshift-app-agent`, in terms of the integration of the CNF Cert Suite, will be reviewed, focusing on the [cnf-cert](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/roles/cnf-cert) role.
- Then, a practical example already defined on `dci-openshift-app-agent`, called [tnf_test_example](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/samples/tnf_test_example), will be presented, in order to see how to define a workload, based on containers and operators, that will be deployed on a running OpenShift cluster with DCI in order to be tested by CNF Cert Suite.
- Finally, the configuration needed to deploy `tnf_test_example` with `dci-openshift-app-agent`, being tested with CNF Cert Suite, will be provided, also linking to a DCI job in which it is shown the results of the tests’ execution.

Note that this blog post will just be focused on the topics aforementioned. Please refer to the documentation of each tool mentioned (`dci-openshift-app-agent`, CNF Cert Suite, etc.) to review more particular details about them.

## Code structure: the cnf-cert role

This Ansible role, included on `dci-openshift-app-agent`, encapsulates the logic for the CNF Cert Suite, based on the following assumptions regarding the certification suite:

- The configuration file used by the suite is reduced to the minimum, mainly using the autodiscovery capabilities to detect the resources under test.
- The suite is executed with a prebuild container, running the tests on DCI.

### Tasks executed

After deploying the workloads to be tested by CNF Cert Suite, in the DCI Red Hat `tests` phase, the main `cnf-cert` role is executed, following these steps sequentially:

- Save images related to CNF Cert Suite execution in local registry if we are in a disconnected environment. A reference to the local registry must be provided.
- Create a temporary directory to clone `test-network-function` (`tnf`) repo on it.
- Clone the correct `tnf` version, depending if we are testing a stable branch or a pull request from the CNF Cert Suite repository:
	- If testing a pull request, the container image is built, based on the code included in the pull request. A customized DCI component, based on the latest commit SHA hash in the pull request, is also created.
	- If testing a stable branch, the container image is directly downloaded from Quay.
- Generate the configuration file, based on a template, which takes care of filling the following fields:
	- `targetNameSpaces`, including the namespaces from which the certification suite has to look for autodiscovery labels.
	- `targetPodLabels`, defining the autodiscovery labels to be checked by the suite.
	- `acceptedKernelTaints`, including the modules which may have taints and that may cause the tainted kernel test case to fail in some of the workloads, so that they are omitted in order to make the test case to pass.
- Run CNF Cert Suite with the correct parameters, being able to tune configurations like the location of the partner repository, the log level, if intrusive tests have to be performed or not, etc.
- Copy the log files generated in the execution in a log folder, to be uploaded to DCI afterwards. Four main files are gathered after the execution:
	- The configuration file created.
	- The `claim.json` file generated by the CNF Cert Suite.
	- The XML file that contains the test results in JUnit format.
	- A file called `execution.log`, containing the standard and error outputs from the execution of the certification suite.

Then, after finishing the tests, in the DCI `post-run` phase, the environment is cleaned in the following way:

- Clean CNF Cert Suite resources if desired (e.g. default namespaces, daemon sets, etc. created during the execution).
- Delete temporary directory.

### Variables to have in mind

The tasks executed on the `cnf-cert` role rely on a set of variables that allow DCI users to provide the configuration needed by `dci-openshift-app-agent` in order to properly execute the CNF Cert Suite.

This does not include the deployment of the workloads (containers, operators, etc.), which must be done in the `dci-openshift-app-agent` hooks. Then, the configuration variables for the CNF Cert Suite must be set in order to make reference to the workloads deployed in the hooks.

The main variables to have in mind, whose default values are [these](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/group_vars/all) for some generic variables, and [these](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/roles/cnf-cert/defaults/main.yml) for some specific variables related to the certification suite, are the following:

- Generic:
	- `do_cnf_cert`: boolean variable that activates or not the execution of the CNF Cert Suite.
	- `dci_disconnected`: boolean variable that indicates if we are in a disconnected environment or not.
	- `provisionhost_registry`: registry to be used on disconnected environments.
	- `partner_creds`: file including partner credentials to access private registries.
	- `sync_cnf_cert_and_preflight`: boolean variable that activates or not the gathering of the data related to operators tested by CNF Cert Suite, in order to also test them on preflight (also with the `dci-openshift-app-agent`). More information regarding this functionality can be found in its specific role.
- Specific:
	- `test_network_function_version`: allows to indicate the CNF Cert Suite version to be used, pointing to a specific release version or to the latest code released, referenced with `HEAD`. `HEAD` version (in the main branch) does not guarantee a complete compatibility with the latest unstable changes.
	- `tnf_suites`: list of test suites to be executed by the CNF Cert Suite, separated by spaces.
	- `tnf_config`: complex variable that is used to fill the CNF Cert Suite configuration file, allowing to test multiple resources on different namespaces, and including a list of elements that are composed by:
		- `namespace`: namespace in which we want to autodiscover workloads.
		- `targetpodlabels`: list of autodiscovery labels to be considered by the CNF Cert Suite for pod testing.
		- `operators_regexp` (optional\*): a regexp to select operators to be tested by the CNF Cert Suite.
		- `exclude_connectivity_regexp` (optional\*): a regexp to exclude containers from the connectivity test.
	- `accepted_kernel_taints`: allow-list for tainted modules. It must be composed of a list of elements called `module: "<module_name>"`.
	- `tnf_non_intrusive_only`: skip intrusive tests which may disrupt cluster operations.
	- `tnf_run_cfd_test`: the test suites from [openshift-kni/cnf-feature-deploy](https://github.com/openshift-kni/cnf-features-deploy) will be run prior to the actual CNF certification test execution and the results are incorporated in the same claim.
	- `tnf_log_level`: log level used to run the CNF Cert Suite.
	- `tnf_postrun_delete_resources`: boolean variable that controls if the deployed resources are kept after the CNF Cert Suite execution for debugging purposes.

\*Note that the logic to use these two variables, and also to create and delete the corresponding autodiscovery labels, need to be implemented. Examples of this can be seen in the following section.

## Example: the tnf_test_example use case

Before executing the CNF (Cloud-native network function) Cert Suite, it is needed to deploy the workloads and to label the pods and operators to test with the autodiscovery labels required by CNF Cert Suite. This can be done manually or programmatically. An example of this can be found in [tnf_test_example](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/samples/tnf_test_example).

This example deploys a couple of pods in two different namespaces, to be used with the CNF Test Suite in a multi-namespace scenario.

The Deployment specification of this pod, obtained from [this repository](https://github.com/test-network-function/cnf-certification-test-partner/blob/main/local-test-infra/local-pod-under-test.yaml), is a suitable one for passing all the test suites from the CNF Test Suite.

It also deploys an operator in one of the namespaces, based on [simple-demo-operator-bundle](https://quay.io/repository/opdev/simple-demo-operator-bundle), in order to execute CNF Cert Suite and Preflight tests over this operator.

### Hooks implemented

The following hooks have been defined in order to properly define all the steps to handle the lifecycle of this example, with the following steps executed sequentially:

- `pre-run`:
	- Install required RPM packages.
	- Prepare the operator for disconnected environments.
- `install`:
	- Create namespaces and deploy test pods on each namespace if not done before. The pods are created with a Deployment based on this template, in which, for example, it is possible to create the correct `skip_connectivity_tests` label if the `exclude_connectivity_regexp` variable is properly defined in the `tnf_config` variable already commented.
	- Deploy `simple-demo-operator` in one of the two namespaces under test.
	- Tag `simple-demo-operator` CSV with the correct autodiscovery label if properly defined in the `operators_regexp` variable defined in the `tnf_config` variable.
- `teardown`:
	- Delete the namespaces under test if not done before (so, the workloads are automatically removed).
	- Delete the resources related to `simple-demo-operator`.

### Variables to have in mind

To deploy this example, it is needed to define the following variables: 

- `dci_config_dir`: it must point to `"/var/lib/dci-openshift-app-agent/samples/tnf_test_example"`, place in which this example is defined. This variable allows to incorporate the hooks defined there to the execution of `dci-openshift-app-agent`.
- `dci_openshift_app_image`: it references the image to be used by the workloads. In this case, it must point to `“quay.io/testnetworkfunction/cnf-test-partner:latest”`.
- `dci_openshift_app_ns`: base namespace to deploy workloads. It must be set to `“test-cnf"`.
- `tnf_config`: defining two elements, to deploy the workload in two different namespaces. In one of them, `simple-demo-operator` is referenced. When showing an example of DCI job, the full definition of this variable will be provided.
- `tnf_operator_to_install`: references the information related to `simple-demo-operator`, including:
	- `operator_name`: it would be `“simple-demo-operator”`.
	- `operator_version`: referencing the correct version of the operator. In the tests, it is used `“v0.0.5”`.
	- `operator_bundle`: including the bundle for the operator. In our case, it would be `"quay.io/telcoci/simple-demo-operator-bundle@sha256:8a4b6e4a430a520b438d91c5ecb815de3c49b204488dafd910d2a450ede1692a"`.

## Example of DCI job running tnf_test_example with CNF Cert Suite

In order to execute an example of a DCI job, managed by `dci-openshift-app-agent`, making use of the `tnf_test_example` and running CNF Cert Suite, just follow these steps:

1. Confirm you have a cluster up and running:

```Shell
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
```

2. Create a `settings.yml` file and place it in `/etc/dci-openshift-app-agent/settings.yml`, with the following content:

```Shell
$ cat /etc/dci-openshift-app-agent/settings.yml
---

# dci-openshift-app-agent settings
# defaults from /usr/share/dci-openshift-app-agent/group_vars/all

# Remove "debug" when your jobs are working to get them in the
# statistics:
dci_tags: ["debug", "blog-post", "dci-openshift-app-agent", "tnf_v3.3.3"]
dci_config_dir: "/var/lib/dci-openshift-app-agent/samples/tnf_test_example"
dci_openshift_app_image: quay.io/testnetworkfunction/cnf-test-partner:latest
dci_openshift_app_ns: "test-cnf"
do_cnf_cert: true
test_network_function_version: "v3.3.3"
tnf_suites: "access-control networking lifecycle observability platform-alteration operator"
tnf_config:
  - namespace: "test-cnf"
    targetpodlabels: [environment=test]
    operators_regexp: "simple-demo-operator"
    exclude_connectivity_regexp: ""
  - namespace: "production-cnf"
    targetpodlabels: [environment=production]
    operators_regexp: ""
    exclude_connectivity_regexp: ""
tnf_operator_to_install:
  operator_name: simple-demo-operator
  operator_version: "v0.0.5"
  operator_bundle: "quay.io/telcoci/simple-demo-operator-bundle@sha256:8a4b6e4a430a520b438d91c5ecb815de3c49b204488dafd910d2a450ede1692a"
...
```

3. Run `dci-openshift-app-agent`:

```Shell
$ dci-openshift-app-agent-ctl -s -- -v
```

4. Check the status of the DCI job until it finishes.
5. Check the results.

Finally, you should have a DCI job like [this one](https://www.distributed-ci.io/jobs/185e2c6e-549b-4dd7-bbf0-8b149ee45737/jobStates), which was done in a connected environment. There, you can observe the results obtained. Mainly, you have to take care of the following:

- In the Tests section, you will see the results of the CNF Cert Suite execution, in JUnit format, clearly viewing the tests that have passed, failed or been skipped.
- In Files section, you can see the logs generated during the execution, including `execution.log` or `claim.json` files, useful for troubleshooting purposes.

## Conclusions

This blog post has summarized the information to have in mind when running CNF Cert Suite on top of an already running OpenShift cluster, using `dci-openshift-app-agent` in order to automate the whole process.

For this purpose, a full definition of the `cnf-cert` role has been provided, also showing an example of a workload composed by a deployment (with two pods), which is created in two different namespaces, and an operator running in one of the testing namespaces.

Then, the work finishes with an example of a DCI job which executes the certification over that workload, showing the main aspects to have in mind when checking the logs and the status of a given DCI job.
