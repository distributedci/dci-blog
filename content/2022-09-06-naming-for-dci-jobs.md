Title: Naming capabilities for DCI jobs
Date: 2022-09-06 07:00
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

## Remote CI

## Team

## Job name

## Configuration

## Comment

## Status reason

## URL

## Tags

## Impact of naming on job comparison

To display improvements or regression in test results, DCI is looking for the previous job. What define a previous job is the most recent job before the current one with the following attributes:

* same remote CI
* same job name
* same configuration
* same URL
