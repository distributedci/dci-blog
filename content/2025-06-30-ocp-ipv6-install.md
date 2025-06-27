---
title: Deploying OpenShift with IPv6 Static Addressing using NMState
date: 2025-06-30 12:00
category: Technical
tags: dci, openshift, networking, ipv6, installation
slug: ocp-ipv6-options
author: Manuel Rodriguez
github: manurodriguez
summary: OpenShift deployments offer multiple options to define IP addresses for servers. IPv4 configuration is well-known, and most services and appliances provide the means to define IPv4 addresses. However, when it comes to IPv6, new concepts are introduced, and standard services do not provide the same configuration capabilities as they do for IPv4. Besides, embracing IPv6 is crucial for scalability today. In this blog post, we will highlight the components that require IPv6 in OpenShift and demonstrate how to configure static IPv6 addressing during installation using NMState through DCI. This will be the first in a series of blog posts discussing the options available for setting up IPv6.

---

[TOC]

## Introduction

OpenShift, built on Kubernetes, relies heavily on robust networking for communication between nodes, pods, and services. While IPv4 has been the long-standing norm, the transition to IPv6 offers several benefits:

* **Vast Address Space:** IPv6 provides an almost limitless supply of unique IP addresses, eliminating the need for complex NAT (Network Address Translation) and simplifying network design.
* **Simplified Network Management:** Features like stateless address auto-configuration (SLAAC) and improved routing efficiency contribute to simpler network management.
* **Future-Proofing:** Many emerging technologies and regulatory requirements increasingly demand IPv6 compatibility.

OpenShift offers support for IPv6, including single-stack IPv6 and dual-stack (IPv4/IPv6) configurations, primarily leveraging the OVN-Kubernetes network plugin. For bare-metal installations, static IPv6 address assignment is often preferred for predictability and control. This is where NMState comes into play.

