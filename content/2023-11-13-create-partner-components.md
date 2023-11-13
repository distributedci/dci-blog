Title: How to create partner components
Date: 2023-11-13 11:00
Category: overview
Tags: dci, components, partner
Author: Yassine Lamgarchal
Github: ylamgarchal
Summary: As a partner, creating your own DCI components is very usefull to enrich the context of your jobs in order to help you doing
post-mortem analysis.

One of the key benefits of using the DCI tooling is the ability to combine Red Hat products and partners' products altogether in one job. The DCI components are one of the ways to enrich the context of a job in order to have a better understanding of what happened. Indeed, when a job is scheduled, multiple components might be attached to it. They come from either Red Hat or partners. In this article we are going to explore all the ways to create components.

## The Red Hat components

Those components are the ones provided by Red Hat and correspond to the Red Hat products like Openshift and RHEL. The DCI backend is in charge to create them and synchronize their data when needed. A job is always attached to at least one Red Hat component.

OCP example:
```
{
    "component": {
    "created_at": "2023-11-08T06:38:56.425952",
    "name": "OpenShift 4.15 nightly 2023-11-07 23:39",
    "released_at": "2023-11-07T23:39:40",
    …,
    …,
    "state": "active",
    "team_id": null,
    "topic_id": "88b0653c-ed2b-4d8d-acd1-cd8e7125ef98",
    "type": "ocp",
    "version": "4.15.0-0.nightly-2023-11-07-233748"
    }
}
```
The “team_id" field is not set, it means that this component is available to all teams.


## The partner components

On top of the Red Hat components, the partners can also create their own components which are isolated to their own team. For example, a partner wants to continuously test his product against the OCP nightlies in order to be ready when a new Openshift version is released. Partners have multiple possibilities to create components.

### Components attached to a topic

Let's say, as a partner, you are developing an Openshift Operator that is only working with a specific OCP minor version. For example, it could be OCP 4.15. In this case you can create a component of your operator that is attached to the topic OCP 4.15. After this operation you can attach your component to your future jobs.

To create this component, you can use the dcictl CLI as below:

Get the team id of your remoteci:
```
$ source your-remoteci.rc.sh
$ REMOTECI_TEAM_ID=$(dcictl --format json remoteci-list --where name:yassine-remoteci | jq .remotecis[0].team_id)
```

Get the topic id:
```
$ TOPIC_ID=$(dcictl --format json topic-list --where name:OCP-4.15 | jq .topics[0].id)
```

Create the component:
```
$ dcictl --format json component-create --type my-cni --topic-id ${TOPIC_ID} --team-id ${REMOTECI_TEAM_ID} --tags staging-ok,platform-x86_64 --url http://myregistry.com/my-operator --version 1.0 my-operator
{
    "component": {
    "id": "a115d5f9-4688-48ae-8d11-1fb18491f96f",
    "name": "my-operator",
    "tags": [
        "staging-ok",
        "platform-x86_64"
    ],
    "team_id": "f0c1160e-5bbf-4fdb-b0cc-cc19dba04c37",
    …,
    …,
    "topic_id": "c7d2f7b6-8393-4a2c-a92c-7538f54a3d32",
    "type": "my-cni",
    "url": "http://myregistry.com/my-operator",
    "version": "1.0"
    }
}
```

### Components attached to a product

These components are created when you develop a product that is working on all major versions of the Red Hat products. For example, your product is working on all RHEL versions (6, ..., 9). In this case, you don’t need to create the same component in all the topics but instead you create only one component that will be attached to the product.

Get the product id:
```
PRODUCT_ID=$(dcictl --format json product-list --where name:RHEL | jq .products[0].id)
```

Create the component:
```
$ dcictl --format json component-create --type my-awesome-product --product-id ${PRODUCT_ID} --team-id ${REMOTECI_TEAM_ID} --tags staging-ok,platform-x86_64 --url http://myawesomeproduct.com/v1.0-nightly --version 1.0 my-awesome-product
{
    "component": {
        "id": "727f4c66-50da-43e7-83b7-dc6ed7382f1d",
        "name": "my-awesome-product",
        "tags": [
            "staging-ok",
            "platform-x86_64"
        ],
        “team_id”: “6fdf13ea-9ca9-466f-9c7f-d843afca15f0”
        …,
        …,
        “product_id”: “d29d417d-6f2b-4b10-a032-17540f877be5”,
        "type": "my-awesome-product",
        "url": "http://myawesomeproduct.com/v1.0-nightly",
        "version": "1.0"
    }
}
```

As a best practice, we do recommend you to create your components as soon as they are released on your side in order to test your latest version with the latest version of the Red Hat products.

### Components created at job runtime

Sometimes, your agent needs to install other dependencies before doing the actual work. Those dependencies might be rpms packages or git repositories. In the dci-{openshift, rhel}-agent we provide an Ansible role “include_components” to create those components.

For example:
```
- name: Include installed software as components
  vars:
    mandatory_rpms:
      - ansible
      - dci-ansible
      - dci-openshift-agent
      - dci-pipeline
      - python3-dciclient
      - python3-kubernetes
      - python3-openshift
    ic_rpms: "{{ (dci_rpms_to_components + mandatory_rpms)|flatten }}"
    ic_gits: "{{ dci_gits_to_components|flatten }}"
    ic_dev_gits: "{{ dev_gits_to_components|flatten }}"
  include_role:
    name: redhatci.ocp.include_components
```

In this example, we can track the version of Ansible, the version of some DCI packages and others. This will help you to troubleshoot an issue when a job that was running fine before is failing because some dependencies have been updated and introduced regressions.  You can check more information about this role at https://galaxy.ansible.com/ui/repo/published/redhatci/ocp/content/role/include_components.

We also provide an Ansible Action plugin that intercept the Ansible git module calls in order to create transparently a component.

Example of a git clone in a playbook:
```
- name: "Clone/update assisted-deploy repo"
  vars:
    git_repo: "{{ assisted_deploy_repo }}"
    git_ref: "{{ assisted_deploy_version }}"
  git:
    version: "{{ git_ref }}"
    repo: "{{ git_repo }}"
    dest: "{{ dci_cache_dir }}/assisted_deploy_repo"
    force: true
```

This will result to the creation of the following component:
```
{
    "component": {
        "created_at": "2023-11-10T09:58:57.857559",
        "id": "748d0ccb-a52b-4c8b-bcb9-5598691446fb",
        "name": "crucible fd87c9c",
        "released_at": "2023-11-10T09:58:57.858231",
        "team_id": "8ca46495-b738-4848-af49-74ab33f7a1aa",
        "topic_id": "7c843073-1c58-4397-bfe5-64ef132c827a",
        ...,
        ...,
        "type": "crucible",
        "uid": "fd87c9cd8720532dde06e3c3be011463d3f3c3a0",
        "updated_at": "2023-11-13T07:41:00.756913",
        "url": "https://github.com/redhat-partner-solutions/crucible/commit/fd87c9cd8720532dde06e3c3be011463d3f3c3a0",
        "version": "fd87c9c"
    }
}
```

## Conclusion

In this article we covered the ways offered to you for the creation of your own DCI components. We recommend creating components when there are important dependencies that can impact the result of your jobs. The DCI tooling is very versatile and can be used in your automation in multiple ways, you can check out more information about automation in this DCI article https://blog.distributed-ci.io/automate-dci-components.html
