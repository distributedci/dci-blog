Title: Using performance profiles with DCI-openshift-agent
Date: 2023-09-21 10:00
Category: Openshift
Tags: OCP
Slug: dci-performance-profile
Author: Charles Caporali
Summary: This post gives an example of how to apply, using the dci automation, a typical PerformanceProfile for a Telco use case.

[TOC]

# Introduction

With the emergence of Edge computing, new needs come and cloud technologies must provide a solid answer. As an example, in the Telco / 5G world, it translates to a drastic reduction of the latency, from 50 ms response time in the 4G world to less than 1ms.
To answer this challenge, OpenShift Container Platform provides mechanisms to tune nodes and softwares running on OpenShift,  for real-time running and low latency options, like enabling a real time kernel. The low-level management of the nodes is achieved by the Performance Profile object which is managed by the Node Tuning Operator for OCP versions 4.11+ (and the Performance Addon Operator project for the previous versions of OpenShift). This profile allows the cluster admin to enable low level options on the nodes of the cluster, like disabling hyperthreading which minimize the latency, or even reserve CPU for the orchestrator's sake or isolate it to a specific workload.
In the context of running applications such as Cloud-native Network Functions (CNF) or Data Plane Development Kit (DPDK), the usage and the mastering of PerformanceProfile objects will be crucial. That is why [dci-openshift-agent](https://github.com/redhat-cip/dci-openshift-agent) handles this resource during the installation.
As a disclaimer, starting from OCP-4.11 and above, the Performance Addon Operator project has been moved as a part of the Node Tuning Operator. It does not change the nature of the PerformanceProfile object that is still behaving the same way.

# How does it work with the dci-openshift-agent

For OpenShift version 4.11 and above, the management of Performance Profile object is done by Node Tuning Operator, a cluster operator automatically shipped with a classic installation of OCP. The dci agent verifies that the operator is installed correctly by calling the corresponding CustomResourceDefinition, and finally creates the performance profile from the file given by the variable `performance_definition`.
For versions of OpenShift below 4.11, as part of the automation provided by the dci-openshift-agent, the Performance Addon Operator can be deployed as part of the installation of OCP; it is [pretty straight forward](https://doc.distributed-ci.io/dci-openshift-agent/#ansible-variables): by setting the variable `enable_perf_addon` to True, the agent will deploy the Performance Addon Operator on the freshly installed OCP cluster. If the cluster is working in disconnected mode, the mirroring of the operator is also handled by the automation. Then, a PerformanceProfile file is applied the same way it is done for the newer versions, by setting the variable `performance_definition` when launching the [DCI automation](https://github.com/redhat-cip/dci-openshift-agent/blob/master/plays/deploy-operators.yml#L151C1-L162C44).

The application of the PerformanceProfile is not a trivial step : the new profile will generate a MachineConfigPool that contains the new expected configuration of the nodes. It means that the impacted nodes are likely to restart in order to apply the low level options enabled by the application of the PerformanceProfile. At this stage, no workload should be running yet on the cluster so a reboot of some nodes should not be too harmful and not take so much time. Once all the MachineConfigPool are all in the expected state, the DCI automation can continue its fine tuning of the OCP platform.

# An example configuration for low latency

The low-latency-oriented tuning can be a direct example of what could be done with PerformanceProfile options. In the Telco world, maintaining a low latency network architecture is the key to reach the 5G requirements. One of the first options that comes to mind is the deployment of a Real-Time kernel on the worker nodes. By simply setting `realTimeKernel: enabled: true` in the PerformanceProfile, the matching nodes will restart with a RT version of the Linux kernel which can provide low and predictable response time.
Another important option is the possibility of partitioning the CPUs' resources. It can be done by using the CPU core ids:

    spec:
      cpu:
        isolated: "2-19,22-79"
        reserved: "0,1,20,21"

In the example above, the 76 CPU cores determined in the `isolated` section are specific to the usage of workloads. The 4 CPU cores from the `reserved` section are specific to the container needed for the cluster housekeeping. The balance of the number of CPU allocated in each section can influence the latency of the cluster responses but also the performance of the workloads running on top of it.
Another option that is widely used for low latency nodes is the disabling of hyperthreading. Again, disabling this option comes with a cost, because it divides by two the number of threads available on a node. Also be sure that, if you are using CPU partitioning, the CPU core ids you are using are still correct after the hyperthreading is disabled. It can be done by adding ’nosmt’ to the kernel argument.

    spec:
        additionalKernelArgs:
            - nosmt


There are plenty of other options available through the PerformanceProfile like the configuration of Huge Pages, the NUMA topology to be applied or all the fine tuning that can be done via the workload hints which combine power consumption and real-time settings. As the creation of the proper PerformanceProfile will largely depend on your needs and your hardware, finding the balance between performances, latency and power consumption requires some tries. Hopefully, there is a cmd-line tool, called Performance Profile Creator (PPC), provided with the Node Tuning Operator that can help you. For more details about the PPC see the [OpenShift Documentation](https://docs.openshift.com/container-platform/4.13/scalability_and_performance/cnf-create-performance-profiles.html).
Here is an example of a real configuration that it is used in our Dallas datacenter lab for testing CNFs, on nodes with 40 CPUs, with  the hyperthreading enabled, huge pages are set for increasing kernel-level performance and with some low-level kernel options:

    kind: PerformanceProfile
    apiVersion: "performance.openshift.io/v2"
    metadata:
    name: dallas-profile
    spec:
    cpu:
        isolated: "1-19,21-39,41-59,61-79"
        reserved: "0,40,20,60"
    hugepages:
        pages:
        - size: "1G"
            count: 32
            node: 0
        - size: "1G"
            count: 32
            node: 1
        - size: "2M"
            count: 12000
            node: 0
        - size: "2M"
            count: 12000
            node: 1
    realTimeKernel:
        enabled: false
    workloadHints:
        realTime: false
        highPowerConsumption: false
        perPodPowerManagement: true
    net:
        userLevelNetworking: false
    numa:
        topologyPolicy: "single-numa-node"
    nodeSelector:
        node-role.kubernetes.io/worker: ""

As we have seen in this article, the PerformanceProfile object is a powerful tool to manage and fine tune low level configuration of OpenShift nodes. It will help you find the right configuration for optimizing your workload, but keep in mind that using these low-level options can have a significant impact (positive or negative) on the performance of a node and applying a new PerformanceProfile may result in a reboot on all impacted nodes. Hopefully, DCI makes its usage simple and it leaves all the liberty to find the right balance between performance and latency to fit the needs of the Telco infrastructure.