[Distributed-CI (DCI) OpenShift Agent](https://docs.distributed-ci.io/dci-openshift-agent/) leverages multiple OpenShift installers and provides the means to define IPv6 addresses by defining variables in an Ansible inventory file. It will prepare the respective configuration files for the installers and monitor the installation.

## Key OpenShift Components and IPv6 Requirements

When deploying OpenShift with IPv6, several core components need proper IPv6 address allocation:

* **Nodes (Control Plane and Workload Nodes):** Each node in your OpenShift cluster (both control plane and workload nodes) will require an IPv6 address for inter-node communication, management, and hosting pods.
* **Pod Network (clusterNetwork):** This is the network from which pods receive their IP addresses. For IPv6, a dedicated IPv6 CIDR must be allocated for pod communication.
* **Service Network (serviceNetwork):** Services in OpenShift use cluster IPs to provide a stable endpoint for applications. An IPv6 CIDR is needed for service IPs.
* **API VIP (apiVIPs):** The API VIP provides a stable entry point for clients to access the OpenShift API server. In an IPv6 deployment (especially dual-stack), both an IPv4 and IPv6 API VIP are required.
* **Ingress VIP (ingressVIPs):** The Ingress VIP is used for external access to applications running within the cluster. Similar to the API VIP, both IPv4 and IPv6 ingress VIPs are needed for dual-stack.
* **DNS:** Cluster DNS resolution (CoreDNS) will need to be configured to correctly resolve IPv6 addresses for services and pods.

**Note:** OpenShift 4.12 and later versions introduced `apiVIPs` and `ingressVIPs` to handle multiple IP addresses for dual-stack networking, where the first IP is IPv4 and the second is IPv6.

Also, when deploying single-stack IPv6 in OCP, you need to make sure your environment has the following requirements:

* Your Ansible controller node is configured with IPv6.
* HTTP store to store artifacts needs to listen on IPv6.
* Your DNS is able to resolve IPv6.
* You have a routable IPv6 network in connected mode.
* Your registry needs to listen on IPv6 in disconnected mode.
* NTP service able to reply to IPv6 requests.

An example of the cluster components described above in an OpenShift `install-config.yaml` will look like this:

    #!yaml
    networking:
      clusterNetwork:
      - cidr: fd01::/48  # IPv6 Pod network
        hostPrefix: 64
      networkType: OVNKubernetes
      serviceNetwork:
      - cidr: fd02::/112 # IPv6 Service network
    platform:
      baremetal:
        apiVIPs:
        - fd2e:6f44:5dd8::4 # IPv6 API VIP
        ingressVIPs:
        - fd2e:6f44:5dd8::5 # IPv6 Ingress VIP
        machineNetworks:
        - cidr: fd2e:6f44:5dd8::/64 # IPv6 Machine network (for baremetal)

An example of a NMstate node network definition with static IPv6 assignment in an OpenShift manifest will look like this:

    #!yaml
    interfaces:
      - name: enp1s0
        type: ethernet
        state: up
        ipv6:
          enabled: true
          dhcp: false
          addresses:
            - ip: fd2e:6f44:5dd8::10/64 # Static IPv6 address
              prefix-length: 64 # Indicates the subnet mask length
          routes:
            - destination: ::/0
              next-hop-address: fd2e:6f44:5dd8::1 # Default gateway
        dns-resolver:
          config:
            server:
              - fd2e:6f44:5dd8::1 # DNS server (e.g., your router or a dedicated DNS server)

## Configuring Static IPv6 during Installation with NMState

NMState is a declarative network configuration tool for Linux that provides a unified API for managing network settings. OpenShift leverages the Kubernetes NMState Operator to apply network configurations to cluster nodes. During installation, you can provide NMState configurations as part of the `install-config.yaml` to statically assign IPv6 addresses.

The main idea is to define NodeNetworkConfigurationPolicy (NNCP) manifests that describe the desired network state for your nodes. These policies are interpreted by [NMState](https://nmstate.io/) to produce NetworkManager configurations. For more information about NMState and the syntax to use it, please visit [NMState official website](https://nmstate.io/).

Here's a breakdown of the process and an example of doing this with DCI OpenShift Agent. The steps provided are mainly for installations of OpenShift using the Agent-Based Installer (ABI) and Installer-Provisioned Infrastructure (IPI) in either Single-Node OpenShift (SNO) or Multi-Node OpenShift (MNO) mode:

### Prerequisites:

- OpenShift Installer inventory
- IPv6 subnet, addresses for the nodes, and addresses to act as DNS, GW, and NTP.

### Agent-Based Installer (ABI)

Steps:

1.  Incorporate the following variables in your ABI inventory to define cluster IPv6 networks and VIPs:

        #!yaml
        all:
          vars:
            # crucible extra networks for ipv6
            extra_machine_networks:
             - cidr: fd2e:6f44:5dd8::/64
            extra_service_networks:
             - cidr: fd02::/112
            extra_cluster_networks:
             - cidr: fd01::/48
               host_prefix: 64
            extra_api_vip: fd2e:6f44:5dd8::6
            extra_ingress_vip: fd2e:6f44:5dd8::7

2.  Define NMState variables for the OpenShift nodes in the ABI inventory. You will specify the static IPv6 addresses for each node's network interfaces.
This is an example of an NNCP for a control plane node, assigning a static IPv6 address to a bonded interface named `bond0`. Here, we can observe the following:

    1. The `interfaces` variable is under `all.vars.nodes.vars.network_config`. This means that the configuration will apply to all nodes. If required to be different, each node can have its own definition in the respective inventory section.

    2. In this example, we are using a customized template under `all.vars.nodes.vars.network_config.template`. If not specified when using DCI OpenShift Agent, by default, it will use a [template](https://github.com/redhatci/ansible-collection-redhatci-ocp/blob/main/roles/process_nmstate/templates/nmstate.yml.j2) provided in the [Red Hat CI OCP collection](https://github.com/redhatci/ansible-collection-redhatci-ocp/) roles.

    3. This configuration is for a `bond0` interface in LACP mode with two physical ports. The `bond0` interface has IPv4 and IPv6 defined statically.

    4. Still under `network_config`, we can find `dns_server_ips` and `routes`, which can take the respective values from other variables, or be explicitly defined here.

            #!yaml hl_lines="6 8 20 21 30 33"
            all:
              vars:
                nodes:
                  vars:
                    network_config:
                      template: /path/to/nmstate/template.yaml.j2
                      interfaces:
                        - name: bond0
                          type: bond
                          state: up
                          link_aggregation:
                            mode: '802.3ad'
                            options:
                              miimon: 100
                            ports:
                            - ens1f0np0
                            - ens1f1np1
                          addresses:
                            ipv6:
                              - ip: "{{ ipv6_address.split('/')[0] }}"
                                prefix: "{{ ipv6_address.split('/')[1] }}"
                        - name: ens1f0np0
                          type: ethernet
                          state: down
                          mac: "{{ mac }}"
                        - name: ens1f1np1
                          type: ethernet
                          state: down
                      dns_server_ips:
                        - "{{ dnsmasq_baremetal_ipv6_dns }}"
                      routes:
                        - destination: "0:0:0:0:0:0:0:0/0"
                          address: "{{ dnsmasq_baremetal_ipv6_gw }}"
                          interface: "bond0"

3.  Finally, to provide the IPv6 addresses and MACs in the template above, there is a variable `mac` that defines the MAC address and `ipv6_address` that assigns two values (separated by a `/`) – one from field zero to `addresses.ipv6.ip` and the value in the second field to `addresses.ipv6.prefix`. These variables can be individually defined for each node under the respective section in the inventory, for example:

        #!yaml hl_lines="10 17"
        all:
          vars:
            nodes:
              children:
                masters:
                  hosts:
                    master-0.ocp.example.com:
                      name: master-0
                      mac: 00:11:22:33:44:c0
                      ipv6_address: "fd2e:6f44:5dd8::15/64"
        ...
                workers:
                  hosts:
                    worker-0.ocp.example.com:
                      name: worker-0
                      mac: 00:11:22:33:55:a2
                      ipv6_address: "fd2e:6f44:5dd8::16/64"
        ...

You would create similar blocks of variables for each control plane and worker node, adjusting the MAC and IPv6 addresses accordingly.

### Installer-Provisioned Infrastructure (IPI)

For "Installer-Provisioned Infrastructure" (IPI) on bare metal, these NMState policies can be generated in NNCP files and placed in the `manifests` directory alongside your `install-config.yaml` before running `openshift-install create cluster`. However, when using DCI OpenShift Agent, specific variables with IPv6 definitions will render the `install-config.yaml` to include the network configuration, VIPs, and networks to use.

Steps:

1.  Incorporate the following variables in your IPI inventory to define cluster IPv6 networks and VIPs:

        #!yaml hl_lines="6 7"
        ipv6_enabled: true
        extcidrnet6: fd2e:6f44:5dd8::/64
        apivip6: fd2e:6f44:5dd8::6
        ingressvip6: fd2e:6f44:5dd8::7
        nmstate_bonding: true
        master_network_config_template: /path/to/your/nmstate/master_template.yaml.j2
        worker_network_config_template: /path/to/your/nmstate/worker_template.yaml.j2

2.  The `master_network_config_template` and `worker_network_config_template` variables will point to a path in the Ansible controller server where DCI OpenShift Agent is installed, and here you can include any NMState definition that suits your environment. Both master and worker variables can point to the same template; these templates can be prepared using Jinja formatting to render any variables provided in the nodes section. Some variables are similar to the ABI installer, but others are specific to IPI roles. For example, a template can include the following, and the variables in curly brackets will take the values defined on each node:

        #!yaml hl_lines="14 15 24 27"
        interfaces:
          - name: bond0
            type: bond
            state: up
            link_aggregation:
              mode: '802.3ad'
              options:
                miimon: 100
              ports:
              - ens1f0np0
              - ens1f1np1
            addresses:
              ipv6:
                - ip: "{{ ipv6_address.split('/')[0] }}"
                  prefix: "{{ ipv6_address.split('/')[1] }}"
          - name: ens1f0np0
            type: ethernet
            state: down
            mac: "{{ mac }}"
          - name: ens1f1np1
            type: ethernet
            state: down
        dns_server_ips:
          - "{{ dnsmasq_baremetal_ipv6_dns }}"
        routes:
          - destination: "0:0:0:0:0:0:0:0/0"
            address: "{{ dnsmasq_baremetal_ipv6_gw }}"
            interface: "bond0" # Added for consistency if applicable

3.  Define NMState variables for the OpenShift nodes in the IPI inventory. You will specify the static IPv6 addresses for each node's network interfaces. When defining the following groups of variables, the IPI `install-config.yaml` templates in the roles will render the NMState templates with those values to generate the complete configuration.

        #!yaml hl_lines="10 17"
        all:
          vars:
            dnsmasq_baremetal_ipv6_dns: fd2e:6f44:5dd8::1
            dnsmasq_baremetal_ipv6_gw: fd2e:6f44:5dd8::1
            masters:
              hosts:
                master-0.ocp.example.com:
                  name: master-0
                  mac: b8:83:03:91:b5:c0
                  ipv6_address: "fd2e:6f44:5dd8::15/64"
        ...
            workers:
              hosts:
                worker-0.ocp.example.com:
                  name: worker-0
                  mac: 00:11:22:33:55:a2
                  ipv6_address: "fd2e:6f44:5dd8::16/64"
        ...

## Conclusion

IPv6 has become a very common implementation in Telco environments, and when doing CI, it is important to use it in every part of the configuration: in the cluster networks, in the nodes, and in the artifact services to make sure that everything that is tested is compatible with IPv6 addressing. In the case of static IPv6 addressing in OpenShift, it provides the following benefits:

- Easy to manage in small clusters.
- No need to configure a SLAAC or DHCPv6 service.
- Provides an easy entry point into IPv6 setup.

In the next blog posts, we will discuss other available options to provide IPv6 addresses to OpenShift cluster nodes. Stay tuned.
