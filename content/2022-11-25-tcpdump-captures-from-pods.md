Title: Troubleshoot pod traffic with nsenter and tcpdump tools
Date: 2022-11-25 10:00
Category: how-to
Tags: troubleshooting, networking, debug
Slug: troubleshoot-network-traffic-from-pods-with-tcpdump
Authors: Manuel Rodriguez
Github: manurodriguez
Summary: When a pod fails to contact another network resource logs might provide some hints, but sometimes the ultimate evidence of what is happening can be seen from a tcpdump capture, however not all pods have tcpdump tools or even a shell to interact with. This blog post demonstrates how to use certain tools available in openshift and GNU/Linux to overcome those challenges and use tcpdump captures to validate network traffic in pods deployed on top of Openshift clusters.


## Problem Statement

When you deploy a pod and the pod communicates with an internal or external network component, and for some reason it fails, taking a look to the logs could help, however sometimes you would like to see more details of the payload, if there is a TCP handshake, DNS resolution or understand the network flow, then you think "I can run a tcpdump capture to see where is the traffic going?". The next step is when you try to go into the pod and start running commands from a shell, but you find out that there is no shell at all, tools are not installed in the pod, or there is not enough privileges to do so.

    $ oc -n spk-dns46 get pods -o wide
    NAME                                   READY   STATUS    RESTARTS   AGE   IP            NODE
    spk-dns46-f5ingress-5cf6f6898d-bdcqx   2/2     Running   0          83s   10.129.2.20   worker-1

    # strike one
    $ oc -n spk-data exec spk-dns46-f5ingress-5cf6f6898d-bdcqx -c f5-lic-helper -it -- ip a
    ERRO[0000] exec failed: unable to start container process: exec: "ip": executable file not found in $PATH 
    command terminated with exit code 255

    # strike two
    $ oc -n spk-data exec spk-dns46-f5ingress-5cf6f6898d-bdcqx -c f5-lic-helper -it -- /bin/sh
    ERRO[0000] exec failed: unable to start container process: exec: "/bin/sh": permission denied 
    command terminated with exit code 255

    # strike three :(
    $ oc -n spk-data exec spk-dns46-f5ingress-5cf6f6898d-bdcqx -c f5-lic-helper -it -- /bin/bash
    ERRO[0000] exec failed: unable to start container process: exec: "/bin/bash": stat /bin/bash: no such file or directory 

The logs show a problem reaching rabbitmq-server.spk-utilities.svc.cluster.local service, and the "no such host" leads to a DNS problem, but can we see more from the network stack? 

    <pre>
    $ oc -n spk-dns46 logs spk-dns46-f5ingress-5cf6f6898d-bdcqx -c f5-lic-helper --tail 10 -f                                                                        
    I1117 00:48:24.075414       1 cm20.go:431] DEBUG: exchange name - CWC-SPK
    E1117 00:48:24.097314       1 rabbitmqapi.go:79] Failed to establish connection to rabbitmq server. Error dial tcp: lookup rabbitmq-server.spk-utilities.svc.cluster.local: no such host
    E1117 00:48:24.097329       1 rabbitmqapi.go:89] error: failed to open connection 
    E1117 00:48:24.097334       1 rabbitmqapi.go:105] error: failed to open channel
    I1117 00:48:24.097339       1 cm20.go:436] error: failed to setup exchange
    E1117 00:48:24.097350       1 rabbitmq_handler.go:38] Failed to create AMQP. Error Failed to Setup exchange: Failed to open channel
    </pre>

An option could be to try to perform the tcpdump capture in the other side (the DNS server) but if that is also not allowed, what options are left?

## nsenter to the rescue

nsenter is part of util-linux-core basic utilities and is available in CoreOS. This command allows to run commands inside namespaces:

    [core@worker-1 ~]$ rpm -qf $(which nsenter)
    util-linux-2.32.1-27.el8.x86_64

if you have access to the worker nodes via SSH, it's simple to use with sudo privileges, let's see an example to access the pod from the example above, located in worker-1

First, login to the worker node where the pod is running, and from there look for the the pod that you want to check.

    $ ssh core@worker-1
    [core@worker-1 ~]$ sudo crictl ps | grep f5-lic-helper
    2279b2951ca2f    17 minutes ago    Running    f5-lic-helper    0    db415107da15b

Then get the pod ID and inspect the pod content to retrieve the process ID (pid)

    [core@worker-1 ~]$ sudo crictl inspect --output yaml 2279b2951ca2f | grep 'pid' | awk '{print $2}'
    98611

Use nsenter and specify the pid with -t, and pass commands available in the host server to run inside the pod

    [core@worker-1 ~]$ sudo nsenter -n -t 98611 -- ip a
    ...
    3: eth0@if67: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 8900 qdisc noqueue state UP group default 
        link/ether 0a:58:0a:82:02:2a brd ff:ff:ff:ff:ff:ff link-netns 2b099085-6bc1-46a1-b31f-dab424e9afa3
        inet 10.130.2.42/23 brd 10.130.3.255 scope global eth0
           valid_lft forever preferred_lft forever
        inet6 fd02:0:0:7::2a/64 scope global 
           valid_lft forever preferred_lft forever
        inet6 fe80::858:aff:fe82:22a/64 scope link 
           valid_lft forever preferred_lft forever

