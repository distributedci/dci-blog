Agent-Based Install on LibVirt
==============================

:date: 2025-03-11 10:20
:slug: abi-on-libvirt
:authors: Jorge Gallegos
:github: thekad
:summary:
    This blog post showcases the steps needed (with automated examples) to get
    an Agent-Based Installer (ABI) cluster in a Virtual Lab up and running

.. contents:: Table of Contents

A couple of years ago, we added support for installations using the on-premise
assisted install (and even `wrote a blog post on how to start a virtual lab
</ocp-assisted-libirt-quick-start.html>`_). Around the same time the OCP
developers added a much more streamlined install method to the install binary
itself. It works mostly out of the box so we just had to get it integrated on
our supported methods and works so well that it has replaced the old assisted
on-premise installation method in the DCI OCP agent.

In this post we’ll be looking at how we can adjust to the Agent-Based installer
method using the DCI OpenShift Agent, spoiler alert: very few things change

Pre-Requisites
--------------
Going by the hardware requisites listed in our official documentation we can
estimate the size of the server that will hold our virtualized environment, it
will depend on how many nodes you want to have in your test lab:

* Single Node OpenShift
* Minimum 3-node OpenShift cluster
* Split 3+3 node OpenShift cluster

For a cluster the size of each VM we need is 8 cores and 16G of RAM, while the
SNO configuration requires a bigger VM (16 cores and 64G of RAM) to house the
whole thing in a single node.
For the purpose of this exercise we’ll pick the control-plane only cluster so
it fits within a regular sized server

Regarding software, our main lab server (our “jumpbox” in DCI lingo) needs RHEL
8 with a valid subscription, EPEL and the DCI release/repositories

Setup DCI Lab
-------------
Once we have our basic RHEL 8 system installed, we can proceed with the rest of
the setup. We've had a few posts before covering sort of the same process but
it all boils down to:

1. Follow the `Virtual Lab Quickstart <https://docs.distributed-ci.io/dci-openshift-agent/docs/abi/#virtual-lab-quick-start>`_ manually or
2. Cheat and use the example `ansible playbook <examples/2025-03-11-abi-on-libvirt/dci-lab-setup.yml>`_

For the purposes of this blog post we're going to be lazy and go with the easy
path (since I already did the work for you!)

.. tip::

   Feel free to modify the provided example playbook to suit your needs! there
   should be a similar playbook in the DCI OCP Agent samples directory, maybe
   even more up to date

Let's examine the playbook piece by piece, the first block is where our
variables are defined

.. include:: examples/2025-03-11-abi-on-libvirt/dci-lab-setup.yml
   :code: yaml
   :number-lines: 6
   :start-line: 5
   :end-line: 23

A couple of things to note here:

1. The RHSM information may not be needed, maybe you have your own way to
   ensure and subscribe your systems to RHSM. In my particular case I have
   these values `stored in an ansible vault
   <https://docs.ansible.com/ansible/latest/vault_guide/vault_encrypting_content.html>`_
   but your mileage may vary
2. The DCI API client and secrets you should fetch from `<https://distributed-ci.io/remotecis>`_

Now the first part of the playbook is basic OS level setup, like subscribing to
RHSM or enabling insights, no need to go too deep into those until line 56:

.. include:: examples/2025-03-11-abi-on-libvirt/dci-lab-setup.yml
  :code: yaml
  :number-lines: 56
  :start-line: 55
  :end-line: 60

Here we enable some extra repositories as defined in the variables at the top.
This bit is important because the DCI agent requires ansible <= 2.9.27 as of
February 2025.

We also install the RPM signing keys and release packages for EPEL and DCI and
then finally we install the appropriate version of ansible and lock its version
to avoid accidentally upgrading in the future. We don't *technically* need to
do this but I like to avoid possible headaches when/if I update the packages in
my system.

.. include:: examples/2025-03-11-abi-on-libvirt/dci-lab-setup.yml
   :code: yaml
   :number-lines: 84
   :start-line: 83
   :end-line: 96

We finally install the ``dci-openshift-agent`` package which actually has
provisions in place to install the supported versions of every requirement as
long as we have the correct repos configured.

After that there's a bit of extra setup that is added as a convenience:
generating an SSH key pair for the ``dci-openshift-agent`` user and add it to
the ``authorized_keys`` so you're able to talk to localhost. In this particular
case our jumpbox is actually localhost, so we need to be able to SSH in back as
our user.

.. include:: examples/2025-03-11-abi-on-libvirt/dci-lab-setup.yml
   :code: yaml
   :number-lines: 104
   :start-line: 103
   :end-line: 145

Finally, we create the Remote CI authentication file for the OCP agent in
``/etc/dci-openshift-agent/dcirc.sh`` and another one for DCI Pipeline in
``/etc/dci-pipeline/credentials.yml``

.. include:: examples/2025-03-11-abi-on-libvirt/dci-lab-setup.yml
   :code: yaml
   :number-lines: 150
   :start-line: 149
   :end-line: 169

