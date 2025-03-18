Title: Creating custom catalog listing discontinued certified operator releases
Date: 2023-10-04 10:00
Category: howto
Tags: partners, operator, catalog
Author: Nacho Silla
Github: nsilla
Summary: A step-by-step guide on how to create a custom catalog source listing discontinued certified operator releases.

As new certified operators are published, the Red Hat OpenShift catalogs are updated to include these new operator versions.

When the operator upgrade path is honored, the new catalog versions allow you to access not only the latest operator version, but any other previous release conforming the upgrade path, so installing previous operator versions is as simple as defining the startingCSV field in the subscription specs.

However, sometimes the operator upgrade paths are broken, for instance, when old operator versions are not compatible with the OCP latest GA release. When this happens, the new catalogs omit all the operator old versions previous to the first supporting the current OCP GA version.

This may pose an inconvenience when you need to test a discontinued operator release on a cluster running an old OCP version still compatible with your target operator version.

In this guide you'll learn how to create a custom catalog image referencing your omited certified operator and how to use it to install the operator in your cluster.

## Requirements

- You must have the [operator-sdk](https://sdk.operatorframework.io/docs/building-operators/golang/installation/) tool installed and present in your system path.

- You must have the [OpenShift client (oc)](https://docs.openshift.com/container-platform/4.13/cli_reference/openshift_cli/getting-started-cli.html) installed and present in your system path.

- You must have a remote container image registry to push your resulting image to after building it, and pull it to create the catalog source.

- You must have a working set of credentials for connect.redhat.com

- You must know the URL of your operator bundle image as served by the Red Hat registry. You can retrieve it from [this site](https://catalog.redhat.com/software/containers/search).

- You must have an OCP cluster up and running to deploy the operator on.

- You must have access to the OCP cluster with the client tool, either by having the kubeconfig file placed in the default path or by setting the KUBECONFIG environment variable.

## Our Example scenario

Let's say you have an OCP 4.12 cluster where you want to deploy the Node Feature Discovery operator version 4.12.0.202308291001 which was recently replaced in the Red Hat Catalog by 4.12.0-202309181625.

For that we'll be using the bundle image stored in the Red Hat registry:

    registry.redhat.io/openshift4/ose-cluster-nfd-operator-bundle:v4.12.0.202308291001.p0.g3d08a74.assembly.stream-1

Once the custom index image is created we'll push it to our Quay.io repository with path and version tag:

    quay.io/nfd-tests/nfd-operator-index:v4.12.0.202308291001

## The direct way

Although this post is intended to show you how to create a custom catalog image and use it to install discontinued operators, it wouldn't be honest not to tell you there's a more direct way which under the hoods automates and runs the very same steps that will be described in the following sections.

Using the `operator-sdk run bundle` command you will achieve the same result with just one single instruction.

First, if needed, you have to log into the registry containing your bundle image.

For bundles served from the Red Hat registries, you must have an account at [the Red Hat Customer Portal](https://contact.redhat.com).

Red Hat maintains several registries depending on the nature of the images so, if you don't know in advance, you may need to browse the [Red Hat Container Catalog](https://catalog.redhat.com/software/containers/search) to locate the URL and registry hosting the images.

In our scenario the bundle and other images are hosted in registry.redhat.io, so to log in you have to do:

    $ podman login registry.redhat.io

Then you can run operator-sdk to create the catalog and deploy the operator with:

    $ operator-sdk run bundle -n nfd registry.redhat.io/openshift4/ose-cluster-nfd-operator-bundle:v4.12.0.202308291001.p0.g3d08a74.assembly.stream-1

Where:

- **-n nfd:** indicates the namespace where you want to have the operator installed.

- The last parameter is the URL to your discontinued operator bundle.

After a few minutes you can verify the operator was installed.

    $ oc get ip,csv -n nfd

This command should show both a CSV and an Install Plan for your operator's target version and the Install Plan should eventually change to status "Succeed".

## Creating the catalog image

If needed, log into the registries containing the bundle and where you'll place the custom index image:

    $ podman login registry.redhat.io
    $ podman login quay.io

Create your project directory

    $ mkdir ~/nfd-operator
    $ cd ~/nfd-operator

Initialize your project.

    $ operator-sdk init --domain my.domain.com --repo github.com/my-domain/nfd-operator
    Writing kustomize manifests for you to edit...
    Writing scaffold for you to edit...
    [...]

For a testing custom index as this is, the domain and repo values don't need to match real values, so you may stick to our example values or use the ones you prefer.

Edit the Makefile and set the following values:

**VERSION:** set it to your target version of the operator.

    VERSION ?= v4.12.0.202308291001

**BUNDLE_IMG:** set it to the URL of your certified operator bundle in registry.connect.redhat.com.

    BUNDLE_IMG ?= registry.redhat.io/openshift4/ose-cluster-nfd-operator-bundle:v4.12.0.202308291001.p0.g3d08a74.assembly.stream-1

**CATALOG_IMG:** set it to the URL of your catalog file as served from your remote registry.

    CATALOG_IMG ?= quay.io/nfd-tests/nfd-operator-index:v4.12.0.202308291001

Build and publish your catalog image:

    $ make catalog-build catalog-push

## Installing the discontinued operator version

Once the index is created and available on a reachable registry, you may configure your cluster to install your target operator release.

Create a catalog source. Make sure you set the right URL to your catalog image.

    $ cat > /tmp/catalog.yml << EOF
    apiVersion: operators.coreos.com/v1alpha1
    kind: CatalogSource
    metadata:
      name: nfd-operator
      namespace: openshift-marketplace
    spec:
      sourceType: grpc
      image: quay.io/nfd-tests/nfd-operator-index:v4.12.0.202308291001
      displayName: Custom NFD Operator Catalog
      publisher: myself
    EOF
    $ oc create -f /tmp/catalog.yml
    $ sleep 30
    $ oc describe catalogsource nfd-operator -n openshift-marketplace

Create a target namespace.

    $ oc create namespace nfd

Create an operator group.

    $ cat > /tmp/group.yml << EOF
    apiVersion: operators.coreos.com/v1
    kind: OperatorGroup
    metadata:
      name: nfd-operator
      namespace: nfd
    spec:
      targetNamespaces:
        - nfd
    EOF
    $ oc create -f /tmp/group.yml

Create a subscription.

    $ cat > /tmp/sub.yml << EOF
    apiVersion: operators.coreos.com/v1alpha1
    kind: Subscription
    metadata:
      name: nfd-operator
      namespace: nfd
      resourceVersion: "1"
    spec:
      channel: stable
      installPlanApproval: Automatic
      name: nfd-operator
      source: nfd-operator
      sourceNamespace: openshift-marketplace
    EOF
    $ oc create -f /tmp/sub.yml
    $ sleep 30
    $ oc describe sub nfd-operator -n nfd

Verify the operator was installed.

    $ oc get ip,csv -n nfd

This command should show both a CSV and an Install Plan for your operator's target version and the Install Plan should eventually change to status "Succeed".

## Final words

So, in this article we showed you two different ways of having a certified operator discontinued version installed in an OCP cluster.

The first method is more direct, but it can be seen as a wrapper that will automate the procedure described in the second method where we first create a custom catalog image out of the operator discontinued version bundle image, we push the catalog image to a registry accessible for our OCP cluster and then we configure the catalog source, subscription and other required objects in order to have the operator installed and running.

Both methods are valid, so it's up to you to decide which one accommodates the best to your testing scenario.
