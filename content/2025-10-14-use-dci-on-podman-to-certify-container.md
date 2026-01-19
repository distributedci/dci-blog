Title: Use DCI on Podman to certify containers
Date: 2025-10-14 10:00
Category: how-to
Tags: dci, podman, container-certification, preflight, dci-pipeline-podman, pyxis
Slug: use-dci-on-podman-to-certify-container
Author: Pierre Blanc, Andrew Vu
Github: pierreblanc
Summary: Learn how to quickly set up container certification using DCI with Podman. This guide shows you how to use dci-pipeline-podman for streamlined Pyxis test execution with minimal configuration.

[TOC]

Container certification has never been easier! With the new `dci-pipeline-podman` approach, you can run Red Hat container certification tests with just a simple dci pipeline configuration. No complex setup required, just install one package and create a minimal pipeline file.

## What you need

The beauty of this approach is its simplicity:

- **RHEL jumphost**: Your execution environment
- **dci-pipeline-podman**: The only package you need to install
- **Container images**: Ready for certification
- **Pyxis credentials**: For submitting results to Red Hat Partner Connect

For detailed DCI setup and configuration, see our comprehensive guides:
- [Introduction to Red Hat Distributed CI](https://blog.distributed-ci.io/introduction-to-the-red-hat-distributed-ci.html)
- [Certification tests for OpenShift containers and operators](https://blog.distributed-ci.io/preflight-integration-in-dci.html)

## Quick setup

### 1. Install dci-pipeline-podman

```bash
# On your RHEL jumphost
sudo dnf install dci-pipeline-podman
```

That's it! All DCI tools are now available in containers, managed automatically. I was tested with RHEL 8/9.

### 2. Create inventory file

Your inventory must include the jumphost because tasks execute on this host via SSH:

```ini
# ~/my-certification/inventories/jumphost.yml
[jumphost]
jumphost
```

> **Note:** Not compatible with `ansible_connection=local`

> **Note:** The jumphost must be able to connect to itself via SSH. This means passwordless SSH (e.g., using SSH keys) from the jumphost to itself must be set up and working. This is required because DCI executes tasks over SSH, even when targeting the local host.


### 3. Minimal pipeline configuration

Create this simple pipeline file for Pyxis-only container certification:

```yaml
# ~/my-certification/pipelines/container-certification-pipeline.yml
---
- name: container-certification
  stage: pyxis-only
  ansible_playbook: /usr/share/dci-openshift-app-agent/dci-openshift-app-agent.yml
  ansible_inventory: ~/my-certification/inventories/jumphost.yml
  dci_credentials: ~/.config/dci-pipeline/dci_credentials.yml
  ansible_extravars:
    # Pyxis API credentials
    #pyxis_apikey_path: ~/.config/dci-pipeline/pyxis-apikey.txt"
    #organization_id: "YOUR_ORG_ID"

    # Registry credentials (if needed)
    #partner_creds: ~/.config/dci-pipeline/partner_config.json

    # Your kubeconfig file to run the tests
    kubeconfig_path: ~/my-certification/kubeconfig

    # Containers to certify
    preflight_containers_to_certify:
      - container_image: "quay.io/myorg/myapp:v1.0.0"
        create_container_project: true
        short_description: "My application container for certification"
        pyxis_product_lists:
          - "YOUR_PRODUCT_LIST_ID"
```

## Running certification

Execute your pipeline:

```bash
dci-pipeline-podman ~/my-certification/pipelines/container-certification-pipeline.yml
```

## What happens

The pipeline automatically:

1. **Pulls your container** using Podman on the jumphost
2. **Runs Preflight tests** in a containerized environment
4. **Creates certification project** in Red Hat Partner Connect (if configured)
5. **Submits results** directly to Pyxis API
6. **Generates reports** available in DCI UI

## Multiple containers

Certify multiple containers in one run:

```yaml
preflight_containers_to_certify:
  - container_image: "quay.io/myorg/frontend:v1.0.0"
    create_container_project: true
    short_description: "Frontend application"
    pyxis_product_lists: ["FRONTEND_PRODUCT_LIST"]
  - container_image: "quay.io/myorg/backend:v1.0.0"
    create_container_project: true
    short_description: "Backend API"
    pyxis_product_lists: ["BACKEND_PRODUCT_LIST"]
  - container_image: "quay.io/myorg/worker:v1.0.0"
    pyxis_container_identifier: "EXISTING_PROJECT_ID"  # Use existing project
```

## Debugging

Check results in the [DCI UI](https://www.distributed-ci.io/jobs):

- **Tests tab**: JUnit results from Preflight
- **Files tab**: Detailed logs including `*preflight.log`
- **Job states**: Step-by-step execution details


## Next steps

- **Schedule jobs with dci-queue**: Automate and chain multiple certification jobs using [dci-queue](https://docs.distributed-ci.io/dci-queue/).
- **Submit certification results**: After a successful run, results are automatically submitted to Red Hat Partner Connect (Pyxis). You can verify submission status in the DCI UI or in the job logs.
- **Integrate with CI/CD**: Trigger DCI jobs from your existing CI/CD systems (GitHub Actions, GitLab CI, Jenkins) using the DCI API or CLI for end-to-end automation.


For advanced scenarios and detailed troubleshooting, see [Exploring Certification Test Suites Integrated in DCI](https://blog.distributed-ci.io/certification-test-suites-in-dci.html) or [DCI Documentation](https://docs.distributed-ci.io/)
