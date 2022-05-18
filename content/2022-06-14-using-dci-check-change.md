Title: Using dci-check-change to test your changes
Date: 2022-06-14 10:00
Category: how-to
Tags: dci-openshift-agent, developers
Slug: using-dci-check-change-to-test-your-changes
Authors: Bill Peck
Summary: The dci-openshift-agent is complex and any code changes could potentially break it.  It's important that all code changes are tested.  Since there are multiple ways to install OpenShift using the dci-openshift-agent it may take several test runs to properly verify.  This blog post summarizes the different ways and environments used to test your code.


## Introduction

OpenShift is a large and complicated piece of software that by nature involves multiple systems.  The DCI openshift agent is written to help test this but it itself is also large and complicated.  It became pretty clear early on that we needed a way to test the test code.  With mutliple developers and with so many different ways to configure and deploy openshift it is imperitive that we have a reproducible way to test the agent.

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

The Automatic checks are great and for most of your PR's you may never need anything more.
But if you are working on a large change that is likely to break things you may want to test it first in your devel environment.  Especially since there are finite resources to handle the automatic checks and no one wants to needlessly block other jobs.  Setting up a devel environment is covered by this blog post [Setting up a devel environment for DCI Openshift](https://blog.distributed-ci.io/settings-up-a-devel-environment-for-dci-openshift.html).

Once you have your devel environment setup you could copy the changes from your PR to the devel environment and run it manually.  But there is a better way.  You will still push your changes to gerrit and use the dci-check-change command directly from your devel environment.

But there is a trick before you push your PR to keep the automatic check from triggering.  If your PR is marked as "Work in Progress" in gerrit then the automatic checks won't pay attention to it.  So the trick is to set this right from the git push.

```console
$ git push gerrit MY_BRANCH:refs/for/master%wip

Enumerating objects: 7, done.
Counting objects: 100% (7/7), done.
Delta compression using up to 8 threads
Compressing objects: 100% (4/4), done.
Writing objects: 100% (4/4), 1.66 KiB | 1.66 MiB/s, done.
Total 4 (delta 2), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (2/2)
remote: Processing changes: refs: 1, new: 1, done
remote:
remote: SUCCESS
remote:
remote:   https://softwarefactory-project.io/r/c/dci-openshift-agent/+/24446 Add Assisted Installer [NEW]
remote:
To ssh://softwarefactory-project.io:29418/dci-openshift-agent.git
 * [new reference]   master -> refs/for/master
```

Use the PR number that gerrit gave from pushing the PR to run dci-check-change directly from your devel environment

```console
$ dci-check-change 24446
```

Once your PR passes in your devel environment remove the "Work in Progress" by either editing the PR in the gerrit UI or use the following syntax in your git push

```console
$ git push gerrit MY_BRANCH:refs/for/master%ready
```

### Hints

We mentioned in the Introduction that there are multiple ways to install OpenShift and the DCI agent supports some of these.  It can be helpful to provide a hint in your review that lets the CI system know to use a different install type.  For example, if your change pertains to SNO then it makes sense to set the  to SNO.  This way that install type will be used and your code changes will get covered.

Here is an example of setting multiple hints, Test-Hints, Args and Dependencies from both Gerrit and Github.

```
Initial work for supporting Assisted Installer

Test-Hints: assisted
Test-Args: -i alternate_inventory.yml
Depends-On: 123423
Depends-on: https://github.com/redhat-cip/dci-openshift-app-agent/pull/1
```

[See the Development docs for all the hints that are supported](https://docs.distributed-ci.io/dci-openshift-agent/docs/development/#advanced)

## Summary

I hope this blog entry will help you get the most out of the CI system.  Giving you confidence in your code changes and being able to easily test large potentially breaking code changes.  Having the flexibility to manually trigger the same CI run in your development environment assures that when you remove that "Work in Progress" marker you will have high confidence that it will pass.

---
