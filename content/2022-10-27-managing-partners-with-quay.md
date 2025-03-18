Title: Why using Quay for CI lab?
Date: 2022-10-27 09:30
Category: Quay
Tags: ansible, OCP, containers
Slug: managing-partners-with-quay
Author: Charles Caporali
Github: capolrik
Summary: Using the features of Quay to handle Access Management

[TOC]

## Overview

Dallas Lab has a particular case regarding connectivity. The different clusters are running in disconnected mode, which means the OCP installed does not have access to the internet. This simple statement requires a lot of work of mirroring for correct behavior. All external resources like binaries and container images must be mirrored for having them available when installing or just deploying a workload on OCP.

On the matter of the container images, the most naive way of dealing with mirroring is to think of pulling all the images needed directly on all nodes. This method has the advantage of being simple to implement. At the beginning of the CI project in Dallas, there was an Ansible automation to copy the images needed on all nodes of the cluster. But this method has many downsides: it is slow because every image needs to be copied on every node and you need to mirror all the images in advance so you cannot dynamically add a set of images for a specific workload. So this solution was not enough for the use case of the Dallas Lab. That is where Quay is coming on the stage!

## Why use Quay?

On the jumpbox of the Dallas Lab (an entrypoint server to the Lab), a private Quay registry has been created to handle the images needed for OCP use cases. It comes with the advantages of chosing an open-source technology and a web UI which is always convinient for partners. In addition, the extensible API, the vulnerability scanning, and the repository Mirroring features are very useful extras that help with the maintenance of the lab.
Why not using the built-in repository of OCP? Because of the CI system used in Dallas, clusters are doing a fresh install several times a day, which means clearing the built-in registry at each install. Always keeping the registry up to date with all the images from all the different partners is too complex to keep this solution.

## Multitenancy and namespaces for access management

Quay allows a more advanced access management by the usage of organizations.

![quay_accesses]({static}/images/2022-10-27-managing-partners-with-quay/quay_accesses.png)
_Fig. 1. Accesses inside a Quay Organization._

In the use case of Dallas, several teams need to access the same Quay registry but it does not mean all images must be accessible by anyone in the Lab. That’s where Organizations can help: by creating one specific organization by partner with its own user. Every member of a partner’s team can have a user who has privileged rights in its organization, like pulling, pushing or deleting a container image. Automated tasks can be handled at the organization level by a Robot account. It does not only improve the overall maintainability of the registry, but it also makes partners autonomous in the management of their own images without waiting for the input of the admin for all the maintenance tasks. In the official Quay doc, there is a [complete guide](https://access.redhat.com/documentation/en-us/red_hat_quay/3.7/html/use_red_hat_quay/use-quay-manage-repo#allow-access-org-repo) on how to configure access in organization repositories.

The separation inside the Quay registry allows the privacy of everyone's container images and also makes the usage of shared images, like the one needed for the installation of OCP, very smooth. For the CI jobs, all images are accessible by a specific Robot account which is dedicated to Dallas automation.

In addition, a quota can be put in place at the organization level to prevent the registry to be out of storage. With the quota reporting, users can track the storage consumption of their assigned organization and the superuser can define the hard limit which prevent users from pushing to the registry when storage consumption reaches the configured limit.
These option improves the maintainability of the registry and is simple to set up. To enable quota management, set the feature flag in your config.yaml to true:

    :::shell-session
    FEATURE_QUOTA_MANAGEMENT: true

## Advanced features

This blog post is only covering a fraction of the all features provided by Quay. There are a lot of options available regarding scalability, git integration, or security. As an example, the security scanning rates (see the [Clair project](https://github.com/quay/clair) the images according to the vulnerabilities found inside it. Also, the tag expedition system allows the automatic cleanup of obsolete images: when an image has no tag or when the tag is expired, it is set to be deleted and will be garbage collected.

Many of the features of Quay have been useful inside the disconnected Dallas Lab, it is one of the big strengths of this open-source project. With its active development cycle, Quay gots you covered in a very large variety of situations: it starts with the basic functions of a container registry and then can lead you to build automation, easy logging, and auditing integration, and an advanced access control for the users and the list goes on.
