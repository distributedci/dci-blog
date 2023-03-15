Title: Automating JUnit test result verification for large applications using Ansible filter-plugins
Date: 2023-03-17 10:00
Category: how-to
Tags: dci, junit, ocp, tests, workload
Slug: verify-tests
Author: Tatiana Krishtop, Pierre Blanc
Github: tkrishtop
Summary: Automated validation of test results becomes necessary when you have a large application and JUnit files with thousands of tests to verify. The typical requirement is to ensure that all tests prefixed by 'network' pass, and when you have several thousands of them, this becomes challenging. In this post, we will showcase an Ansible role that automates this type of validation.

[TOC]

# Standard Need: Automated Regex Validation

Let's imagine a large application written in several programming languages. During unit and integration testing, we could end up with several JUnit files, each containing thousands of tests. At this scale, manually going through all the tests is out of the question. However, automating everything is not straightforward either.

The naive idea is to list all the tests expected to pass and validate them in an automated loop.

        tests_to_verify:
          - filename: "my_nice_junit_file.xml"
            expected_green:
              - testcase: 'HasProductionTag_2022_10_01_155918946139571'
              - testcase: 'LayerCountAcceptable'
              - testcase: 'RunAsNonRoot'
              - ...
          - filename: "my_another_junit_file.xml"
            expected_green:
              - testcase: 'failingInUserAcceptancePhase'
              - testcase: 'networkBasicConnectivity_2022_10_01_155918946139571'
              - testcase: 'networkEdgeNetworkConnectivity_2022_10_01_155918946139571'
              - testcase: 'networkDatabaseLatency'
              - ...

The first argument against that idea is that writing and keeping up-to-date a configuration file with thousands of tests is quite error-prone. We may need to add, remove, or rename tests, which would require manual updates to this huge configuration file. In practice, we often need a form of test-name-by-regex validation, such as validating all tests to be passing or ensuring that all tests whose names start with 'network' are passing. The idea is not to hard-code the test name but to allow developers some freedom in adding or modifying tests, or even using timestamps in the test names.

        tests_to_verify:
          - filename: "my_nice_junit_file.xml"
            expected_green:
              - testcase: '*'  # all testcases should pass
          - filename: "my_another_junit_file.xml"
            expected_green:
              - testcase: 'failingInUserAcceptancePhase'
              - testcase: 'network\w+'  # all tests whose names start with 'network' should pass

That makes the initial configuration much shorter, but it does not consider the tests that are expected to fail when running in certain environments. Therefore, instead of pinning all "green" test results, we might need to customize our expectations.

        tests_to_verify:
          - filename: "my_nice_junit_file.xml"
            expected_results:
              - testcase: '*'  # all testcases should pass
                passed: True
          - filename: "my_another_junit_file.xml"
            expected_results:
              - testcase: 'failingInUserAcceptancePhase'
                passed: False
              - testcase: 'network\w+'  # all tests whose names start with 'network' should pass
                passed: True

Now that we have technically defined our task by identifying a configuration file format with expected results that is convenient to use, let's move on to the implementation details. If you are only interested in practical usage, please skip the next section and go directly to [the example of standalone usage for verify-tests role](verify-tests#standalone-usage).

# Implementation details: Verify-Tests Role Description

## Implementation Steps

The [Ansible implementation](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/roles/verify-tests/tasks/parse_junit_file.yml) of the tests validation is pretty straightforward. The idea is to iterate over the config with expected results and do the following steps for every file:

- Check if the required file is present and fail if not.

- Retrieve the actual test results.

- Compare actual results with the expected results.

## Filter-Plugins in Ansible

The first point is trivial, but two next points are more interesting because they leverage nice Ansible option called [filter-plugins](https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html#filter-plugins). The main point of its usage is to implement some easy-to-code-in-Python tasks in Python and then natively use them within the Ansible role.

You could check [Ansible core](https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/filter) for the best practices for filter-plugins, but the main idea of writing custom filter is pretty simple. All you need is to create a folder called `filter-plugins` and put inside this folder your Python plugin. `filter-plugins` is a reserved location and Ansible will consider it automatically.

        $ tree
        .
        └── roles
            └── verify-tests
                ├── filter_plugins
                │   ├── junit2dict.py
                │   └── regex_diff.py
                ├── README.md
                └── tasks
                    ├── main.yml
                    └── parse_junit_file.yml

The fishbone of every Python plugin is simple as well: all you need is a class `FilterModule` implementing method `filters`:

        class FilterModule(object):
            def filters(self):
                return {
                    'junit2dict': self.junit2dict,
                }

            def junit2dict(self, junit_filepath):
                # TODO: process JUnit file and return dictionary

Once it is done, the new custom filter `junit2dict` could be directly used. Here, the `junit2dict` filter is used to process `junit_filename`:

        set_fact:
          actual_results: "{{ junit_filename | junit2dict }}"

The filter could also take several variables as input, allowing quite flexible data processing. For example, to compare `expected_results` and `actual_results` and return a difference:

        vars:
          expectation_failed: "{{ t.expected_results | regex_diff(actual_results) }}"

## Two Custom Filter-Plugins

Back to the implementation logic, we use filter-plugins twice: first, [to retrieve the actual test results](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/roles/verify-tests/filter_plugins/junit2dict.py) using junitparser Python package to parse JUnit file, and second, to [compare them to the expected results](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/roles/verify-tests/filter_plugins/regex_diff.py) in a nested loop that would be cumbersome in Ansible but looks pretty standard in Python.

# Standalone Usage

# Use DCI to Automatically Verify the Tests

