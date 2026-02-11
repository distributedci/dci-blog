# DCI Daily Jobs Report: Telco Partner CI — install-4.20 hybrid

**Period:** Monday 2026-02-09 — Sunday 2026-02-15  
**Pipeline:** install-4.20  
**Team:** rh-telco-ci  
**Configuration:** hybrid  
**Tag:** daily  

---

## 1. Executive summary

During the week of 2026-02-09 to 2026-02-15, the **rh-telco-ci** team ran **7** daily jobs for the **install-4.20** pipeline with **hybrid** configuration. **3** jobs succeeded and **4** failed (2 `failure`, 2 `error`), giving a **~43% success rate**. Failures were concentrated on **2026-02-09** (2 jobs: bootstrap/DNS and VM provisioning) and **2026-02-12** (2 jobs: both "Install packages"). The following days (2026-02-10, 2026-02-11, 2026-02-13) had successful runs. All jobs ran on remoteci **rh-dallas**. Root causes are tracked in Jira under CILAB (JIRA-2253, JIRA-1884, JIRA-551). Component version differences between failed and successful runs are summarized in Section 3 to support triage and regression analysis.

---

## 2. Failed jobs

| Date       | Job ID   | Job name         | Status  | Reason | Jira |
|-----------|----------|------------------|--------|--------|------|
| 2026-02-09 | [7e476fc4-2126-442e-a0f5-9ac918c84cbc](https://www.distributed-ci.io/jobs/7e476fc4-2126-442e-a0f5-9ac918c84cbc) | openshift-vanilla | failure | Failed at (dns): redhatci.ocp.installer : Wait for Bootstrap Complete: dial tcp: lookup no such host | JIRA-2253 |
| 2026-02-09 | [ef13f9de-137f-47be-88d8-ac174799cd3d](https://www.distributed-ci.io/jobs/ef13f9de-137f-47be-88d8-ac174799cd3d) | openshift-vanilla | error   | Failed at redhatci.ocp.kvirt_vm : Wait for VM to be in desired state master-1 | JIRA-1884 |
| 2026-02-12 | [d175fda4-3822-4f85-8c05-a6caf1ed2c88](https://www.distributed-ci.io/jobs/d175fda4-3822-4f85-8c05-a6caf1ed2c88) | openshift-vanilla | error   | Failed at Install packages | JIRA-551 |
| 2026-02-12 | [8a35977d-cb9e-485e-a79c-34cc978451a5](https://www.distributed-ci.io/jobs/8a35977d-cb9e-485e-a79c-34cc978451a5) | openshift-vanilla | error   | Failed at Install packages | JIRA-551 |

**Failure reason summary**

- **JIRA-2253:** Bootstrap/DNS — installer failed waiting for bootstrap with "dial tcp: lookup no such host" (likely DNS or network resolution in the hybrid environment).
- **JIRA-1884:** VM provisioning — kvirt_vm role did not reach desired state for `master-1`.
- **JIRA-551:** Install packages — two jobs failed at "Install packages" (likely repo/package availability or environment; same Jira for both).

---

## 3. Component version analysis

For each failed job, the table below shows the **OpenShift**, **dci-openshift-agent**, **dci-pipeline**, and **ansible-collection-redhatci-ocp** versions used in the failed run, and the **successful reference** version from the most recent prior (or same-week) successful job in this pipeline/configuration.

*Note: No dci-openshift-app-agent component was present in the retrieved jobs.*

### 3.1 Failed job: 7e476fc4 (2026-02-09 — JIRA-2253)

| Component | Failed job version | Successful reference (2026-02-10) |
|-----------|--------------------|------------------------------------|
| **OpenShift** | 4.20.0-0.nightly-2026-02-08-075840 | 4.20.0-0.nightly-2026-02-09-061845 |
| **dci-openshift-agent** | 1.23.0-1.202601300245gitdef8c8e3.el8 | 1.23.0-1.202601300245gitdef8c8e3.el8 |
| **dci-pipeline** | 0.12.0-1.202602031249gitd5df9c5d.el8 | 0.12.0-1.202602091414git40928561.el8 |
| **ansible-collection-redhatci-ocp** | 2.19.1770333967-202602052326gitc2e3a0c8.el8 | 2.19.1770646501-202602091415gite0495e92.el8 |

### 3.2 Failed job: ef13f9de (2026-02-09 — JIRA-1884)

| Component | Failed job version | Successful reference (2026-02-10) |
|-----------|--------------------|------------------------------------|
| **OpenShift** | 4.20.13 | 4.20.0-0.nightly-2026-02-09-061845 |
| **dci-openshift-agent** | 1.23.0-1.202601300245gitdef8c8e3.el8 | 1.23.0-1.202601300245gitdef8c8e3.el8 |
| **dci-pipeline** | 0.12.0-1.202602031249gitd5df9c5d.el8 | 0.12.0-1.202602091414git40928561.el8 |
| **ansible-collection-redhatci-ocp** | 2.19.1770333967-202602052326gitc2e3a0c8.el8 | 2.19.1770646501-202602091415gite0495e92.el8 |

### 3.3 Failed jobs: d175fda4 & 8a35977d (2026-02-12 — JIRA-551)

| Component | Failed job version (d175fda4) | Failed job version (8a35977d) | Successful reference (2026-02-11 or 2026-02-13) |
|-----------|-------------------------------|-------------------------------|--------------------------------------------------|
| **OpenShift** | 4.20.0-0.nightly-2026-02-11-020558 | 4.20.13 | 4.20.0-0.nightly-2026-02-09-061845 (Feb 11) / 4.20.0-0.nightly-2026-02-11-020558 (Feb 13) |
| **dci-openshift-agent** | 1.23.0-1.202601300245gitdef8c8e3.el8 | 1.23.0-1.202601300245gitdef8c8e3.el8 | 1.23.0 (Feb 11) / 1.24.0-1.202602122045git75e97a9c.el8 (Feb 13) |
| **dci-pipeline** | 0.12.0-1.202602101303gita70786cb.el8 | 0.12.0-1.202602101303gita70786cb.el8 | 0.12.0-1.202602101303gita70786cb.el8 (same) |
| **ansible-collection-redhatci-ocp** | 2.19.1770646501-202602091415gite0495e92.el8 | 2.19.1770646501-202602091415gite0495e92.el8 | 2.19.1770646501 (Feb 11) / 2.20.1770931618-202602122126git670ca3f8.el8 (Feb 13) |

**Observations**

- Feb 9 failures used **older** dci-pipeline and ansible-collection builds than the Feb 10 success; upgrading to the versions used on 2026-02-10 may help avoid the same class of issues.
- Feb 12 failures used the **same** dci-pipeline and ansible-collection as the Feb 11 success; the "Install packages" (JIRA-551) failures are likely **environment/repo or lab-state** rather than component regressions. The Feb 13 success used a newer dci-openshift-agent (1.24.0) and ansible-collection (2.20.x).

---

## 4. Recommendations

### Immediate

- **Confirm and update Jira:** Ensure JIRA-2253, JIRA-1884, and JIRA-551 are still the correct tickets for the observed failures and that they are linked to the DCI jobs above.
- **JIRA-551 (Install packages):** Check rh-dallas lab state for 2026-02-12 (repos, network, disk, or cleanup) and confirm whether the same failure reproduces on retry or with the same component set.
- **JIRA-2253 (DNS / bootstrap):** Verify DNS and network configuration for the hybrid setup on rh-dallas, especially for the nightly build used on 2026-02-09.

### Medium-term

- **Stabilize component versions:** Prefer the dci-pipeline and ansible-collection versions that were used in successful runs (e.g. 2026-02-10) when scheduling daily install-4.20 hybrid jobs to reduce regressions from new builds.
- **JIRA-1884 (VM state):** Review kvirt_vm and lab automation for master-1 provisioning and timeouts; consider retries or clearer error reporting.
- **Monitoring:** Add or review alerts for "Install packages" and "Wait for VM" failures in this pipeline/configuration so CI duty can react quickly.

### Long-term

- **Trend analysis:** Run similar reports regularly (e.g. weekly) for install-4.20 hybrid to spot recurring failures and component-version patterns.
- **Documentation:** Document known failure modes (JIRA-2253, JIRA-1884, JIRA-551) and preferred component versions in team runbooks so future failures are tagged and triaged faster.
- **Lab and automation:** Work with lab owners to improve resilience of rh-dallas (repos, DNS, VM lifecycle) for hybrid daily jobs.

---

## 5. List of analyzed jobs (by date)

All jobs: pipeline **install-4.20**, team **rh-telco-ci**, configuration **hybrid**, tag **daily**, period **2026-02-09 — 2026-02-15**.

| # | Date       | Job ID   | Status  | Name             | Remoteci  |
|---|------------|----------|--------|------------------|-----------|
| 1 | 2026-02-09 | 7e476fc4-2126-442e-a0f5-9ac918c84cbc | failure | openshift-vanilla | rh-dallas |
| 2 | 2026-02-09 | ef13f9de-137f-47be-88d8-ac174799cd3d | error   | openshift-vanilla | rh-dallas |
| 3 | 2026-02-10 | 0e9e4095-b9c3-4f25-a4dd-e14422ef0536 | success | openshift-vanilla | rh-dallas |
| 4 | 2026-02-11 | 8d908fd3-be70-4b8e-b991-73d03e7287a0 | success | openshift-vanilla | rh-dallas |
| 5 | 2026-02-12 | d175fda4-3822-4f85-8c05-a6caf1ed2c88 | error   | openshift-vanilla | rh-dallas |
| 6 | 2026-02-12 | 8a35977d-cb9e-485e-a79c-34cc978451a5 | error   | openshift-vanilla | rh-dallas |
| 7 | 2026-02-13 | 13e69652-473c-4826-9ff3-e5fbfc0f6261 | success | openshift-vanilla | rh-dallas |

**Total:** 7 jobs (3 success, 4 failed).  
**Source:** DCI job search, filter: `(created_at>='2026-02-09') and (created_at<='2026-02-16') and (tags in ['daily']) and (team.name='rh-telco-ci') and (pipeline.name='install-4.20') and (configuration=~'hybrid')`.
