Title: How DCI embraces ZTP use cases
Date: 2025-06-02 10:00
Category: divulgation
Tags: dci, ztp, use-cases
Slug: ztp-use-cases
Author: Ramon Perez
Github: raperez
Summary: We have already presented some particular deployments where you have seen the benefits of leveraging DCI to deploy your OpenShift clusters by following the ZTP approach. In this blog post, we want to emphasize what are the kind of use cases that are currently covered by DCI, and what’s coming next in the support of ZTP deployments. You will see how DCI can help you to configure the cluster you need with a wide variety of cases.

[TOC]

# Introduction

Zero-touch Provisioning (ZTP) enables the remote provisioning of network elements at scale without manual configuration. We have already presented, in this [DCI Blog](https://blog.distributed-ci.io/), some resources where we have talked about how you can use Distributed-CI (DCI) to deploy OpenShift clusters using ACM and ZTP as the installation method. In particular, we have been focusing on GitOps-based deployments, a methodology that manages system configuration changes through a Git repository, achieving version-controlled and automated deployments.

See:

- [GitOps ZTP with DCI](gitops-ztp-with-dci.html) to find a wider explanation about GitOps ZTP with DCI, focused on baremetal setups.
- [An alternative GitOps ZTP deployment with DCI using virtual machines](ztp-vms.html) that demonstrates how to adapt this kind of deployment to virtual infrastructures.

However, DCI coverage for ZTP goes beyond GitOps. It is worth to mention that, within the ZTP framework, we offer support to multiple cluster setups (SNO and MNO), and the recently added [ClusterInstance API]((https://docs.distributed-ci.io/dci-openshift-agent/docs/acm/#clusterinstance)) through SiteConfig Operator v2. Additionally, day-2 operations are supported like cluster detachment and re-attachment. These use cases will be extended in this blog post, presenting them to OCP and DCI users, so that they can understand what are the benefits of using DCI to deploy these different ZTP use cases.

# ZTP use cases covered by DCI

Here's a tentative classification of all the possible ZTP deployments you can run with DCI, depending on different factors. You can combine these setups to adapt to your needs. We'll comment the particularities about each case in separated sections, providing tips to consider when addressing different scenarios. This will help you customize your ZTP setup according to your desired configuration.

- Spoke cluster size
    - SNO
    - MNO
- Underlying infrastructure
    - Baremetal
    - Virtual machines
- Network environment
    - Connected
    - Disconnected
- ZTP implementation
    - SiteConfig
    - ClusterInstance
- Day-2 operations
    - Detach a spoke cluster from a hub cluster
    - Attach a spoke cluster to a hub cluster
    - Redeploy the spoke cluster

## Spoke cluster size

With DCI, you can deploy ZTP spoke clusters based on a single node (SNO) or multiple nodes (MNO). The main difference to bear in mind is the node specification in the manifest description (in both SiteConfig or ClusterInstance resource, depending on the selected paradigm):

- For SNO, you just need to define one node.
- In MNO, you have to define all the nodes that will be part of the cluster, including at least 3 control plane nodes. Also, you need to define the apiVIP and ingressVIP addresses (for SNO, these addresses are the same that the IP address of the SNO node), while it's not required to define the machineNetwork CIDR (which is mandatory in the SNO case).

In the case of the hub cluster, it is also possible to deploy it in SNO or MNO configuration, so that you can combine all the possibilities between hub-spoke cluster sizes in a set of pipelines that are managed and automated with DCI. This means you can have the following configurations:

- SNO hub cluster and SNO spoke cluster.
- SNO hub cluster and MNO spoke cluster.
- MNO hub cluster and SNO spoke cluster.
- MNO hub cluster and MNO spoke cluster.

Having said that, it is also worth to mention a node architecture implemented by the Telco Partner CI team in their labs to test MNO deployments on a CI basis by minimizing the number of nodes to be used.

Imagine you have a [DCI queue]((dci-queue.html)) system with multiple resources, where each resource covers a set of nodes that can be used for a MNO deployment; for example, with 3 control plane nodes and 4 compute nodes, using installers such as IPI or ABI.

The idea of this architecture is to reuse these resources for a SNO hub-MNO spoke deployment, by taking one compute node to be used as the SNO hub cluster, and the rest of nodes (3 control plane and 3 compute nodes) as spoke clusters. You just need to ensure that the network used for the SNO hub cluster is isolated from the MNO spoke, using /32 IPv4 mask (or /128 for IPv6), and that you have a dnsmasq configuration that allows a correct network address resolution for each cluster (unless you use a static IP configuration; you can use both options with DCI).

Here you have an example of a [DCI execution](https://www.distributed-ci.io/jobs?limit=20&offset=0&sort=-created_at&where=pipeline_id:67e4933c-64a9-4471-9564-17b4aae33047,state:active) of this pipeline.

You can see here an example of a network configuration for this scenario:

- Hub cluster
    - Network prefix: /32
    - API VIP: 192.168.21.26
    - Ingress VIP: 192.168.21.26
    - sno node: 192.168.21.26
- Spoke cluster
    - Network prefix: /24
    - API VIP: 192.168.21.18
    - Ingress VIP: 192.168.21.19
    - master-0 node: 192.168.21.20
    - master-1 node: 192.168.21.21
    - master-2 node: 192.168.21.22
    - worker-0 node: 192.168.21.23
    - worker-1 node: 192.168.21.24
    - worker-2 node: 192.168.21.25

The sno node could be used also as worker-3 of the regular 3-control plane and 4-compute node cluster. This could be achieved by using this kind of entries in a dnsmasq config, to ensure the resolution of the correct name depending on the cluster that is used:

        # entry for the worker node
        dhcp-host=<MAC address>,192.168.21.26,worker-3.cluster1.our.lab
        host-record=worker-3.cluster1.our.lab,192.168.21.26
        host-record=sno-cluster1.our.lab,192.168.21.26

## Underlying infrastructure

As demonstrated in the already-published blog posts regarding ZTP, the nodes could be baremetal or virtual machines. As a reminder, these are the main differences between both cases:

- A physical server is associated with a physical BMC IP address. However, in the case of VMs, they must have a BMC emulator available, such as sushy-tools or Fakefish.
- To identify the disk to be used with the `rootDeviceHints` spec, while this can be directly extracted from the disk description of the physical server, in the case of VMs you need to build the disk reference based on the output from `virsh dumpxml` output.
- Network connectivity is crucial in both cases, but remember that, for the virtualized scenario, connectivity between physical and virtual servers is required.
- The boot entries on the virtual machine may have an impact on the re-deployment of the lab, whereas this is not really critical in the case of baremetal.

## Network environment

The main difference between connected and disconnected environments is the presence (or not) of Internet connection. DCI supports both setups; for the case of disconnected environments, you can check [here](https://docs.distributed-ci.io/dci-openshift-agent/docs/disconnected_en/) what you need to have in mind when deploying OpenShift in disconnected mode.

For the case of ZTP, the extra requirement that you need to fulfill in the case of the GitOps methodology is the access to the Git repository. Since there is no Internet access, it is not possible to reach the repository if the reference is set to a public site.

To overcome this situation, DCI offers the deployment of a [Gitea](https://github.com/go-gitea/gitea) server, typically deployed on the hub cluster. Through a Route OpenShift resource that is created by the automation, you can later on instruct DCI to point to that route to find the Git repository where sites and policies are defined. You can find more information about the usage of Gitea in the [ZTP GitOps chapter from DCI docs](https://docs.distributed-ci.io/dci-openshift-agent/docs/gitops-ztp/).

## ZTP implementation

We have already talked about GitOps. The GitOps approach provides a solution for the deployment of OCP clusters and configuration through version-control repositories.

The GitOps service provides a way to define CR manifests using Kustomized templates that are rendered through ArgoCD. The inventory-like templates live in the repository and are rendered to then be applied to deploy and configure a cluster.

The inputs for GitOps live all within the same repository, following a specific directory structure. For example:

        + clusterN
        |-- sites         <-- Deployment of cluster (currently v1 is supported in DCI)
        |-- policies      <-- Configuration of cluster (not supported in DCI)

Note that the GitOps + SiteConfig v1 combination is deprecated in OCP 4.18, and will be removed in the incoming OCP 4.20. Right now, we are working in the transition towards SiteConfig v2, which is work in progress.

When combining GitOps with DCI, the Git repository is treated as another input, together with the pipeline file and the inventory, which are the classical input files for DCI. The hardest part of this integration is the presence of two main sources of truth: the DCI side (pipelines and inventories) and the GitOps side (Git repository). The way to overcome this situation up to now is to statically configure the Git repository through the DCI automation. This allows us to synchronize some configuration from both sides that are initially diverging; for example, the OCP release to use:

- In the Git repository, the OCP version to use is referenced in the clusterImageRefSet resource; however, this can only be defined from the existing ClusterImageSet CRs available in the hub cluster. In regular deployments, this means that there's no access to, for example, nightly builds for spoke cluster deployments.
- In the case of DCI jobs, with the DCI components referenced in the pipelines, we can select any OCP release available in the DCI control server, which ranges from GA to nightly builds.

With the integration between DCI and GitOps, we can deploy the spoke cluster using the OCP release referenced in the DCI component from the pipeline. For this to work, we clone the GitOps repository to track, we extract the OCP version to use from the pipeline file (which includes from GA to nighly releases), we override the clusterImageRefSet and create an entry in the ClusterImageSet CR, then we deploy the spoke cluster.

However, this static approach also has some constraints. For example, DCI takes care of all the automation related to the spoke cluster deployment, based on the latest commit in the repository by the time DCI is launched. However, what happens in subsequent commits is not currently under the radar of DCI.

The alternative to this approach is the usage of the ClusterInstance API, using [templates](https://docs.distributed-ci.io/dci-openshift-agent/docs/acm/#clusterinstance-templates) to render the manifests that are required for this paradigm. In this case, no Git repository is required, so that the DCI execution would have again a single source of truth for the cluster configuration (i.e. pipelines and inventories). This makes easier the management of the CI loop.

As said in the DCI docs, the ClusterInstance, at least for SNO (which is currently the only cluster setup supported), requires 4 manifests documented in the [Installing single-node OpenShift clusters with the SiteConfig operator](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.12/html-single/multicluster_engine_operator_with_red_hat_advanced_cluster_management/index?ref=cloud-cult-devops#install-clusters). But the dci-openshift-agent only requires 3, as Namespace is created automatically. The other manifests are provided as templates to use the dci-openshift-agent capabilities to extract information from different sources like the hub itself, DCI control server, the inventory and the pipeline file. Here the links to the documention for each of the manifests required:

- [PullSecret](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.12/html-single/multicluster_engine_operator_with_red_hat_advanced_cluster_management/index?ref=cloud-cult-devops#install-create-pull-secret)
- [BMH-Secret](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.12/html-single/multicluster_engine_operator_with_red_hat_advanced_cluster_management/index?ref=cloud-cult-devops#install-create-bmc-secret)
- [ClusterInstance](https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.12/html-single/multicluster_engine_operator_with_red_hat_advanced_cluster_management/index?ref=cloud-cult-devops#install-render-manifests)

## Day-2 operations

After installing the spoke cluster, DCI also offers some day-2 operations that are included in the automation to be able to interact with the given spoke cluster. We have the following cases:

- [Detach a spoke cluster](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/samples/day_2_cluster_operations/detach_ztp_spoke_cluster) from a given hub cluster (also cleaning up the GitOps resources if present).
- [Attach the spoke cluster](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/samples/day_2_cluster_operations/attach_spoke_cluster) to a given hub cluster.

These two cases are managed by the [dci-openshift-app-agent](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/samples/day_2_cluster_operations), and are important to alter the relationship between hub and spoke cluster.

You can even re-deploy a spoke cluster, but right now, what DCI offers is the full redeployment by recreating all the GitOps or ClusterInstance resources. This is done with the dci-openshift-agent, instead, since this represents a new OCP cluster deployment.

Here you can find a [pipeline](https://www.distributed-ci.io/jobs?limit=20&offset=0&sort=-created_at&where=team_id:47513c50-d5a5-4d93-a63f-f6545a3313fc,tags:pipeline:ztp,state:active) where these day-2 operations are tested on a daily basis in the Telco Partner CI labs. In particular, a hub cluster is deployed, then we create a spoke cluster, we detach it from the hub cluster, we re-create the spoke cluster with a new, fresh installation, and we re-detach it from the hub. All this is done with virtual machines, with a MNO hub cluster and a SNO spoke cluster in a connected environment, using the GitOps approach.

# Conclusion

Drawing from the demonstrated capabilities in the preceding discussions, it's clear that DCI offers a robust platform for Zero-Touch Provisioning (ZTP) supporting a variety of use cases. These use cases can be distinguished based on various features, such as the underlying infrastructure (e.g. baremetal versus virtual machines), the network environment (e.g. connected versus disconnected setups), or the applied paradigm (e.g. GitOps versus ClusterInstance). This flexibility allows DCI to cater to a broad spectrum of deployment scenarios, from large-scale bare-metal rollouts to resource-efficient lab testing environments, all while leveraging consistent principles for automation and configuration management.

The good thing is, this is not the end of the support of DCI for ZTP cases! There is still a large room for new features to be created; especially in the GitOps side, since DCI currently supports a more "static" approach to the Git repository management, whereas the final objective is to be able to manage the GitOps within the CI, reconciling the CI philosophy and the GitOps way of managing that to make the workflow more dynamic. This would make DCI to react to new commits in the Git repo to monitor the changes in the running cluster. Also, more complex scenarios are to come, such as cluster upgrades or a better management of ACM policies (which would imply the replacement of some of the roles we currently use on DCI from the [redhatci.ocp collection](https://github.com/redhatci/ansible-collection-redhatci-ocp) to move to ACM policies created as day-2 operations after the cluster deployment).

Stay tuned to be the first one to know what are the news that will come to DCI with regards to the support of ZTP use cases. Don't hesitate top ping the Telco Partner CI team for any question you may have!
