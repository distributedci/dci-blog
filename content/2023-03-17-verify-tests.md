Title: Automating JUnit test result verification for large applications using Ansible filter-plugins
Date: 2023-03-21 10:00
Category: how-to
Tags: dci, junit, ocp, tests, workload
Slug: verify-tests
Author: Tatiana Krishtop, Pierre Blanc
Github: tkrishtop
Summary: Automated validation of test results becomes necessary when you have a large application and JUnit files with thousands of tests to verify. The typical requirements are to ensure that all tests are green, or all tests prefixed by 'network' pass, and when you have several thousands of tests, this becomes challenging. In this post, we will showcase an Ansible role that automates this type of validation.

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

The first argument against that idea is that writing and keeping up-to-date a configuration file with thousands of tests is quite error-prone. We may need to add, remove, or rename tests, which would require manual updates to this huge configuration file. In practice, we often need a form of testname-by-regex validation, such as validating all tests to be passing or ensuring that all tests whose names start with 'network' are passing. The idea is not to hard-code the test name but to allow developers some freedom in adding or modifying tests, or even using timestamps in the test names.

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

[Our Ansible implementation](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/roles/verify-tests/tasks/parse_junit_file.yml) of the tests validation is pretty straightforward. The idea is to iterate over the config with expected results and do the following steps for every file:

- Check if the required file is present and fail if not.

- Retrieve the actual test results.

- Compare actual results with the expected results and fail if they differ.

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

Back to the implementation logic, we use filter-plugins twice:

- First, [to retrieve the actual test results](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/roles/verify-tests/filter_plugins/junit2dict.py) using junitparser Python package to parse JUnit file and convert it into suitable JSON.

- Second, to [compare them to the expected results](https://github.com/redhat-cip/dci-openshift-app-agent/blob/master/roles/verify-tests/filter_plugins/regex_diff.py) in a nested loop that would be cumbersome in Ansible but looks pretty standard in Python.

# Standalone Usage

In this section, we provide an example of standalone usage of our development, which does not require DCI installation. For example, suppose you have the following JUnit file with multiple test suites and would like to verify that all tests starting from `test_edu` are passing.

        $ cat multiple_testcases.xml
        <?xml version='1.0' encoding='UTF-8'?>
        <testsuites tests="8" failures="0" errors="0" skipped="0" time="509.707">
        <testsuite errors="0" failures="0" hostname="ocp"
        name="du_robustness_sanity_before_test"
        skipped="0" tests="2" time="1.093" timestamp="2022-11-28T04:42:27.491770">
        <testcase classname="home.rq.cloud-test.test-common.tests.test.edu.test_basic"
        name="test_edu_pods_count_before" time="0.714"/>
        <testcase classname="home.rq.cloud-test.test-common.tests.test.edu.test_basic"
        name="test_edu_pods_status_before" time="0.379"/>
        </testsuite>
        <testsuite errors="0" failures="0" hostname="ocp"
        name="robustness-test_recovery" skipped="0" tests="4"
        time="507.516" timestamp="2022-11-28T04:45:33.086397">
        <testcase classname="home.rq.cloud-test.test-common.tests.test.robustness.test_recovery"
        name="test_ssh_recovery" time="161.791"/>
        <testcase classname="home.rq.cloud-test.test-common.tests.test.robustness.test_recovery"
        name="test_site_healthz" time="90.104"/>
        <testcase classname="home.rq.cloud-test.test-common.tests.test.robustness.test_recovery"
        name="test_api_resources_status" time="254.335"/>
        <testcase classname="home.rq.cloud-test.test-common.tests.test.robustness.test_recovery"
        name="test_operators_status" time="1.286"/></testsuite>
        <testsuite errors="0" failures="0" hostname="ocp"
        name="du_robustness_sanity_after_test"
        skipped="0" tests="2" time="1.098" timestamp="2022-11-28T04:54:19.020942">
        <testcase classname="home.rq.cloud-test.test-common.tests.test.edu.test_basic"
        name="test_edu_pods_count_after" time="0.395"/>
        <testcase classname="home.rq.cloud-test.test-common.tests.test.edu.test_basic"
        name="test_edu_pods_status_after" time="0.703"/>
        </testsuite>
        </testsuites>

1. Copy the `filter-plugins` directory from the [source](https://github.com/redhat-cip/dci-openshift-app-agent/tree/master/roles/verify-tests) to the same folder as your playbook.

        $ tree
        .
        ├──
        ├── filter_plugins
        │   ├── junit2dict.py
        │   └── regex_diff.py
        ├── files
        |   └── multiple_testcases.xml
        └── my_nice_playbook.yml

2. Write a simple playbook to define the expected results, retrieve the actual test results, and compare them.

        $ cat my_nice_playbook.yml
        ---
        - name:
          hosts: local
          tasks:
            - name: Define the expected test results
              set_fact:
                expected_results:
                  - testcase: 'test_edu_*'
                    passed: True

            - name: Retrieve the actual test results
              vars:
                junit_filename: "files/multiple_testcases.xml"
              set_fact:
                actual_results: "{{ junit_filename | junit2dict }}"

            - name: Validate test results and fail if they are not as expected
              vars:
                expectation_failed: "{{ expected_results | regex_diff(actual_results) }}"
              fail:
                msg: "The following expectations failed: {{ expectation_failed }}"
              when: expectation_failed | length > 0
        ...

3. Check that the validation works.

        $ ansible-playbook -i inventory my_nice_playbook.yml -v

        PLAY [local] **********************************************************************************************************************************

        TASK [Gathering Facts] ************************************************************************************************************************
        ok: [127.0.0.1]

        TASK [Define expected test results] ***********************************************************************************************************
        ok: [127.0.0.1] => {"ansible_facts": {"expected_results":
        [{"passed": true, "testcase": "test_edu_*"}]}, "changed": false}

        TASK [Retrieve actual test results] ***********************************************************************************************************
        ok: [127.0.0.1] => {"ansible_facts": {"actual_results":
        [{"passed": true, "testcase": "test_edu_pods_count_before"},
        {"passed": true, "testcase": "test_edu_pods_status_before"},
        {"passed": true, "testcase": "test_ssh_recovery"},
        {"passed": true, "testcase": "test_site_healthz"},
        {"passed": true, "testcase": "test_api_resources_status"},
        {"passed": true, "testcase": "test_operators_status"},
        {"passed": true, "testcase": "test_edu_pods_count_after"},
        {"passed": true, "testcase": "test_edu_pods_status_after"}]},
        "changed": false}

        TASK [Validate test results and fail if they are not as expected] *****************************************************************************
        skipping: [127.0.0.1] => {"changed": false, "skip_reason": "Conditional result was False"}

        PLAY RECAP ************************************************************************************************************************************
        127.0.0.1                  : ok=3    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0

# Use DCI to Automatically Verify the Tests

