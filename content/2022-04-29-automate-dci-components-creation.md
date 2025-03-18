Title: How to automate DCI components creation
Date: 2022-04-29 10:00
Modified: 2022-09-30 10:00
Category: how-to
Tags: introduction, dci, git, github, github-actions, ci, components, OpenShift, OCP
Slug: automate-dci-components
Author: Tony Garcia
Github: tonyskapunk
Summary: Components are the artifacts used in a DCI job, these are the elements that distinguish jobs. They are the elements to be tested on each job. This post will discuss their use and an example of how to automate them to be continuously tested.

## What is a component?

A component is an artifact (file, package, URL, etc.) attached to a topic. An agent takes components in its workflow. Components are immutable and should be regularly created with newer versions of the artifact.

In DCI, we have some basic components that are constantly created with new versions; this is part of the work made by the feeder. The feeder is a service that takes care of watching for newer versions/releases of different components. For example, the versions of the OpenShift Container Platform (OCP), latest, release candidates, or nightly builds.

Components are not limited to the DCI creation through its feeder. Partners or individuals using DCI can create their components to represent that element/artifact they want to test in a job, so a job has context.

## What are the components used for?

Primarily, they provide the specific version of a product, for example, a particular RHEL version or a release candidate of OCP. Additionally, components offer the link of elements that are tested or validated in a job.

Let's see an example of how a component could be used.

Say you have an operator and would like to test it on all the supported versions of OCP. If you're new to DCI, most likely, the first thing you would like to do is to run a job on top of a version your operator works as expected; this way, you could have a baseline and compare the results when using other versions of OCP.

To deploy a particular version of OCP, you could leverage our [dci-openshift-agent](https://docs.distributed-ci.io/dci-openshift-agent/). Then to deploy your operator and your tests, you could use our [dci-openshift-app-agent](https://docs.distributed-ci.io/dci-openshift-app-agent/). Finally, you could repeat the same process for other versions of OCP and then compare each Job to determine their differences and potential issues. However, even though doing this works, the more you repeat, the harder it is to track those differences.

If we have created a component for the operator to be tested, it would be easier to compare jobs between different versions of OCP or even different versions of the same operator.

Here we have the same component version run in two different topics:

- OCP-4.10

  ![Table with three sections: number of jobs, percentage of successful jobs, and the latest run. Underneath a list of jobs with their name, status, tags, duration, and time of creation]({static}/images/2022-04-29-automate-dci-components-creation/component_ocp-4.10-v029.png)

- OCP-4.11

  ![Table with three sections: number of jobs, percentage of successful jobs, and the latest run. Underneath a list of jobs with their name, status, tags, duration, and time of creation]({static}/images/2022-04-29-automate-dci-components-creation/component_ocp-4.11-v029.png)

Now, here we have the same component but of an older version and an older version of OCP

![Table with three sections: number of jobs, percentage of successful jobs, and the latest run. Underneath a list of jobs with their name, status, tags, duration, and time of the creation]({static}/images/2022-04-29-automate-dci-components-creation/component_ocp-4.7-v027.png)

## Why should I care about components?

In the previous sections, we mentioned that components provide context to a job. We also offered an example of how the components are used. The benefit of using a component is differentiating jobs by component versions and thus pinning the exact version of the tested software.

Additionally, using components could help with the generation of a compatibility matrix between OCP versions and the different components and their versions used by a partner.

If you're using DCI, and you're using it to test your operator, your driver, your application, you name it. Then you should use a component for it.

## How to create a component?

Creating a component is relatively easy with the help of the [python-dciclient](https://docs.distributed-ci.io/python-dciclient/) package.

### Tool installation

Install repositories:

    source /etc/os-release
    dnf -y install epel-release
    dnf -y install https://packages.distributed-ci.io/dci-release.el${VERSION}.noarch.rpm

Install package:

    dnf -y install python3-dciclient

### Creation

1. Obtain the remoteCI from <https://www.distributed-ci.io/remotecis>, save its content, and source it

<pre>
source myremoteci.sh
</pre>

1. Create the component using `dci-create-component` tool:

<pre>
dci-create-component \
  --format json \
  OCP-4.11 "my awesome operator" v1.2.3 ga
</pre>

### Example

In this example, we are creating a component called "FredCo dci operator" on a release candidate version v1.2.3-rc1:

    $ dci-create-component --format json OCP-4.10 "FredCo dci operator" v1.2.3-rc1 candidate
    {
        "component": {
            "canonical_project_name": "Fredco Dci Operator v1.2.3-rc1",
            "created_at": "2022-12-23T00:11:22.00000",
            "data": {},
            "etag": "a0b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
            "id": "87654321-dcba-cdef-2109-dcba0987654321",
            "message": null,
            "name": "v1.2.3-rc1",
            "state": "active",
            "tags": [
                "build:candidate"
            ],
            "team_id": "12345678-abcd-fedc-9012-34567890abcd",
            "title": null,
            "topic_id": "",
            "type": "fredco-dci-operator",
            "updated_at": "2022-12-23T00:11:22.00000",
            "url": null
        }
    }

## How to automate component creation releases?

The automation should live in the release process of your component; this is usually your CI. It could be in a GitHub Action, a Jenkins pipeline, etc.

Ideally, the creation of a component should occur before it is released. Every time a new version of your software is ready, `dci-create-component` tool could automatically create a component for further testing with DCI

In this repository: <https://github.com/rh-nfv-int/nfv-example-cnf-index>, we create a catalog (an image with multiple operator bundles inside). Then, when we release a new version of that catalog, we automatically create new components in all the OCP topics. Later, we use the newly created component through the DCI agent to validate it's working as expected.

In this catalog repository, we use GitHub actions to create the components during release time. Here is the link to the code that takes care of this: <https://github.com/rh-nfv-int/nfv-example-cnf-index/blob/master/.github/workflows/quay.yml>

### Automation of components creation through GitHub Actions

A GitHub Action is available to help with the component creation. It could be either during the creation of a PR, the release of the artifact, or as needed.

The documentation on how to use this particular GitHub Action is available in the marketplace: <https://github.com/marketplace/actions/dci-component>

## Summary

Components are quite important as they represent a change or a version of an artifact being tested or validated. See this example, where the component selected is OCP. The graph shows the success rate for the different versions of that component.

![Table showing multiple versions of OpenShift 4.11, with the tags used for each component, the percentage of successful jobs, the failures/successes in the last few weeks, and a link to the jobs of each component]({static}/images/2022-04-29-automate-dci-components-creation/ocp_4.11.png)

As a Red Hat partner, verifying that the upcoming product versions will work as expected is essential. DCI provides a way to verify the integration of the upcoming product and the partner's components.

Finally, we understand your components and our products are not released simultaneously. Thus it is crucial to automate the creation of the component, so it keeps being continuously verified each time there's a new release or a change in your components.

---
