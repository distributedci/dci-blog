Title: ACM integration in DCI
Date: 2023-01-05 09:30
Category: DCI
Tags: dci, integration, SNO, OpenShift, OCP, ACM
Slug: acm-int-dci
Author: Beto Rodriguez
Github: betoredhat
Summary: ACM is a tool that allows deploying, and managing OCP clusters and workloads on top of it. Now the DCI Agent has the support to automate the creation of SNO instances by the integration of the ACM roles.

[TOC]

## ACM in DCI

[Red Hat Advanced Cluster Management for Kubernetes](https://www.redhat.com/en/technologies/management/advanced-cluster-management) (ACM) controls and deploys OpenShift clusters.

ACM provides:

- SNO and multi-node cluster deployments.
- Built-in security policies.
- The ability to deploy applications
- The enforcement of policies across infrastructure platforms
- Resources governance.
- An easy-to-use console.

ACM is an easy method for deploying and managing OCP clusters. Now DCI supports installing SNO instances using ACM.

## ACM architecture

ACM is available in the Red Hat Catalog and can be installed by first creating a subscription and then a multi-cluster engine resource. It requires a storage class that will hold information about the managed clusters.

We will use the following ACM terminology to refer to the two kinds of clusters:

- Hub: The cluster running the ACM operator.
- Spoke: The cluster(s) deployed/managed by the Hub.

![acm_arch]({static}/images/2023-01-05-acm-integration/acm-architecture.png)

_Fig. 1. ACM architecture._

## The ACM Ansible Roles

The `dci-openshift-agent` uses two roles to deploy Hub and Spoke clusters.

- The [acm-setup](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/acm_setup/README.md) validates requirements, and then deploys and configures the ACM operator, which provides a graphical console for management.

- The [acm-sno](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/acm_sno/README.md) role interacts with the Hub to request and deploy an SNO instance, from installation to importing the resource into the ACM console.

![acm_arch]({static}/images/2023-01-05-acm-integration/acm-console.png)

_Fig. 2. ACM console._

These roles do not have any dependencies, as the only requirement for executing them is to provide a KUBECONFIG file as input. This file will allow interaction with the OpenShift clusters. Some examples of how to use the roles for multiple scenarios are available on the corresponding role’s readme.

## The integration with DCI

The creation of the roles was the first stage. Later on, we included them as part of the skeleton of the DCI Agent to take advantage of the known benefits of using DCI to deploy and test OCP..

The DCI Agent takes care of the following tasks and generates some of the parameters passed to the ACM roles.

- Performs the OCP release mirroring.
- Downloads container images and ISOs for disconnected environments. In connected-mode, it identifies the asset's URL in public repositories.
- Saves logging information and collects cluster information.
- Deploys OLM operators.

## What is next?

We had a quick overview of the ACM and some generalities about its integration with DCI. We are going to dedicate some blog posts on this matter, so if you have an interest in giving it a try, please take a look at [using ACM to deploy SNO](acm-deploy-sno).
