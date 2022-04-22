Title: SNO deployments with DCI under the hood
Date: 2022-04-22 10:00
Category: divulgation
Tags: deployment, sno, virtual, baremetal
Slug: SNO with DCI under the hood
Authors: Manuel Rodriguez Hernandez
Summary: Single Node OpenShift (SNO) was introduced officially in OCP 4.9, available documentation describes the ways to deploy it using Assisted Installer through the Red Hat portal in order to generate an ISO and install it using virtual media or ACM. This article illustrates how we leverage some of those features and highlights the most relevant aspects of the installation using [DCI Openshift Agent](https://doc.distributed-ci.io/dci-openshift-agent/).

## SNO Official deployment options
Let’s take a look at the 2 official methods to deploy SNO:
1. Single Node OpenShift [Official deployment documentation](https://docs.openshift.com/container-platform/4.9/installing/installing_sno/install-sno-installing-sno.html) consists on generating a discovery ISO that will contain installation images and base information about the cluster. This ISO is used to bootstrap the node by attaching it to a Server or VM through a virtual media (CD-ROM or USB). This method is also known as installation through Assisted Installer.
2. Another deployment method is to use [Advanced Cluster Management (ACM) with Zero Touch Provisioning (ZTP)](https://docs.openshift.com/container-platform/4.9/scalability_and_performance/ztp-deploying-disconnected.html#ztp-single-node-clusters_ztp-deploying-disconnected), this option requires installing ACM, [Openshift Data Foundation (ODF)](https://access.redhat.com/documentation/en-us/red_hat_openshift_data_foundation/4.10) and [GitOps](https://docs.openshift.com/container-platform/4.10/cicd/gitops/understanding-openshift-gitops.html) operators in a running OCP cluster (with at least three nodes). It uses Assisted Installer mechanisms to install a separate or multiple Single Node Openshift clusters via virtual media or Preboot eXecution Environment (PXE).


## What DCI does to deploy SNO

SNO deployment via DCI is a very opinionated collection of playbooks to facilitate the automation and customization with as little hardware as possible, it can be used in hardware without virtual media support. It uses the traditional PXE method to perform the installation as it has proved to be the most compatible method across the platforms available to test by most partners.

DCI will take care of the orchestration of multiple phases to set up the provisioner node, deploy SNO, and run post-deployment operations like installing operators or running tests. It can install both: SNO on libvirt or SNO on Baremetal. OCP upgrades can also be executed in the SNO nodes deployed via DCI.

### Prerequisites

SNO deployments with DCI mainly require the installation of the [DCI OpenShift Agent](https://github.com/redhat-cip/dci-openshift-agent), and a provisioner node.

For Virtual SNO these are the main requirements:

- A provisioner node with virtualization capabilities is required, here libvirt will be installed to create a VM with at least 16GB RAM, 6vcpu, 20GB, (more resources recommended to be able to run operators and applications). 
- This can be installed on a Fedora laptop with 32GB in less than 45 mins.

For Baremetal SNO the main requirements are the following:

- The provisioner node does not require plenty of resources, as it would be just used as a server to connect to SNO and to host dnsmasq (TFTP, DHCP) services, as well as HTTP. Note: support of the Intelligent Platform Management Interface protocol [IPMI](https://en.wikipedia.org/wiki/Intelligent_Platform_Management_Interface) service is required.
- The SNO baremetal node can also run with 16GB RAM, 6vcpu, and 20GB disk, but more resources are recommended for a better experience.
 

### Virtual SNO main aspects

A full detailed description of the steps to deploy can be found [here](https://github.com/redhat-cip/dci-openshift-agent/blob/master/samples/sno_on_libvirt/README.md). And an [example](https://github.com/redhat-cip/dci-openshift-agent/blob/master/roles/sno-node-prep/tests/inventory-libvirt) of the inventory is provided in the DCI OpenShift Agent. Because it is a virtual deployment, predefined values are configured by default, and the cluster will only be accessible from the provisioner node (the host server). What happens during the installation is the following:

- Provisioner node is setup (libvirt storage, network) and cleanup phases are executed.
- Images from the release in question are downloaded, mainly the Live image to generate the final Discovery ISO.
- The install-config file is built from the variables and the manifest paths provided. Then the ignition file is generated from it.
- A Podman container is used to consume the ignition file and embed it into the Live image to generate the Discovery ISO.
- Finally, the VM is created and the ISO is attached as virtual media as the first option to boot the VM.

In summary, the initial steps listed above are what the SNO documentation provides, but in an automation fashion through DCI.


### Baremetal SNO main aspects

Also, a full picture of the variables, components, and installation requirements are described [here](https://github.com/redhat-cip/dci-openshift-agent/blob/master/roles/sno-installer/README.md). Similarly to the virtual deployment, the important parts are the variables defined in the inventory.
An inventory [example](https://github.com/redhat-cip/dci-openshift-agent/blob/master/roles/sno-node-prep/tests/inventory-baremetal) is provided in the DCI OpenShift Agent as reference.

The Baremetal deployment through DCI at first glance looks very different compared to the official documentation and the virtual installation, but what is important is that it uses the same bits. This means that instead of pulling the Live image and building a discovery ISO with an embedded ignition, the DCI agent will pull the kernel, ramdisk, and rootfs which usually come inside the Live image, and generate a grub configuration to boot via iPXE, the grub file will make reference to the images which are stored in the TFTP service in the provisioner node, and the ignition file is stored in a cache (HTTP) service. 

To summarize these are the main steps during the deployment:

- TFTP and HTTP services are set up in the provisioner node.
- Images are pulled and stored in the respective paths of the TFTP and HTTP services.
- The install-config file is built and the ignition file generated from it, then it’s stored in the cache service.
- The SNO baremetal node gets an IPMI call to set the Network device as the first boot option and powers on.
- The provisioner node will provide an IP via DHCP, the kernel/ramdisk images are pulled through TFTP and the installation will start using the configuration settings in the ignition file.
- The DCI agent will check the API readiness, wait for the node to be in ready status,  and the cluster operators to be running. 


## Conclusions
SNO allows the deployment of an OCP cluster without many complications and without worrying about having a mini data center for the deployment. Some of the recommended use scenarios are summarized below. Of course, I invited you to give it a try to the deployment via DCI and let us know your feedback or comments.

- Deploying SNO through virtual media manually can be a good option to test SNO specially if no extra customization is required.
- Deploying SNO via ACM through ZTP is a great choice for production environments that require multiple distributed SNO clusters, and planning to support them over a long term.
- Deploying SNO through DCI is meant to be used as a CI solution, allowing the use of all DCI features: From deploying continuously, customizing the configuration, tracking the results, to using hardware where virtual media is not an option. Useful for testing in a development environment or even a personal one.

