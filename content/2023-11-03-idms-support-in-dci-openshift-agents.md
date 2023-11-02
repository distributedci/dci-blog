Title: Image Digest Mirror Set (IDMS) support in DCI OpenShift Agents
Date: 2023-11-03 10:00
Category: DCI
Tags: disconnected, dci, idms, icsp, airgap, mirroring,
Slug: idms-support-in-dci-openshift-agents
Author: Tony Garcia
Github: tonyskapunk
Summary: The DCI openshift agents bring transparent support to use the newly added Image Digest Mirror Sets (IDMS) in OpenShift. The main use of IDMS is in disconnected clusters. The IDMS provides the registry mirroring functionality for images that are not reachable due to network constraints.

Red Hat OpenShift Container Platform (OCP) is a leading Kubernetes distribution that provides a scalable and secure environment for running containerized applications. In recent releases, [OCP (4.13) is deprecating](https://docs.openshift.com/container-platform/4.13/release_notes/ocp-4-13-release-notes.html#ocp-4-13-icsp) the [image content source policies (ICSPs)](https://docs.openshift.com/container-platform/4.13/rest_api/operator_apis/imagecontentsourcepolicy-operator-openshift-io-v1alpha1.html) the replacement is a couple of new resources [image digest mirror sets (IDMS)](https://docs.openshift.com/container-platform/4.13/rest_api/config_apis/imagedigestmirrorset-config-openshift-io-v1.html) and [image tag mirror sets (ITMS)](https://docs.openshift.com/container-platform/4.13/rest_api/config_apis/imagetagmirrorset-config-openshift-io-v1.html). This blog post will focus on the former, IDMS; and how the dci-openshift-agent integrates transparently to make easier to manage image synchronization in [disconnected environments](https://blog.distributed-ci.io/disconnected-environments-quick-start.html). At this point, the installers supported by the dci-openshift-agent that use IDMS are IPI, ACM, and SNO.

A cluster in a disconnected environment or Air-gap; is a cluster with a restricted network, usually meaning no Internet access or limited access. Such environments require a registry to mirror and synchronize images between the public Internet and the restricted environment. The following diagram is an example of a disconnected cluster with restricted access to the Internet through a firewall.

![Diagram of an OCP cluster with three nodes acting as the control-plane and three nodes as workers. All the nodes connect to two networks. On the top network, the one that goes to the Internet, is behind a firewall, limiting access to registries like quay.io. On the bottom network, the nodes are interconnected to a local registry. All the nodes include a reference to a Machine Config. The machine config comes from the IDMS and configures the nodes to the mirroring configuration. The workers contain a reference to a Pod]({static}/images/20231103-idms/disconnected_environment.jpg)

## ICSP and IDMS characteristics

ICSP and IDMS hold cluster-wide information about how to handle registry mirror rules using digest pull specification. Both resource definitions look pretty similar, and they operate in a similar way, with only a couple of differences. The image below shows an example of them.

![Example of an ImageContentSourcePolicy and an ImageDigestMirrorSet resource]({static}/images/20231103-idms/idms_icsp.jpg)

From the image above, both resources require a list of Digest Mirrors. Those mirrors include a source and a list of mirrors for the specified source. Both resources allow images referenced by image digests in pods to be pulled from the alternative mirrored repository locations. Any image specified using a tag **does not** use ICSP or IDMS.

IDMS functionality brings two main differences compared to ICSP.

1. If the image pull specification matches the repository of "source" in multiple *imagedigestmirrorset* objects. Then, only the objects that define the most specific namespace match are used.
1. If the "mirrors" are not specified, the image will continue to be pulled from the specified repository in the pull spec.

> NOTE: With the introduction of ITMS it will be possible to expand this constraint in the image pull specification to tags. At this point the DCI agents do not bring yet support to ITMS.

## Operation with ICSP and IDMS

In a disconnected environment, it is common that some (if not all) of the images consumed by pods are not reachable at their source due to restrictions in the network. A list of mirrors is then required to provide that image. When defining an IDMS resource, a machine config is generated and applied to all the nodes in the cluster. This allows the nodes to use the mirrors for the sources defined in the IDMS.

When a pod is scheduled, the images containing a Digest are compared against the IDMS sources, and then the mirrors are used to pull the image. Here is a simplified diagram showing when IDMS are used:

![A Pod containing a container with an image using a pull specification by digest. An IDMS for that image using a mirror. A couple of arrows showing the case when an image is used by Tag, going to a public registry (quay.io) and when using a Digest that matches the IDMS, going to a local registry]({static}/images/20231103-idms/IDMS_flow.jpg)

If the image contains a Digest, e.g. quay.io/example-by-digest@sha256:a1b2c3... And this pull specification matches a source in IDMS, then the mirror list is used to pull that image.

## DCI Agents and IDMS

The dci-openshift-agent is a tool that enables partners and alike to run OCP on their labs, with their hardware, and in their environment. In specialized industries, like telcos, the use of disconnected (Air-gap) clusters is a requirement. The dci-openshift-agent brings support to IDMS making it easy for disconnected clusters to operate.

Starting in OCP 4.14 the DCI agents will automatically use IDMS instead of ICSP. The [dci-openshift-agent](https://doc.distributed-ci.io/dci-openshift-agent/) will take care from the installation of OCP, to the setup of operators in the cluster. The [dci-openshift-app-agent](https://doc.distributed-ci.io/dci-openshift-app-agent/) will adapt to use IDMS if the cluster is already using them.

## Closing notes

The DCI agents are taking care of a deprecation change going on in OCP in a transparent way. Whether a deployment using any of the agents is using 4.13 or below, or 4.14 or above. Under the hood, we are taking care by using the appropriate mechanism to look at the images required by the cluster so you don't have to worry about it.

---
