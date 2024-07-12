Title: Certification with DCI on OpenShift Partner Labs (ROSA)
Date: 2024-07-17 10:00
Category: how-to
Tags: partners, certification, preflight, cnf, open-partner-labs
Slug: certification-with-dci-on-rosa
Author: Tatiana Krishtop, Yanai Gonzalez
Github: tkrishtop
Summary: In this article, we describe how to automate the certification process by running all required certifications in one batch: Preflight for containers, Preflight for operators, Chart Verifier for Helm charts, and CNF certification. The automation will be achieved with the help of DCI (Distributed CI) pipelines running on Open Partner Labs in ROSA.

[TOC]

# How-To: Certification with DCI

## What is Distributed CI

DCI stands for Distributed CI, a CI tool written in Ansible. It combines the advantages offered by CI and Ansible, enabling you to schedule the deployment of OCP clusters with multiple installers, automate the deployment of your plugins and workloads, and execute various tests seamlessly.

## Design Overview: DCI on OpenShift Partner Labs

DCI app-agent is tailored for deployment on a jumpbox—a RHEL machine with an NFR subscription and access to the OCP cluster via kubeconfig. The user operating DCI should possess local sudo permissions and administrative privileges within the cluster.

At OpenShift Partner Labs like ROSA (OCP on AWS), there isn't a dedicated jumpbox created by default. Instead, ROSA CLI is recommended for managing clusters.

To satisfy these needs, setting up a local RHEL8 Vagrant VM on your laptop with an NFR subscription serves as an ideal jumpbox solution. This jumpbox serves as a central hub for managing DCI workflows and integrating with ROSA clusters via locally-copied kubeconfig. Additionally, we configure DCI-queue to streamline certification jobs efficiently.

## Pipeline Overview: All Certification Flavors in One Config File

The core of DCI certification is a pipeline file that manages detailed configurations for all certification tests. There are four primary sections that we are going to use for the certification: preflight_containers_to_certify for container certification, preflight_operators_to_certify for operator certification, dci_charts and helmchart_to_certify to initiate Helm chart verification, and cnf_to_certify to establish CNF certification projects in Connect. 

### Preflight_containers_to_certify

        preflight_containers_to_certify:
          # run preflight check container tests
          - container_image: "quay.io/orga/image1@sha256:digest1"
          # run preflight check container tests
          # and submit the results to the existing cert project at Connect UI
          - container_image: "quay.io/orga/image2@sha256:digest2"
            pyxis_container_identifier: "ZZZZZZZZZZZZZZZZZZZZZZZ"
          # run preflight check container tests, 
          # create new certification project at Connect UI,
          # and submit the test results to this new project
          - container_image: "quay.io/orga/image3@sha256:digest3"
            create_container_project: true
            short_description: "Here is the default 50+ characters image description"
          # run preflight check container tests, 
          # create new certification project at Connect UI,
          # submit the test results to this new project,
          # and attach the project to the existing Product Listings  
          - container_image: "quay.io/orga/image3@sha256:digest3"
            create_container_project: true
            short_description: "Here is the default 50+ characters image description"
            pyxis_product_lists:
              - "XXXXXXXXXXXXXXXXXXXXXXXX"    
              - "YYYYYYYYYYYYYYYYYYYYYYYY"

The preflight_containers_to_certify section automates the preflight check container tests. In the example configuration above, we cover four common use cases. More information can be found in [this article](https://blog.distributed-ci.io/preflight-integration-in-dci.html#end-to-end-certification-of-container-images-with-dci) and the documentation: [preflight](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/preflight#certification-of-standalone-containers) role and [create_certification_project](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/create_certification_project#example-of-configuration-file) role in redhatci.ocp Ansible galaxy collection.

### Preflight_operators_to_certify 

        preflight_operators_to_certify:
          - bundle_image: "quay.io/rh-nfv-int/testpmd-operator-bundle:v0.2.9"
            # Mandatory for the connected environments.
            index_image: "quay.io/rh-nfv-int/nfv-example-cnf-catalog:v0.2.9"
            # Optional; provide it when you need to create
            # a new "Operator Bundle Image" and submit test results in it.
            create_operator_project: true
            # Optional; use it to open the certification PR automatically
            # in the certified-operators repository
            create_pr: true
            # Optional; use it to merge the certification PR automatically
            # in the certified-operators repository
            merge_pr: true

Similarly to standalone container certification, the preflight_containers_to_certify section, preflight_operators_to_certify handles running preflight check operator tests, submitting test results to an existing certification project in Connect or creating a new project and submitting test results there, as well as creating a pull request in the certified-operators repository. You can use all options at once or only part of the functionality. Detailed documentation can be found [here](https://github.com/redhatci/ansible-collection-redhatci-ocp/tree/main/roles/preflight#operator-end-to-end-certification).

### dci_charts and helmchart_to_certify 

        # run chart verifier tests and generate report.yaml
        do_chart_verifier: true
        partner_name: "MyNicePartnerName"
        partner_email: "example@example.me"
        dci_charts:
          - name: "my_nice_chart"
            chart_file: "path/to/my-nice-chart-1.2.3.tgz"
            deploy_chart: true

        # create cert project for the helm chart
        helmchart_to_certify:
          - repository: "https://github.com/orga/chartrepo"
            short_description: "Here is the default 50+ characters image description"
            chart_name: "my_nice_chart"
            create_helmchart_project: true
            pyxis_product_lists:
              - "YYYYYYYYYYYYYYYYYYYYYYYY"

While the same configuration manages both tests and the creation of certification projects for operators and containers, Helm charts have a separated approach: the [dci_charts](https://github.com/redhatci/ansible-collection-redhatci-ocp/blob/main/roles/chart_verifier/README.md?plain=1) section runs the chart verifier tests, and the [helmchart_to_certify](https://github.com/redhatci/ansible-collection-redhatci-ocp/blob/main/roles/create_helmchart/README.md?plain=1) section triggers the creation of the certification projects.

### Cnf_to_certify

# create cnf cert project

        cnf_to_certify:
          - cnf_name: "my-test23.5 OCP4.12.49"
            pyxis_product_lists:
              - "YYYYYYYYYYYYYYYYYYYYYYYY"

For CNF, we currently cannot automate much; we can only [create the vendor-validated project](https://github.com/redhatci/ansible-collection-redhatci-ocp/blob/main/roles/openshift_cnf/README.md?plain=1) in Connect.

# How-to: Demo

Let's now consolidate everything practically. Here is a [repository](https://github.com/dci-labs/certification-lab-config/tree/main) with an example setup for DCI-on-OPL certification, along with a [demo](https://www.youtube.com/watch?v=I3KaNEpy3PE&ab_channel=RedKrie) illustrating the exact setup process.
