Title: Explore the DCI MCP server to unlock AI models support on DCI resources
Date: 2026-02-18 10:00
Category: divulgation
Tags: dci, mcp, ai
Slug: dci-mcp-server-ai
Author: Ramon Perez
Github: raperez
Summary: The DCI MCP server is a Model Context Protocol (MCP) server adapted for the DCI API. It allows AI models to interact with DCI for comprehensive data extraction about DCI jobs, components, topics and files. This blog post presents this AI tool and provide some context about potential use cases, involving AI analysis, where you can benefit from this utility.

[TOC]

# Introduction

[Distributed-CI (DCI)](https://doc.distributed-ci.io/) is a platform that orchestrates CI/CD pipelines and stores a wealth of data about jobs, components, topics, teams, and artifacts. As pipelines and test results grow, making sense of that data (finding patterns, diagnosing failures, or producing reports) can be time-consuming. AI assistants can help, but they need structured access to DCI rather than manual copy-paste.

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open protocol that lets AI applications connect to external data sources and tools through standardized *servers*. An MCP server exposes capabilities (tools, resources, prompts) that an AI model can call during a conversation. That way, the model can query real data, run actions, and use the results in its answers.

The [DCI MCP server](https://github.com/redhat-community-ai-tools/dci-mcp-server) is a MCP server built for the [DCI API](https://doc.distributed-ci.io/dci-control-server/docs/API/). It allows AI models to interact with DCI for comprehensive data extraction: searching jobs with rich query filters, querying components and topics, downloading job files, and more. Optional integrations extend the workflow (for example, turning DCI reports into Google Docs or pulling Jira ticket data referenced in job comments). By plugging this server into your AI environment (e.g. [Cursor](https://cursor.com/) or any MCP-compatible client), you can ask natural-language questions about your DCI jobs and pipelines and get answers grounded in live DCI data.

This post is for DCI users who want to expand how they analyze DCI resources with AI. We will introduce the DCI MCP server, walk through its main features and integrations, and suggest practical ways to use it in your daily work. We will focus in Cursor as tool to drive the interaction with this MCP server.

# Installing the tool

Below is a concise overview of how to install the [DCI MCP server](https://github.com/redhat-community-ai-tools/dci-mcp-server) and optionally enable Google Drive and Jira integrations.

For exact commands and config snippets, use the project’s [README](https://github.com/redhat-community-ai-tools/dci-mcp-server/blob/main/README.md) and the setup guides linked in each section.

## DCI MCP server

- **Get the code and dependencies** — Clone the repo, then install with `uv sync` and activate the virtual environment.
- **DCI credentials** — Copy the example env file to `.env` and fill in your DCI auth (API key via `DCI_CLIENT_ID` / `DCI_API_SECRET`, or username/password via `DCI_LOGIN` / `DCI_PASSWORD`). A credentials' option could be to use the ones from a remoteci that belongs to the team from which you want to start to extract and analyze data from this MCP server.
- **Wire it into your MCP client** — For Cursor, add a `dci` server entry in `~/.cursor/mcp.json` that runs the project’s `main.py` with `uv run` (see README for the exact JSON). For web or HTTP-based clients, use the SSE transport: run the server with the `MCP_TRANSPORT=sse` env set and point the client at the SSE endpoint; the [README](https://github.com/redhat-community-ai-tools/dci-mcp-server#web-based-integration-sse-transport) has the details.

Once that’s done, DCI tools (job search, components, file download, etc.) are available.

The next two sections are optional add-ons that can be included.

## Google Drive integration (optional)

This integration turns DCI reports and markdown into Google Docs. In short:

- Create a Google Cloud project and enable the Drive API.
- Generate OAuth 2.0 *Desktop application* credentials and save the JSON as `credentials.json`.
- In your `.env` file, set the paths for `GOOGLE_CREDENTIALS_PATH` and `GOOGLE_TOKEN_PATH`.
- Run the one-time Google Drive initialization script (a small Python one-liner from the repo) and complete the browser OAuth flow; this stores your token for future use.

With this, you can start uploading reports in Google Drive. For this to work, we recommend to run your prompts **without Red Hat VPN connection**, else the upload process is likely to fail. Also, bear in mind that the documents that are uploaded are usually saved in the root directory of your user account.

Full steps, troubleshooting, and security notes are in the [Google Drive Setup Guide](https://github.com/redhat-community-ai-tools/dci-mcp-server/blob/main/GOOGLE_DRIVE_SETUP.md).

## Jira integration (optional)

Jira support fetches ticket data (including comments and changelog) from Red Hat Jira and links to DCI job comments. For this to work:

- Create a Personal Access Token in your [Red Hat Jira profile](https://issues.redhat.com/secure/ViewProfile.jspa) under Personal Access Tokens.
- Add the following to your `.env` file:
  - `JIRA_API_TOKEN=<your_token>`
  - `JIRA_URL=https://issues.redhat.com`
- Once these are set, the Jira MCP tools will be available.

For usage and troubleshooting, see the [Jira Setup Guide](https://github.com/redhat-community-ai-tools/dci-mcp-server/blob/main/JIRA_SETUP.md).

# Playing with the MCP server

Once the DCI MCP server is installed and connected to your client, you can use the built-in prompts (e.g. weekly or quarterly reports, root-cause analysis) or drive the assistant with free-form questions. To get repeatable, high-quality results, it helps to use **custom prompts** that spell out the task, the data to fetch, and the format of the output.

## Creating your own prompts

Good prompts for DCI workflows usually do the following:

- **Define the role and goal** — e.g. “You are a CI Duty engineer; produce a daily failure report” so the model knows the context and the deliverable.
- **Specify which DCI data to use** — Mention filters that matter: `remoteci`, `team`, tags (e.g. `daily`), `configuration`, or pipeline name, and the time window (use the MCP `today` / `now` tools when you need “current” or “today” in DCI’s timezone).
- **Break the work into clear steps** — e.g. “(1) List expected jobs from cron, (2) Query DCI for jobs in that window, (3) Compare and list missing/failed jobs, (4) Build the report.” That encourages the model to call the right MCP tools in order.
- **Describe the output format** — Sections (Executive Summary, New Problems, Critical Issues, tables, etc.), and whether to add hyperlinks to job IDs or Jira tickets. If the report should be written to a file (e.g. under `/tmp/dci/`), say so.
- **Call out pitfalls** — e.g. “Query by pipeline name as well as by lab/team so you don’t miss post-install stages” or “Only count a job as unexecuted if its previous stage succeeded.” That reduces common mistakes when the model uses the job search DSL.

You can ship these prompts as Cursor *commands* (e.g. markdown files in a folder that Cursor exposes as `/your-command-name`) so your team can run the same workflow with a single command and optional parameters (e.g. a date). Please ask Telco Partner CI team in case you want to expand information about this, we have experience on defining this kind of prompts for our daily jobs.

## Example: extracting the list of jobs

Here is an example of a prompt that you can use with your preferred AI editor to retrieve the list of jobs for a given pipeline name in a given lab, in order to extract some intersting information such as the passed/failed jobs, comparison of DCI components used on thes jobs, etc.

    I want to make a report to analyze the results obtained in the following subset of DCI daily jobs launched in the Telco Partner CI team during the last week (from Monday to Sunday):

    - pipeline name is install-4.20
    - team name is rh-telco-ci
    - configuration is hybrid
    - since it's a daily job, it has to have the `daily' tag

    Make a report with the following information:

    1. Executive summary: Brief overview of CI health for the specified teams and time period.
    2. List of failed job, including link to the related Jira card and reason of failure.
    3. Component Version Analysis: For each failed job, show the components related to the OpenShift, dci-openshift-(app)-agent, dci-pipeline and ansible-collection-redhatci-ocp version in failed jobs, and what's the successful reference version from previous passed jobs.
    4. Recommendations (immediate/medium/long-term): Action items under 'Immediate', 'Medium-term', and 'Long-term' headings, presented as bullet lists.
    5. List of analyzed jobs: for further reference, include the list of jobs that you have retrieved, ordered by date. Also display the date.

You have [here](examples/2026-02-18-dci-mcp-server-ai/dci-report-telco-install-4.20-hybrid-week-2026-02-09.md) a report example based on this prompt.

# Conclusions

The DCI MCP server brings DCI’s job, component, and pipeline data into AI-assisted workflows. By implementing the Model Context Protocol, it lets AI models query DCI in a structured way—searching jobs, components, and topics, and downloading artifacts—so you can analyze failures, compare runs, and produce reports without manual copy-paste. Optional integrations (e.g. Google Drive for reports, Jira for ticket context) extend these capabilities inside tools like Cursor.

Getting started requires cloning the server repo, configuring DCI credentials (API key or remoteci credentials), and wiring the server into your MCP client (e.g. `~/.cursor/mcp.json` for Cursor). The optional Google Drive and Jira setups add a few extra steps but enable report publishing and Jira-linked analysis. Once connected, the DCI tools are available to your AI assistant for natural-language questions over live DCI data.

Effective use hinges on clear prompts: define the role and goal, specify DCI filters (remoteci, team, tags, time window), break the work into steps, and describe the desired output format. Custom prompts can be packaged as Cursor commands, so your team can run the same workflows consistently. For more details on these workflows, examples, or how to adapt them to your use case, please reach out to the Telco Partner CI team, we will be glad to help you!
