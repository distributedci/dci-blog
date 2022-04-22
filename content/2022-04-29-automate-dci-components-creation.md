Title: How to automate DCI components creation
Date: 2022-04-29 10:00
Category: how-to
Tags: introduction, dci, git, github, github-actions, ci, components, OpenShift, OCP
Slug: automate-dci-components
Authors: Tony Garcia
Summary: Components are the artifacts used in a DCI job, these are the elements that distinguish jobs. They are the elements to be tested on each job. In this post, we will discuss what they are, what they are used for, and an example of how to automate them to be continuously tested.

## What is a component?

A component is an artifact (file, package, URL, etc.) attached to a topic. An agent takes components in its workflow. Components are immutable and should be regularly created with newer versions of the artifact.

In DCI, we have some basic components that are constantly created with new versions, this is part of the work made by the feeder. The feeder is a service that takes care of watching for newer versions/releases of different components.  For example, the versions of the OpenShift Container Platform (OCP), latest, release candidates, or nightly builds.

Components are not limited to the DCI creation through its feeder. Partners or individuals using DCI can create their components to represent that element/artifact they want to test in a job. Through a component a job has context.

## What are the components used for?

Primarily, they provide the specific version of a product, for example, a particular RHEL version or a release candidate of OCP. Additionally, components provide the link of elements that are tested or validated in a job.

Let's see an example of how a component could be used.

Say, you have an operator and would like to test it on all the supported versions of OCP. If you're new to DCI, most likely the first thing you would like to do is to run a job on top of a version your operator works as expected, this way you could have a baseline and compare the results when using other versions of OCP.

To deploy a particular version of OCP you could leverage our [dci-openshift-agent](https://docs.distributed-ci.io/dci-openshift-agent/). Then to deploy your operator and your tests you could use our [dci-openshift-app-agent](https://docs.distributed-ci.io/dci-openshift-app-agent/).

You could repeat the same process for the other versions of OCP and then compare each Job to figure out the differences and any potential issues between them. Even though doing this works, the more you repeat, the harder it is to track those differences.

If we have created a component for the operator to be tested, it would be easier to compare jobs between different versions of OCP or even different versions of the same operator.

Here we have the same component version run in two different topics:

- OCP-4.10

    ![Table with three sections: number of jobs, percentage of successful jobs, and the latest run. Underneath, a list of jobs with their name, status, tags, duration, and time of creation]({static}/images/component_ocp-4.10-v029.png)

- OCP-4.11

    ![Table with three sections: number of jobs, percentage of successful jobs, and the latest run. Underneath, a list of jobs with their name, status, tags, duration, and time of creation]({static}/images/component_ocp-4.11-v029.png)

Now, here we have the same component but of an older version and an older version of OCP

![Table with three sections: number of jobs, percentage of successful jobs, and the latest run. Underneath, a list of jobs with their name, status, tags, duration, and, time of creation]({static}/images/component_ocp-4.7-v027.png)

## Why should I care about components?

In the previous sections, we mentioned that components provide context to a job. We also provided an example of how the components are used. From there it is clear that the benefit of using a component is to differentiate jobs that will have different versions of components. Then, in continuous integration, it's important to have a clear way to differentiate job executions to know what was tested against what.

Additionally, the use of components could help with the generation of a compatibility matrix, between OCP versions and the different components and their versions used by a partner.

If you're using DCI, and you're using it to test your operator, your driver, your application, you name it. Then you should use a component for it.

## How to create a component?

Creating a component is quite easy with the help of the [python-dciclient](https://docs.distributed-ci.io/python-dciclient/) package. Available either as an RPM or a python library through PyPI.

### Installation

#### RPM

Install repositories:

```Shell
source /etc/os-release
dnf -y install epel-release
dnf -y install https://packages.distributed-ci.io/dci-release.el${VERSION}.noarch.rpm
```

Install package:

```Shell
dnf -y install python3-dciclient
```

#### PYPI

```Shell
$(type -p pip3 pip | head -1) install --user --upgrade dciclient
```

### Creation

1. Obtain the remoteCI from <https://www.distributed-ci.io/remotecis>, save its content, and source it  

    ```Shell
    source myremoteci.sh
    ```

1. Get remoteCI Team ID:

    ```Shell
    TEAM_ID=$( dcictl --format json team-list |  
        jq -r '.teams[] | select(.name == "my-team-name") | .id' )
    ```

1. Get the Topic ID where you want to create the component, for example, "OCP-4.10":

    ```Shell
    dcictl \  
        –format json \  
        topic-list \  
        --where "name:OCP-4.10" |  
    jq -r '.products[].id' )
    ```

1. Create the component

    ```Shell
    dcictl \  
      --format json \  
      component-create \  
      --topic-id ${TOPIC_ID} \  
      --team-id ${TEAM_ID} \  
      --name 'v1.2.3' \  
      --canonical_project_name 'My Awesome Operator v1.2.3' \  
      --type "operator" |  
    jq .
    ```

## How to automate components creation releases?

The automation should live in the release process of your component, this is usually your CI, it could be in a GitHub Action, a Jenkins pipeline, etc.

Ideally, the creation of a component should occur at the time a new version of your component is going to be created or published, but it can be created as well once it has been released. Once a new version of your component is ready, a step should be introduced to create this component using the python-dciclient to later use a DCI agent and test it.

In this repository: <https://github.com/rh-nfv-int/nfv-example-cnf-index> we create a catalog (an image with multiple operator bundles inside). When we release a new version of that catalog, we create a new component in multiple topics, in this case in multiple versions of OCP. Later, we use the new component through the DCI agent to validate its working as expected.

In this catalog repository, we make use of GitHub actions to create the components during release time, here is the link to the code that takes care of this: <https://github.com/rh-nfv-int/nfv-example-cnf-index/blob/master/.github/workflows/quay.yml>

### Automation of components creation through GitHub Actions

A GitHub Action has been created to help with the step of creating the component during a particular time, this could be either during the creation of a PR, the release of the artifact, or as needed.

The details and documentation on how to use this particular GitHub Action can be found here: <https://github.com/tonyskapunk/dci-component>

## Summary

Components are quite important as they represent a change or a version of an artifact that is being tested or validated.
As a Red Hat partner, it is not only important to verify the upcoming versions of a product are going to work in my use case, but to verify the integration of the upcoming product and my components.

Finally, we understand your components and our products are not released at the same time. Thus it is important to automate the creation of the component so it keeps being continuously verified each time there's a new release or a change in your components.
