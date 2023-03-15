Title: Testing large application? Use Ansible to get your test results validated in an automated way
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

# Standalone Usage

# Use DCI to Automatically Verify the Tests

