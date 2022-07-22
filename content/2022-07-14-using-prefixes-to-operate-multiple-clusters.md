Title: Using prefixes to operate multiple DCI environments
Date: 2022-07-14 10:00
Category: how-to
Tags: introduction, dci, ci, OpenShift, OCP
Slug: using-prefixes
Authors: Nacho Silla
Summary: Prefixes allow you to control the inventory and settings of different DCI environments from a single central directory. We hope this article will convince you of the convenience of using prefixes in your DCI labs and will serve as a solid foundation for you to start leveraging their potential.

Prefixes allow you to control the inventory and settings of different DCI environments from a single central directory. We hope this article will convince you of the convenience of using prefixes in your DCI labs and will serve as a solid foundation for you to start leveraging their potential.

Although most of the examples here deal with the dci-openshift-agent, other DCI agents follow the same usage of prefixes and the examples are valid.

## The basic use case

In the most basic use case, the dci agents need the files *hosts* and *settings.yml* to exist in their configuration directory.

The *hosts* file identifies the target systems the agent will operate when launched, along with those Ansible variables related to the infrastructure.

The *settings.yml* file contains the main DCI related variables like the topic, the list of components or the job type the agent will be running.

The agent's configuration directory is the file system path where it looks for its input files. For the dci-openshift-agent it defaults to /etc/dci-openshift-agent and it goes likewise for the other DCI agents. As we'll see later, the path can be changed to some other location.

So... this being clarified, we were discussing the basic use case. In this scenario we just need to make sure the two files described above exist in the configuration directory and launch the agent:

```Shell
$ dci-openshift-agent-ctl -s -- -v
```

With this simple command line, the agent assumes default values are used so it just goes in the configuration directory and makes sure the *hosts* and *settings.yml* files exist. If they don't the agent will just fail reporting the missing file, otherwise, the agent will launch the Ansible playbook setting the inventory to point to the *hosts* file, and including the *settings.yml* variables file.

This is just an example or what the resulting *ansible-playbook* command would look like:

```Shell
ansible-playbook -e @/etc/dci-openshift-agent/settings.yml -i /etc/dci-openshift-agent/hosts -v dci-openshift-agent.yml
```

## Some more complicated use cases

Now, the basic use case is great when you just have one lab with a single OpenShift cluster and you don't even need to persist your settings. But you may be asking yourself:

- *What if I have one lab with multiple OpenShift clusters?*

- *What if I have a fleet of labs?*

- *What if I just have one lab, with one cluster, but I want to run different deployment scenarios (IPI, UPI, upgrades...)?*

- *What if I have any combination of the above?*

- *Do I need to keep editing the *hosts* and *settings.yml* files or swapping them for every testing scenario?*

Here is where prefixes come in handy.

## Prefixes to the rescue

Prefixes are just what their name imply: prefixes you may add to the *hosts* and *settings.yml* file name so you may manage multiple operation setups from the same config directory without having to edit any files and on an almost seamless fashion.

So, let's say you have your lab, and in that lab you have two different clusters which, in a sheer effort of imagination, we'll call *cluster1* and *cluster2*.

Each cluster has its own Provision Host and its own set of master and worker nodes with their individual addressess and BMC consoles.

With the tools and information we have so far, in order to have the dci-openshift-agent deploying over these two cluster we would have two copies of the *hosts* file somewhere in the filesystem and would keep placing the right one under /etc/dci-openshift-agent before running the agent.

Now, what at this point you may be guessing you can do instead of the above is just renaming each copy of the *hosts* file after the cluster they belong to just by adding the cluster name as a prefix:

```
cluster1-hosts
cluster2-hosts
```

This way the two files may exist under /etc/dci-openshift-agent and remain static for the rest of your lab life span.

Likewise, if each cluster is aimed at a different testing scopes (target versions, type of jobs, etc.) you may create copies of the *settings.yml* file and name them with the same prefixes. In this example:

```
cluster1-settings.yml
cluster2-settings.yml
```

The next time we run the agent, we can provide it with a prefix by passing the parameter *-p* with the target cluster prefix. For instance:

```Shell
$ dci-openshift-agent-ctl -s -p cluster1 -- -v
```

What happens then with the agent is that it implements a logic that allows it to look for the given prefixed file or fail back into the default file names if none is found. In other words, when a prefix is provided:

1. The agent tries to read the prefixed settings file (*cluster1-settings.yml*).

2. If the file exists, the agent passes the variables to the Ansible playbook.

3. If it does not exists, the agent tries to read the default *settings.yml* file.

4. If it exists, the agent passes the variables to the Ansible playbook.

5. If it does not exist, the agent fails reporting the missing file.

6. The agent tries to read the prefixed inventory file (*cluster1-hosts*)from the configuration directory.

7. If the file exists, the agent sets it as the inventory for the Ansible playbook.

8. If it does not exists, the agent tries to read the default *hosts* file.

9. If it does not exist, the agent reports the missing file and goes on with the execution.

The reason why the agent does not fail if the inventory file is missing is because there are other means to provide the Ansible playbook with an inventory, like the *ansible.cfg* file. However, if no hosts file is provided after all, the agent will most likely end up failing.

## What about the different scenarios?

The most straight scenario now would that that we have on lab with different clusters. In this case, the initial setup we'd go with is prefixed copies of the hosts and settings files for each lab.

An exception to this would be that we had several clusters, forcing us to have dedicated inventory files per cluster, but the scope of the testing would be the same for each cluster. In this case, we could simply have the default *settings.yml* file define in our configuration directory. This way, when running the agent, regardless of the cluster we indicate by the prefix, the agent will always default to the only settings file in the directory.

Another scenario would be where we have a single cluster, and different scopes of the tests we want to run. In this case, we would only need the *hosts* file, but then we'd create several copies fo the settings file and name them after the different scopes. For instance:

```
install-settings.yml
upgrade-settings.yml
```

A particular case for this scenario is where you have a default scope of testing and them some corner cases to test. In this case, we could just keep one non-prefixed copy of the settings file, and only create duplicates for the alternative test scenarios:

```
settings.yml
upgrade-settings.yml
```

Finally, you could use any combination of the scenarios above:

```
cluster1-install-hosts
cluster1-upgrade-hosts
cluster1-upgrade-settings.yml
cluster2-install-hosts
cluster2-upgrade-hosts
cluster2-upgrade-settings.yml
settings.yml
```

So, in the example above, both cluster1 and cluster2 share the settings file when installing OCP, but they'll use a different settings file when testing upgrades (for instance because they have a different upgrade path each).

## Some bonus tips

- Changing the config directory path

- Other commands that may use prefixes (dci-check-change).

- Using prefixes from queues: queues user the env var RES by default, by they can be instructed to set the prefix in the call to the test-runner instead
