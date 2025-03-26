Title: An Introduction to the DCI RHEL Agent
Date: 2025-03-25 10:00
Category: divulgation
Tags: dci, dci-rhel-agent, RHEL
Slug: dci-rhel-agent-intro
Author: Michael Burke
Github: miburke
Summary: An introduction to the DCI RHEL Agent's architecture, installation, and usage

[TOC]

# An Introduction to the DCI RHEL Agent

## Introduction
The RHEL agent is DCI’s offering which allows users to provision their test systems within their own CI lab with pre-release and milestone versions of RHEL.  Along with provisioning, the DCI RHEL agent provides hooks to run any tests a user may want to perform.  Results from these tests can be shared with Red Hat and stored in the DCI infrastructure for easy reference in any bug reports which may be necessary.  Test results can also be analyzed for trends using an analytics suite developed by DCI as well.

Perhaps you are a partner interested in the next publicly available RHEL kernel and would like to test with kernel changes in real time leading up to general availability (GA) release. Or perhaps you provide a product on top of RHEL and would like to be ready for release to your customers on day one of the next RHEL major or minor release.  DCI can help reduce your time to market by helping you identify and mitigate bugs prior to an official RHEL public release inside your lab to eliminate the cost of shipping and standing up your hardware in a Red Hat environment.

DCI also provides the modularity to allow a user to stand up an entire lab of test systems for provision and test by the RHEL agent, or if the full DCI stack is not something you would like to commit to right away, simply use another DCI offering, the Red Hat Downloader (RHDL) to download the latest pre-release RHEL composes and do with them as you please in your CI environment.  You then have the opportunity to take advantage of the full stack at your own pace if desired.

## Architecture

At a minimum, a DCI RHEL agent lab contains what DCI refers to as a “jumpbox” acting as a command and control node, and one or more Systems Under Test (SUT).  The jumpbox is where the agent is installed and run from, and must have network connectivity to all SUTs which are to be provisioned by the agent, along with a connection to the internet to download and host the pre-release RHEL composes hosted by DCI.  The RHEL agent and all supporting software runs in containers.

![architecture]({static}/images/2025-03-25-intro-to-dci-rhel-agent/dci_arch.png)

## Installation

The installation of the DCI RHEL agent and two supporting packages provides everything a partner needs to get started.  It includes a containerized version of the [Beaker](https://beaker-project.org/) provisioning software responsible for the installation of RHEL on partner test systems.  The installation of the RHEL agent installs and configures Beaker specifically for the partner lab it is installed on.  All test systems will be loaded in Beaker and ready for provision and test via a settings file that is configured prior to installation.

A single settings file is all that is needed to configure a DCI RHEL lab.  It will include network information, file storage information, test system inventory, and provisioning configuration.  An initial setup script will install and configure everything, and if additional test systems are added to the lab another run of the same setup script is all that is needed.  After initial setup, a pod of containers will be up and running Beaker alongside both a database and Apache container. All of your test system inventory will be in Beaker, and you will be ready to begin provisioning and testing those systems with DCI.


## Settings

The DCI RHEL agent’s configuration is controlled by a single settings file which contains all relevant information regarding the partners DCI lab machine inventory, along with the desired jobs to run on the lab machines.  The file is broken up into two main sections: “beaker_lab” and “topics”.


The beaker_lab section contains information regarding IP address ranges to be assigned to your test systems, jumpbox hostname information, along with an inventory of all test systems and their relevant information (MAC addresses, architectures, whether or not they use EFI BIOS, etc.).

```yaml
beaker_lab:
  beaker_dir: /opt/beaker
  dns_server: "{{ machine_network_ip }}"
  router: "{{ machine_network_ip }}"
  dhcp_start: "{{ machine_network_cidr | ip addr('20') | ipaddr('address') }}"
  dhcp_end: "{{ machine_network_cidr | ipaddr('100') | ipaddr('address') }}"
  build_bridge: true
  bridge_interface: eno2

  system_inventory:
    dci-legacy-client.dci.local:
      fqdn: dci-client
      mac: "78:2b:cb:27:1b:0b"
      ip_address: 192.168.1.20
      efi: false
      arch: x86_64
      power_address: dell-power-idrac.dcilab.com
      power_user: p_user
      power_password: p0wer
      power_type: ipmitool_lanplus
      power_id: ""
      petitboot: false
      linux_cmd_additions: ifname=eth0:00:01:02:03:04:05 ip=10.20.30.40
    dci-uefi-client.dci.local:
      fqdn: dci-uefi-client
      mac: "12:34:56:78:90:1b"
      efi: true
```

The topics section contains information for each job that a user would like the agent to perform.  Information includes the RHEL topic to use (RHEL-9.1, RHEL-8.6, etc.), what architectures to download, what variants to download, any kernel options to be used during installation, and what machines to provision.  Additional options like downloading debug packages, disabling password based logins for root, and the enabling of some Red Hat tests are also included in this section.

```yaml
topics:
  - topic: RHEL-10.1
    variants:
      - AppStream
      - BaseOS
    archs:
      - x86_64
      - aarch64
      - ppc64le
    with_debug: false
    dci_rhel_agent_cert: false
    dci_rhel_agent_cki: false
    disable_root_login_pw: true
    systems:
      - fqdn: dci-legacy-client.dci.local
      - fqdn: ibm-power-client.dci.local
        kernel_options: "console=hvc0"
      - fqdn: apm-mustang-aarch-client.dci.local
        alternate_efi_boot_commands: true
```

## Running Your Tests On Your Hardware In Your Lab

After the successful provisioning of a system, the DCI RHEL agent will run an Ansible playbook which can be customized by the partner to execute any new or existing tests they would like.  While the hook provided is an Ansible file, almost any tests can easily be executed regardless of format, making integration with existing CI infrastructures and test suites easy.  This allows an existing CI infrastructure to execute after DCI has provisioned all test systems, enabling testing on the latest pre-release RHEL content.  After user test execution, any relevant test files can be specified by the user to be collected by the agent, bundled with the overall job results, and accessible via the DCI web-based user interface.  Partner job and test results are viewable only by members of the applicable team, and the members of the DCI team.  Any sensitive files can be excluded from the agent’s collection after test execution.

While the sharing of test results is not mandatory, it is encouraged in order to give Red Hat insight into any issues encountered which will facilitate a quick response and resolution.  Furthermore, if a bug report is needed, files and logs associated with the issue can be easily referenced via a link to the job in the DCI web UI.  DCI has also implemented analytics features to allow for test statistics and trends to be visualized.


## DCI Partnership

DCI for RHEL is a powerful tool for any partner producing products which make use of RHEL.  With easy access to pre-release composes and automatic provision and test, a partner is able to be ready on day one of GA to deliver a working product to their customers while at the same time strengthening their partnership and collaboration with Red Hat.  DCI is always interested in accommodating as many customer use cases as possible and implementing ways to facilitate those for our partners to keep them moving forward quickly.


For more information please contact the DCI team at [distributed-ci@redhat.com](mailto: distributed-ci@redhat.com) and visit the [DCI documentation](https://docs.distributed-ci.io/dci-rhel-agent/).
