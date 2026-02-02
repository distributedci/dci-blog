Title: Running PTP Tests on OpenShift with ansible-collection-redhatci-ocp
Date: 2026-01-28
Category: Openshift
Tags: ansible, collection, OCP, automation, PTP, testing, CNF
Slug: running-ptp-tests-openshift-collection
Author: Pierre Blanc
Github: pierreblanc
Summary: This blog post demonstrates how to use the ansible-collection-redhatci-ocp collection to run PTP (Precision Time Protocol) tests on an already deployed OpenShift cluster using a standalone Ansible playbook. This is part of a blog post series exploring the collection's capabilities.

[TOC]

## Introduction

The `redhatci.ocp` Ansible collection provides a comprehensive set of roles and modules for automating OpenShift Platform interactions, deployment, testing, and continuous integration. While the collection is often used with DCI (Distributed CI), it can also be used independently in standalone Ansible playbooks.

This blog post is part of a series exploring the `ansible-collection-redhatci-ocp` collection. In this installment, we'll focus on running PTP (Precision Time Protocol) tests on an already deployed OpenShift cluster. PTP is critical for Cloud Native Functions (CNF) workloads that require precise time synchronization, such as 5G RAN applications.

We'll demonstrate how to use the `redhatci.ocp.eco_gotests` role to execute PTP test suites without requiring DCI infrastructure, making it accessible for teams who want to validate PTP functionality on their existing clusters.

## Installing the Collection

Before we can use the collection, you can install it as an RPM package:

```bash
dnf -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
dnf -y install https://packages.distributed-ci.io/dci-release.el8.noarch.rpm
dnf -y install ansible-collection-redhatci-ocp
```

## Prerequisites

Before running PTP tests, ensure you have the following prerequisites in place:

### Cluster Access

- Access to an already deployed OpenShift cluster
- A valid `kubeconfig` file with cluster administrator permissions
- The `kubeconfig` should be accessible from the machine where you'll run the playbook

### System Requirements

- **Ansible**: Version 2.9 or later
- **Podman**: Required for running the eco-gotests container
- **Python dependencies**: The collection may require additional Python libraries (check the collection's `requirements.txt`)

### PTP Operator Requirements

The PTP operator must be installed and properly configured on your cluster:

- **PTP Operator installed**: The operator should be available in the `openshift-ptp` namespace
- **PtpOperatorConfig properly configured**: The `PtpOperatorConfig` resource must have the following configuration in its `spec.ptpEventConfig` section:
  - `enableEventPublisher: true`
  - `apiVersion: "2.0"`

Here's an example of the required configuration:

```yaml
apiVersion: ptp.openshift.io/v1
kind: PtpOperatorConfig
metadata:
  name: default
  namespace: openshift-ptp
spec:
  ptpEventConfig:
    enableEventPublisher: true
    apiVersion: "2.0"
```

You can verify the PTP operator installation and configuration:

```bash
oc get namespace openshift-ptp
oc get ptpoperatorconfig -n openshift-ptp
oc get ptpoperatorconfig default -n openshift-ptp -o yaml
```

### Registry Authentication

- A registry authentication file (pull-secret) with access to the eco-gotests container image
- The default image is `quay.io/ocp-edge-qe/eco-gotests:latest`

## Understanding the eco_gotests Role

The `redhatci.ocp.eco_gotests` role is designed to run eco-gotests for OpenShift CNF testing. It supports two main test suites:

- **PTP (Precision Time Protocol)**: Tests for time synchronization functionality
- **SRIOV (Single Root I/O Virtualization)**: Tests for SR-IOV network functionality

The role uses Podman to run a containerized test suite that connects to your OpenShift cluster and executes the specified tests. Test results are saved as JUnit XML files in a directory you specify.

### Required Variables

The role requires the following variables:

- `eco_gotests_test_suites`: List of test suites to run (e.g., `['ptp']` or `['ptp', 'sriov']`)
- `eco_gotests_log_dir`: Path where test logs and reports will be stored
- `eco_gotests_kubconfig_dir`: Directory containing the kubeconfig file
- `eco_gotests_registry_auth_file`: Path to the registry authentication file (pull-secret)

### Optional Variables

- `eco_gotests_image`: Container image for eco-gotests (default: `"quay.io/ocp-edge-qe/eco-gotests:latest"`)

## Running PTP Tests 

Now let's create a complete playbook that uses the `eco_gotests` role:

```yaml
---
- name: Run PTP tests on OpenShift cluster
  hosts: localhost
  vars:
    eco_gotests_test_suites: ['ptp']
    eco_gotests_log_dir: /tmp/ptp-test-results 
    eco_gotests_kubconfig_dir: /home/user/cluster-configs # must be updated with your kubeconfig directory
  tasks:

    - name: Create log directory
      ansible.builtin.file:
        path: "{{ eco_gotests_log_dir }}"
        state: directory
        mode: '0755'
       
    - name: Run PTP tests using eco_gotests role
      ansible.builtin.include_role:
        name: redhatci.ocp.eco_gotests
    
    - name: Display test results location
      ansible.builtin.debug:
        msg: "PTP test results are available in {{ eco_gotests_log_dir }}"
```

## Conclusion

The `ansible-collection-redhatci-ocp` collection provides powerful automation capabilities that can be used independently of DCI infrastructure. In this blog post, we demonstrated how to use the `eco_gotests` role to run PTP tests on an already deployed OpenShift cluster.

This is part of a blog post series exploring the collection's capabilities. Stay tuned for more posts covering other roles and use cases.

For more information:
- [Collection GitHub Repository](https://github.com/redhatci/ansible-collection-redhatci-ocp)
- [eco_gotests Role Documentation](https://github.com/redhatci/ansible-collection-redhatci-ocp/blob/main/roles/eco_gotests/README.md)
