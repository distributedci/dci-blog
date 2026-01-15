Title: Advanced dci-queue features
Date: 2026-01-09 10:00
Category: how-to
Tags: dci, ci, OpenShift, OCP, dci-queue, advanced
Slug: advanced-dci-queue-features
Author: Pierre Blanc
Github: pierreblanc
Summary: Advanced features of dci-queue for power users: multi-pools, console output, and more

[TOC]

## Introduction

In the [previous article](dci-queue.html), we introduced `dci-queue`, a queuing tool used in DCI deployments. We covered the basics: creating pools, scheduling commands, and managing resources.

This article explores advanced features that help you get more out of `dci-queue` in complex scenarios, such as multi-pool deployments, debugging with console output, and discovering information about your queued jobs.

## Multi-Pools

In complex scenarios, you may need resources from multiple pools simultaneously. A common use case is ACM (Advanced Cluster Management) Hub/Spoke setups, where you need one resource from a hub pool and another from a spoke pool.

### Using dci-pipeline-schedule with Multiple Pools

The `dci-pipeline-schedule` command supports multiple `-p` options to specify pools. Each `-p` option associates a pool name with the pipeline jobs that follow it.

For example, to schedule a ZTP (Zero Touch Provisioning) deployment with an ACM hub deployment using a resource from the `vpool` pool, followed by spoke deployments using resources from the `spokes` pool:

    :::shell-session
    $ dci-pipeline-schedule -p vpool acm-hub -p spokes ocp-4.19-spoke-ztp-gitops hardware-validation

In this ZTP deployment example, the spoke pool (`spokes`) contains two pipeline jobs: `ocp-4.19-spoke-ztp-gitops` (which handles the ZTP deployment of the spoke cluster) and `hardware-validation` (which validates the hardware). You can specify as many pipeline jobs as needed for each pool. Similarly, while this example uses two pools, you can chain more pools by adding additional `-p` options.

When this job executes, `dci-queue` reserves resources from each pool before starting execution. You can see which resources were reserved in the queue listing:

    :::shell-session
    $ dci-queue list vpool
    Executing commands on the vpool pool:
     158 [jumphost,sno2]: env DCI_QUEUE=vpool RES=jumphost KUBECONFIG= /usr/share/dci-pipeline/dci-pipeline-helper acm-hub -p2 ocp-4.19-spoke-ztp-gitops hardware-validation (wd: /home/dci)

In this example, `jumphost` was reserved from the `vpool` pool and `sno2` was reserved from the `spokes` pool. The notation `[jumphost,sno2]` shows both reserved resources.

### Referencing Pools in Pipeline Jobs

When using multiple pools, pipeline jobs can reference specific pools using the `-p<num>` syntax, where `<num>` is the pool number (starting from 1 for the first pool, 2 for the second, etc.).

When you use `dci-pipeline-schedule`, it automatically manages the pool referencing for you. You don't need to manually specify the `-p<num>` syntax in your pipeline files. The command translates the `-p` options you provide on the command line into the appropriate pool references for each pipeline job.

In the example above, `acm-hub` uses the first pool (`vpool`), and `-p2` in the command indicates that `ocp-4.19-spoke-ztp-gitops` and `hardware-validation` should use the second pool (`spokes`). This `-p2` reference is automatically added by `dci-pipeline-schedule` based on the pool order you specified.

Multi-pools work seamlessly with dci-pipeline's input and output mechanism. Jobs can share information between them using input/output configuration keys, regardless of which pool they use. The input and output functionality is not impacted by multi-pools and works perfectly across pools.

## Console Output and Logging

By default, `dci-queue` writes command output to log files. For debugging or monitoring, you can output logs to the console instead.

### Console Output

Use the `-c` or `--console-output` global option to send logs to the console:

    :::shell-session
    $ dci-queue -c schedule mypool dci-pipeline pipeline.yml

You can also use the `-C` or `--command-output` option with the `schedule` command to output only the command output (not the dci-queue logs) to the console:

    :::shell-session
    $ dci-queue schedule -C mypool dci-pipeline ocp-install:ansible_inventory=/path/inventories/@RESOURCE pipeline.yml

### Logging Levels

Control the verbosity of `dci-queue` logs with the `-l` or `--log-level` option. Available levels are: `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.

For example, to see detailed debug information:

    :::shell-session
    $ dci-queue -l DEBUG schedule mypool dci-pipeline pipeline.yml

You can also set the default log level using the `DCI_QUEUE_LOG_LEVEL` environment variable:

    :::shell-session
    $ export DCI_QUEUE_LOG_LEVEL=DEBUG
    $ dci-queue schedule mypool dci-pipeline pipeline.yml

## Resource Reservation for Debugging

When debugging a deployment, you may want to ensure that a resource remains reserved after the job starts, preventing other jobs from redeploying on the same node. This is particularly useful when you need to investigate issues after a deployment completes.

### Removing Resources After Job Start

Use the `-r` or `--remove-resource` option with the `schedule` command to remove the resource from the pool after the job starts executing. This ensures the resource is no longer available for other jobs, allowing you to debug the deployment without interference:

    :::shell-session
    $ dci-queue schedule -r mypool dci-pipeline pipeline.yml

Once the job starts, the resource is removed from the pool, guaranteeing that no other job will redeploy on that node.

The resource remains removed until you manually add it back to the pool using `dci-queue add-resource <POOL> <RESOURCE>`.

## Running Multiple Jobs with the Same Command

By default, `dci-queue` prevents scheduling a job if the exact same command is already running. However, when you have multiple resources in your pool and want to test the same deployment multiple times in parallel, you can use the `-f` or `--force` option to override this behavior.

The `-f` option allows you to schedule a job even if the same command is already running:

    :::shell-session
    $ dci-queue schedule -f mypool dci-pipeline pipeline.yml

This is particularly useful when you want to:

- Validate a deployment configuration by running it on multiple resources simultaneously
- Test the same deployment across different nodes at the same time
- Ensure consistency by running identical commands on multiple resources

## Extracting DCI Job IDs

When `dci-pipeline` or `dci-check-change` runs through `dci-queue`, the logs contain DCI job IDs. The `dci-job` command extracts these IDs from the logs, making it easy to find the DCI job associated with a queue job.

    :::shell-session
    $ dci-queue dci-job mypool 42
    openshift-vanilla:2441f3a5-aa97-45e9-8122-36dfc6f17d84
    deploy-app1:3b2c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e

The output shows the job definition name and the DCI job ID, one per line. This is useful for tracking jobs in the DCI web UI or for rebuilding pipelines using `dci-rebuild-pipeline`.

If no DCI job IDs are found in the log, the command returns an error:

    :::shell-session
    $ dci-queue dci-job mypool 43
    No DCI job IDs found in (pool/id): mypool/43

## Conclusion

These advanced features make `dci-queue` more powerful for complex deployment scenarios. Multi-pools enable sophisticated setups like ACM Hub/Spoke architectures, and the dci-job command helps you track your queued jobs effectively.

For more information, refer to the [dci-pipeline documentation](https://doc.distributed-ci.io/dci-pipeline/#dci-queue-command).