As you can see the example playbook follows the documentation step by step, and
just does a few more things for convenience.

Here's a short screencast showing the playbook in action, depending on how many
things you changed the output *should* be similar. Run it and after a few
minutes you should have a general-purpose DCI jumpbox with the appropriate
configuration to run the OCP agent.

.. raw:: html

    <script src="https://asciinema.org/a/7AWMulRigVCCZfbgDNC5dMgFK.js" id="asciicast-7AWMulRigVCCZfbgDNC5dMgFK" async="true"></script>

Generating Ansible Inventory
----------------------------
In order to complete your lab is generating an inventory file that can control
our VMs. Specifically for the ABI method there's an example installed as part
of the OCP agent package. You'll need to excute a tiny playbook on your jumpbox
(which should already have the package installed) as the
``dci-openshift-agent`` user. There's a
``samples/abi_on_libvirt/parse-template.yml`` playbook in the user's home:
executing this playbook with the desired configuration will leave you with an
ansible inventory that you can put in your ``/etc/dci-openshift-agent``
directory. Today we're setting up an inventory with a control-plane only
configuration, so we execute the playbook like so:

.. code:: bash

   $ whoami
   dci-openshift-agent
   $ cd samples/abi_on_libvirt
   $ ansible-playbook --inventory dev/controlplane parse-template.yml

.. raw:: html

   <script src="https://asciinema.org/a/oduT9HIMQp3HfHbNtl0egdvni.js" id="asciicast-oduT9HIMQp3HfHbNtl0egdvni" async="true"></script>

.. tip::

   Feel free to explore the other inventories and adjust the resulting
   inventory to your liking, e.g. number/distribution of nodes, VM size, etc

Once you have a hosts file you can then copy it to
``/etc/dci-openshift-agent/hosts``.

Installing Underlying VM Infrastructure
---------------------------------------
Since we're mimicing a real-world physical cluster (and accompanying provision
infrastructure) in a single machine with virtual machines, we also need to
mimimic the usual infrastructure that is needed when installing any openshift
cluster, meaning NTP/DNS/HTTP servers

There is yet another `example playbook <examples/2025-03-11-abi-on-libvirt/vm-infrastructure.yml>`_ and,
again, there is probably a more up to date version in the OCP agent samples
directory.

This playbook leverages quite a few roles from the excellent `Red Hat CI OCP
Ansible collection
<https://galaxy.ansible.com/ui/repo/published/redhatci/ocp/>`_ with just a tiny
bit of extra logic on top.

Based on the inventory you created in the last step (and whatever adjustements
you make) this playbook will:

1. Install an HTTP store for you (container based)
2. Install a local container registry (container based, optional)
3. Setup and create a full libvirt environment
4. Setup DNS records for your VMs
5. Setup NTP server for your VMs
6. Install the `Sushy Tools emulator
   <https://docs.openstack.org/sushy-tools/latest/index.html>`_, to control
   your VMs with an RedFish-like interface

I'm not going too deep into this playbook because most of the work is done in
the imported roles, suffice is to say that once you're happy with your
``/etc/dci-openshift-agent/hosts`` inventory you can then run this playbook
like this:

.. code:: bash

   $ ansible-playbook --inventory /etc/dci-openshift-agent/hosts vm-infrastructure.yml

And here's a short screen cast of what (roughly) this playbook should
accomplish:

.. raw:: html

   <script src="https://asciinema.org/a/cOPVmgOOk18Lo39enlHfSL8x7.js" id="asciicast-cOPVmgOOk18Lo39enlHfSL8x7" async="true"></script>

.. hint::

   Please adjust both your inventory and/or playbook to your needs, most of
   the defaults are "fine" but may not suit your needs 100%

DCI Pipeline
------------
The last step is to create and adjust your pipeline file, an agent-based
install pipeline can be as simple as follows:

.. code:: yaml

   - name: my-openshift-abi
     stage: ocp
     ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
     ansible_cfg: /usr/share/dci-openshift-agent/ansible.cfg
     ansible_inventory: /etc/dci-openshift-agent/hosts
     dci_credentials: /etc/dci-pipeline/credentials.yml
     topic: OCP-4.17
     components:
       - ocp

And that's it, save that ``pipeline.yml`` wherever you like (since we're
referencing absolute paths) and let it run:

.. raw:: html

    <script src="https://asciinema.org/a/1mIEszMU4gFe98OCSZu9SURg7.js" id="asciicast-1mIEszMU4gFe98OCSZu9SURg7" async="true"></script>

.. note::

   The above screencast is sped up, the time for completion will vary
   depending on hardware factors

Conclusion
----------
If you followed all the steps so far (and no bugs were found) at the end you
should have a local lab with a Red Hat OpenShift (virtual) Cluster, you can now
interact with this cluster just like any other OCP cluster and you can run both
the DCI OpenShift and the OpenShift App agents on it, based on the exact same
inventory.