If access to SSH is restricted, there is an alternative using the "oc debug" command to get access to the worker console, use "--image" option in a disconnected environment and specify the registry to use in /root/.toolboxrc

    $ oc debug node/worker-1 --image=registry.dfwt5g.lab:4443/rhel8/support-tools
    ...
    sh-4.4# chroot /host
    sh-4.4# vi /root/.toolboxrc
    REGISTRY=registry.dfwt5g.lab:4443

    sh-4.4# toolbox
    [root@worker-1 /]#

Then follow similar steps, look for the pod, inspect it and grep the PID, here "crictl" commands need to specify "chroot /host" before, and not all commands are available since we are running inside a toolbox image

    [root@worker-1 /]# chroot /host crictl ps
    [root@worker-1 /]# chroot /host crictl inspect --output yaml 2279b2951ca2f | grep 'pid' | awk '{print $2}'
    [root@worker-1 /]# nsenter -n -t 98611 -- ip a

## Get your tcpdump filter skills ready

In order to use tcpdump we'll require to login to the worker node using the "oc debug" command, since CoreOS has no tcpdump command installed, even in connected environments, only difference is that you might not have to specify the registry and the image to use.

Once logged into the toolbox you can run nsenter command and this time pass the tcpdump command, with the interface we listed previously with the nsenter command, storing the capture output is optional, just use a location where you have privileges to write, in this case "/host/var/tmp/", and finally you can leave your creativity and knowledge of tcpdump unleash to specify filters and inspect the traffic you want.

    [root@worker-1 /]# nsenter -n -t 98611 -- tcpdump -nn -i eth0 -w /host/var/tmp/f5-lic-helper_$(date +%d_%m_%Y-%H_%M_%S-%Z).pcap udp port 53
    tcpdump: listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes

In this capture we can see more details of the communication between the f5-lic-container pod and the rabbitmq service, we can see how it tries both ipv4 and ipv6 and the iteration of the domains until all possibilities are tried and the record is not found. It confirms it can reach the DNS service, the source and destination IP address, but the name is not found. Helpful to discard certain issues.

    00:51:38.680894 IP 10.129.2.20.33212 > 172.30.0.10.53: 20408+ A? rabbitmq-server.spk-utilities.svc.cluster.local.spk-dns46.svc.cluster.local. (93)
    00:51:38.680900 IP 10.129.2.20.33212 > 172.30.0.10.53: 20748+ AAAA? rabbitmq-server.spk-utilities.svc.cluster.local.spk-dns46.svc.cluster.local. (93)
    00:51:38.681427 IP 172.30.0.10.53 > 10.129.2.20.33212: 20748 NXDomain*- 0/1/1 (197)
    00:51:38.681441 IP 172.30.0.10.53 > 10.129.2.20.33212: 20408 NXDomain*- 0/1/1 (197)
    00:51:38.681465 IP 10.129.2.20.41183 > 172.30.0.10.53: 22208+ A? rabbitmq-server.spk-utilities.svc.cluster.local.svc.cluster.local. (83) 
    00:51:38.681468 IP 10.129.2.20.41183 > 172.30.0.10.53: 22453+ AAAA? rabbitmq-server.spk-utilities.svc.cluster.local.svc.cluster.local. (83)
    00:51:38.681923 IP 172.30.0.10.53 > 10.129.2.20.41183: 22453 NXDomain*- 0/1/1 (187)
    00:51:38.681941 IP 172.30.0.10.53 > 10.129.2.20.41183: 22208 NXDomain*- 0/1/1 (187)
    00:51:38.681954 IP 10.129.2.20.44139 > 172.30.0.10.53: 54593+ A? rabbitmq-server.spk-utilities.svc.cluster.local.cluster.local. (79) 
    00:51:38.681956 IP 10.129.2.20.44139 > 172.30.0.10.53: 54814+ AAAA? rabbitmq-server.spk-utilities.svc.cluster.local.cluster.local. (79)
    00:51:38.682265 IP 172.30.0.10.53 > 10.129.2.20.44139: 54593 NXDomain*- 0/1/1 (183)
    00:51:38.682284 IP 172.30.0.10.53 > 10.129.2.20.44139: 54814 NXDomain*- 0/1/1 (183)
    00:51:38.682297 IP 10.129.2.20.52085 > 172.30.0.10.53: 3660+ A? rabbitmq-server.spk-utilities.svc.cluster.local.cluster4.dfwt5g.lab. (85) 
    00:51:38.682299 IP 10.129.2.20.52085 > 172.30.0.10.53: 3879+ AAAA? rabbitmq-server.spk-utilities.svc.cluster.local.cluster4.dfwt5g.lab. (85)

## To be continued...

Not everything can be proved with tcpdump captures, but having the option to use them to confirm certain aspects of the communication between two resource is helpful. In the future well talk more about network traffic flows, ovs and how to find out where the traffic is getting lost.