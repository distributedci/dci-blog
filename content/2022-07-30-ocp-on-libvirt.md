Title: Setting up a virtual development environment for OCP agent
Date: 2022-07-30 10:00
Category: how-to
Tags: dci, ocp, development, libvirt
Slug: libvirt-dev-env-for-ocp-agent
Author: Jorge Gallegos
Github: thekad
Summary: Developing for the OCP ecosystem can be a daunting task, developing for the ecosystem that tests this can become even more so but, fear not, we have tried to make it as painless as possible.

## Do you need to read this?

Perhaps the most important question you should be asking yourself right now is
if you really need to follow the steps in this blog post. I can help you
answering this a little bit, if you:

1. Want to develop a custom _hook_ for your specific dci-openshift-agent
   (d-o-a) setup or
1. Identified a bug and the patch to fix it or
1. Want to add a core feature to the agent or
1. Just want to know more!

Then feel free to continue reading :)

!!! note
    All examples throughout this blog post assume we're working with
    RHEL/CentOS 8


## What does it mean to have a development environment?

A development environment in this case refers to a complete setup where you can
test your DCI OCP agent changes, this means a jumpbox and a System Under Test
(SUT)

Let's face it, not everyone has an extra rack with 4 (minimum) servers laying
around just to be used. If you do then great (I am a bit jealous even) but if
you're like me, then you have **at most** one extra (albeit beefy) server where
you can start tinkering with the DCI OCP agent.

