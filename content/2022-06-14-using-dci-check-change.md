Title: Using dci-check-change to test your changes
Date: 2022-06-14 10:00
Category: how-to
Tags: dci-openshift-agent, developers
Slug: using-dci-check-change-to-test-your-changes
Authors: Bill Peck
Summary: The dci-openshift-agent is complex and any code changes could potentially break it.  It's important that all code changes are tested.  Since there are multiple ways to install OpenShift using the dci-openshift-agent it may take several test runs to properly verify.  This blog post summarizes the different ways and environments used to test your code.


## Introduction

OpenShift is a large and complicated piece of software that by nature involves multiple systems.  The dci-openshift-agent is written to help test this but it itself is also large and complicated.  It became pretty clear early on that we needed a way to test the test code.  With mutliple developers and with so many different ways to configure and deploy OpenShift it is imperitive that we have a reproducible way to test the agent.

## Automatic checks

Everytime you push a review to gerrit it will trigger an automated check unless your review is marked as "Work in Progress".  The default check will test your change in a virtualized environment using the default IPI install type.  Depending on how many other reviews are in process it may be a while before your review is tested.  You will know your review is currently running when you see this comment from the dci-ci-bot:

![alt_text]({filename}/images/2022-06-03-using-dci-check-change-gerrit-started-check.png)
<center>Starting dci-check-change job.</center>

After the test completes there will be an additional comment stating if the CI job was Successful or Failed.  For both Success and Failure you will normally have a link to the job execution in DCI.  This will allow you to investigate the results in more detail if the job failed or you simply want to look closer at the results.

![alt_text]({filename}/images/2022-06-03-using-dci-check-change-gerrit-success.png)
<center>dci-check-change SUCCESS tested on libvirt:assisted</center>

The exception to this is if the CI job fails in the pre-run stage.  This means we had a failure before we even schduled the job in the DCI control server.  For these failures you will need to log into the server running the CI jobs and investigate further.

![alt_text]({filename}/images/2022-06-03-using-dci-check-change-gerrit-pre-run-failure.png)
<center>dci-check-change pre-run : FAILURE tested on libvirt:assisted</center>

### Voting

All of the jobs executed from the ci environment are voting in gerrit.  You will need a +1 from dci-ci-bot in order to merge your review.  Failures will vote -1.

## Manual checks

You can manually run dci-check-change as well.  If your fix is for an issue a partner reported you can have them verify the pull request in their lab using their cluster config.  You may also want to run the pull request in your devel environment.  This is especially handy if your change doesn't work as expected since you will still have the environment for inspection.

Setting up a devel environment is covered by this blog post [Setting up a devel environment for DCI Openshift](https://blog.distributed-ci.io/settings-up-a-devel-environment-for-dci-openshift.html).

When running manually dci-check-change will use the inventory and settings from /etc/dci-openshift-agent.  You should verify that your environment works using the regular dci-openshift-agent-ctl first.

```console
dci-check-change -f 24446
```

This will look for PR 24446 from gerrit and check out the changeset locally and run using your local inventory and settings.

The -f forces it to run even if you have given your PR a no-check hint, more on that below.

### Hints

We mentioned in the Introduction that there are multiple ways to install OpenShift and the dci-openshift-agent supports some of these.  It can be helpful to provide a hint in your review that lets the CI system know to use a different install type.  For example, if your change pertains to SNO then it makes sense to set the  to SNO.  This way that install type will be used and your code changes will get covered.

Here is an example of setting multiple hints, Test-Hints, Args and Dependencies from both Gerrit and Github.

An example commit message with hints.
```
Initial work for supporting Assisted Installer

Test-Hints: assisted
Test-Args: -i alternate_inventory.yml
Depends-On: 123423
Depends-on: https://github.com/redhat-cip/dci-openshift-app-agent/pull/1
```

You can also tell the automated CI to ignore your pull request if it's not ready for testing yet.

```
Test-Hints: no-check
```

As mentioned in the previous section you can still run dci-check-change manually with the -f option.

[See the Development docs for all the hints that are supported](https://docs.distributed-ci.io/dci-openshift-agent/docs/development/#advanced)

## Summary

I hope this blog entry will help you get the most out of the CI system.  Giving you confidence in your code changes and being able to easily test large potentially breaking code changes.  Having the flexibility to manually trigger the same CI run in your development environment assures that when you remove that "Work in Progress" marker you will have high confidence that it will pass.

---
