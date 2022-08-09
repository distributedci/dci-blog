Title: Naming capabilities for DCI jobs
Date: 2022-09-16 07:00
Category: how-to
Tags: dci
Slug: naming-for-dci-jobs
Author: Frédéric Lepied
Github: fredericlepied
Summary: Good practices in naming for DCI jobs

[TOC]

## Introduction

Following good practices in naming for your DCI jobs will help you visualize your jobs in the DCI User Interface and easily search them. It will also ease the creation of meaningful dashboards (See [How to build your own DCI dashboard](how-to-build-your-own-dci-dashboard.html)).

In this article, we are going to explore the various places where naming could have an impact.

## Team

The team name should start by the name of your company and if there are multiple teams in DCI for your company, add a name that will differentiate the various teams.

![job team](images/naming/job-team.png)

## Remote CI

A remoteci reprensents the lab so to easily find it, use the name of your company and something to identify your lab. For example the location of the lab or the type of hardware in your lab.

![job remoteci](images/naming/job-remoteci.png)

## Job name

The job name can be specified in your `settings.yml` file by using the `dci_name`. Use a name that is meaningful for your organization to help differentiate your various jobs.

![job name](images/naming/job-name.png)

## Configuration

`dci_configuration` is also a variable that can be configured in your `settings.yml` file. It represents the different scenarios or hardware configurations you want to use for a particular job.

![job configuraion](images/naming/job-configuration.png)

## Comment

I recommend not to set the `dci_comment` variable in your `settings.yml` file and to keep it for analysis. You can build your own automation to set a comment based on the log analysis when a job is failing. Or you can have a process in your team to comment failed jobs and this way you know a job has been analyzed when a comment is set.

![job comment](images/naming/job-comment.png)

## Status reason

`status_reason` is a field of a job that can only be set after the job creation. It is used usually to track bug ids for a particular job failures. It is very useful for statistics on failures. You can use [`httpie`](https://httpie.io/) to set it like that:

        $ http -p h --auth "<user>:<password>" GET https://api.distributed-ci.io/api/v1/jobs/<job-id>|grep ETag:
        $ http --auth "<user>:<password>" PUT https://api.distributed-ci.io/api/v1/jobs/<job-id> If-match:<etag> status_reason=<reason>

![job status reason](images/naming/job-status-reason.png)

## URL

You can specify the URL representing a change you are testing from a GitHub PR or a Gerrit change using the `dci_url` variable. This is usually set on the command line when starting the agent rather than putting it in the `settings.yml` file as it can change at all invocation.

![job url](images/naming/job-url.png)

## Tags

Tags are a good way to organize jobs to be able to filter them. This can be set by using a list of strings on the `dci_tags` variable.

![job tags](images/naming/job-tags.png)

## Impact of naming on job comparison

To display improvements or regression in test results, DCI is looking for the previous job. What define a previous job is the most recent job before the current one with the following attributes:

* same remote CI
* same job name
* same configuration
* same URL