For an everyday solution we created what we call an [OCP on LibVirt
setup](https://docs.distributed-ci.io/dci-openshift-agent/docs/ocp_on_libvirt/)
which means you have your entire cluster emulated in a single server. Your
jumpbox, your SUT, your mirrors, all of it, it can be done in a single machine.


## What do you need to start?

The requirements are simple, you need:

1. A server with a minimum of 200Gb disk and 64G of RAM
1. RHEL 8 (CentOS works as well, yes even Stream)
1. An SSH connection

That's all. Of course there are fancier ways to work on this but I will show
you the most basic ways to test your libvirt environment and then you can go
and explore on your own.


## The process

I am going to explain what the rough process to get a libvirt environment is,
then at the very end I will point you in the direction of an *experimental* (at
the time of this post) script to automate it all


### The base operating system

As mentioned before, you need a server with RHEL/CentOS 8. Make sure your
system has all updates installed and it's got an active subscription in the
case of RHEL.

Make sure you have enough space (around 200G for an [IPI
install](https://openshift-kni.github.io/baremetal-deploy/)) in the partition
holding your data, by default it is `/opt` but it can be customized

Install Ansible 2.9 because currently the OCP agent is not compatible with
2.12. If you are using CentOS want to install the
`centos-release-ansible-29-1-2` package first, then install `ansible-2.9.27`. I
like to optionally lock the version of ansible to avoid issues on future system
updates, example:

    #!bash
    sudo dnf install centos-release-ansible-29-1-2
    sudo dnf install 'dnf-command(versionlock)'
    sudo dnf update
    sudo dnf install ansible-2.9.27
    sudo dnf versionlock ansible

Install libvirt and all other packages needed:

    #!bash
    sudo dnf install libvirt \
        libvirt-daemon-kvm \
        libvirt-client \
        virt-install \
        libvirt-python3 \
        python3-netaddr \
        python3-lxml

The last specific piece is to enable nested KVM in your host, as one of the VMs
created during installation (the provision host) needs to create another VM
inside (the bootstrap VM). For that you need to edit/create a
`/etc/modprobe.d/kvm_nested.conf` file matching your processor family, and then
reload the module, something like this:

    #!bash
    grep -q GenuineIntel /proc/cpuinfo && PROC=intel || PROC=amd
    echo "options kvm-$PROC nested=1" | sudo tee /etc/modprobe.d/kvm_nested.conf
    echo "options kvm-$PROC enable_shadow_vmcs=1" | sudo tee -a /etc/modprobe.d/kvm_nested.conf
    echo "options kvm-$PROC enable_apicv=1" | sudo tee -a /etc/modprobe.d/kvm_nested.conf
    echo "options kvm-$PROC ept=1" | sudo tee -a /etc/modprobe.d/kvm_nested.conf
    sudo modprobe -r kvm_$PROC
    sudo modprobe -a kvm_$PROC

### Setting up DCI

The next step is to install the DCI repo and the required packages, easy enough
to do if you download the appropriate `dci-release` package from the DCI repo at
<https://packages.distributed-ci.io> and then installing the
`dci-openshift-agent` package:

    #!bash
    sudo dnf install -y https://packages.distributed-ci.io/dci-release.el8.noarch.rpm
    sudo dnf update
    sudo dnf -y install dci-openshift-agent

This creates a `dci-openshift-agent` user in your system, which should be the
owner for all directories and processes that drive the OCP agent. As such, you
should install your public key(s) under
`~dci-openshift-agent/.ssh/authorized_keys` so you are able to login directly.

This also creates a directory `/etc/dci-openshift-agent` which houses your DCI
remote authentication credentials. You can download your remote CI
authentication credentials [as per the official
documentation](https://docs.distributed-ci.io/#remote-ci) and once you have
them, add them to your `/etc/dci-openshift-agent/dcirc.sh` file.

The last step to configure DCI is to edit your
`/etc/dci-openshift-agent/settings.yml` file to suit your needs e.g. changing
the topic you want to test


### Creating your virtual SUT

A SUT (System Under Test) in this case is composed of a provision host plus a
mixed OCP control/data plane with 3 nodes, for a total of 4 VMs.

We have a playbook that will take care of that for you, it is located in
`samples/ocp_on_libvirt/libvirt_up.yml` under the `dci-openshift-agent` user
home dir, and you can execute it from your jumbox now that you have installed
ansible, like so:

    #!bash
    sudo -i -u dci-openshift-agent
    cd ~/samples/ocp_on_libvirt
    ansible-playbook -v libvirt_up.yml

This takes a little while, but at the end of the run you should be able to
check there are indeed 4 VMs running with `sudo virsh list --all`

This also creates a file `~dci-openshift-agent/samples/ocp_on_libvirt/hosts`
templated out from your SUT definition. You have to copy that file to
`/etc/dci-openshift-agent/hosts`. This file should work as-is assuming a
connected environment, you can edit this inventory to suit your needs e.g.
creating a disconnected cluster and etc.

!!! note
    Along with the `libvirt_up.yml` playbook there is a second
    `libvirt_destroy.yml` playbook which you can use to re-create your virtual
    SUT, should you need to.


## Running the agent

Once you have all the pieces in place, you can run the agent in two ways:

1. Using the packaged `/usr/bin/dci-openshift-agent` binary. This will use the
   stock/release codebase
2. Manually running via `ansible-playbook` if e.g. you're running from a local
   clone of the dci-openshift-agent codebase

For point #1 above there's not much to say, but let's say you're developing
something with the OCP agent, you want to test that out and of course the
released code doesn't have it. In such cases you need a copy of the codebase in
an editable place and then you can run your changes like this:

    #!bash
    source /etc/dci-openshift-agent/dcirc.sh  # this exports the DCI credentials
    cd /path/to/your/local/clone
    ansible-playbook dci-openshift-agent.yml -e @/etc/dci-openshift-agent/settings.yml -v

And done, you can iterate as many times as you want now.


## Cheat code

I have explained roughly the overall process to get you up and running, and you
may be asking yourself "well, this should all be in a playbook somewhere" which
you are 100% correct and, good news! It already is!

You may have noticed a suspicious `samples/ocp_on_libvirt/ocp-on-libvirt.yml`
playbook. This performs all the steps I have explained automatically. It is
experimental as of yet and prone to changes in the near future, but if you want
to try your luck here's what you can do:

1. Create a `~/.ocp-agent.yml` file containing the following variables:
    * `dci_client_id`: use DCI_CLIENT_ID from your remote CI credentials
    * `dci_api_secret`: use DCI_API_SECRET from your remote CI credentials
    * `rhn_user`: If your lab is RHEL, you need this to automatically subscribe
    * `rhn_pass`: If your lab is RHEL, you need this to automatically subscribe
    * `github_user`: To add your public keys to the agent's authorized keys list
2. Create an inventory file (or edit the default `/etc/ansible/hosts`) and add
   an entry for your lab
3. Execute the playbook. The playbook itself is executable thanks to the magic
   of shebangs and bash, so you can just
   `samples/ocp_on_libvirt/ocp-on-libvirt.yml myhost` or you can take a look at
   the shebang to figure out the proper call to execute it.

After this, you should end up with a system ready to execute the OCP agent.


## Closing thoughts

Developing for/with OCP is not easy; we at DCI aim to make it as easy as
possible to tighten the development->testing->release feedback loop, but there
is and always will be room to improve. So feel free to get in touch with us if
you see something not-quite-right or you have any questions, don't hesitate!
