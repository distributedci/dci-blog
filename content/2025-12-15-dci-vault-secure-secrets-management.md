Title: dci-vault: Secure Secrets Management for DCI
Date: 2025-12-15 10:00
Category: how-to
Tags: dci, security, ansible-vault, secrets, encryption
Slug: dci-vault-secure-secrets-management
Author: Pierre Blanc
Github: pierreblanc
Summary: Learn how to securely manage secrets in your DCI pipelines and inventories using dci-vault, a wrapper around ansible-vault that uses your RemoteCI's API secret for encryption.

[TOC]

# Introduction

Managing secrets securely is a critical aspect of any CI/CD pipeline. In DCI (Distributed CI), you often need to store sensitive information like API keys, passwords, and credentials in your pipeline files and Ansible inventories. However, storing these secrets in plain text is a security risk.

**dci-vault** provides a secure solution for encrypting secrets in your DCI configuration files. It's a wrapper around `ansible-vault` that automatically uses your RemoteCI's `DCI_API_SECRET` as the encryption key, making it seamless to encrypt and decrypt secrets without managing separate vault passwords.

# Why Use dci-vault?

- **Encrypted Storage**: Secrets are stored in encrypted form, not in plain text
- **Team Collaboration**: Encrypted secrets can be safely committed to version control
- **No Password Management**: Uses your RemoteCI's API secret automatically - no need to remember or share vault passwords
- **Automatic Decryption**: DCI agents automatically decrypt secrets during execution

# How to Use dci-vault

## Prerequisites

Before using `dci-vault`, ensure you have:

1. **DCI credentials configured**: Your `DCI_API_SECRET` must be set in your environment or credentials file
2. **python-dciclient installed**: The `dci-vault` command is provided by the `python-dciclient` package

```bash
# Install python-dciclient (if not already installed)
sudo dnf install python3-dciclient
```

## Basic Usage

### Setting Up Your Environment

First, source your DCI credentials file to set the `DCI_API_SECRET` environment variable:

```bash
source dcirc.sh
```

Your `dcirc.sh` file should contain:

```bash
export DCI_CLIENT_ID=remoteci/<remoteci_id>
export DCI_API_SECRET=<your_remoteci_api_secret>
export DCI_CS_URL=https://api.distributed-ci.io
```

### Encrypting a String

To encrypt a string value for use in YAML files:

```bash
$ echo -n "my-secret-password" | dci-vault encrypt_string --stdin-name password
Reading plaintext input from stdin. (ctrl-d to end input)
password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          36373332616633313866333234303166616237613332316534393834663934663463353433363464
          6363626133323036383939633566383139373636633533390a316363393437653663363538343730
          65333862633131353030353137636236663036656264393638353464343138623664323731613331
          6466636637393865380a336365633465633037623935633866366562373732356635343361353334
          3732
Encryption successful
```

You can then copy the encrypted output directly into your YAML files.

### Encrypting Entire Files

To encrypt a complete file containing secrets:

```bash
$ dci-vault encrypt secrets.yml
New Vault password: 
Confirm New Vault password: 
Encryption successful
```

Wait, that's not right! Actually, with `dci-vault`, you don't need to enter a password - it uses your `DCI_API_SECRET` automatically. The command works seamlessly:

```bash
$ dci-vault encrypt secrets.yml
Encryption successful
```

### Viewing Encrypted Files

To view the contents of an encrypted file:

```bash
$ dci-vault view secrets.yml
api_key: my-secret-api-key
password: my-secret-password
```

### Editing Encrypted Files

To edit an encrypted file:

```bash
$ dci-vault edit secrets.yml
```

### Decrypting Files

To decrypt a file (for example, to use with other tools):

```bash
$ dci-vault decrypt secrets.yml
Decryption successful
```

## Using Encrypted Secrets in YAML Files

Once you have encrypted strings, you can use them in your pipeline files or inventories:

```yaml
# pipeline.yml
- name: deploy-openshift
  stage: ocp
  ansible_playbook: /usr/share/dci-openshift-agent/dci-openshift-agent.yml
  ansible_inventory: /etc/dci-pipeline/inventory
  dci_credentials: /etc/dci-openshift-agent/dci_credentials.yml
  topic: OCP-4.20
  components:
    - ocp
  ansible_extravars:
    # Encrypted secret
    api_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          36373332616633313866333234303166616237613332316534393834663934663463353433363464
          6363626133323036383939633566383139373636633533390a316363393437653663363538343730
          65333862633131353030353137636236663036656264393638353464343138623664323731613331
          6466636637393865380a336365633465633037623935633866366562373732356635343361353334
          3732
```

Or in your Ansible inventory:

```yaml
# inventory.yml
all:
  vars:
    registry_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          36373332616633313866333234303166616237613332316534393834663934663463353433363464
          6363626133323036383939633566383139373636633533390a316363393437653663363538343730
          65333862633131353030353137636236663036656264393638353464343138623664323731613331
          6466636637393865380a336365633465633037623935633866366562373732356635343361353334
          3732
  hosts:
    jumphost:
      ansible_host: 192.168.1.100
```

## Secrets Not Decrypting in dci-pipeline

If `dci-pipeline` cannot decrypt your secrets:

1. **Check credentials file**: Ensure `dci_credentials` in your pipeline points to a file with `DCI_API_SECRET`
2. **Verify RemoteCI**: Ensure you're using the same RemoteCI that encrypted the secrets
3. **Check file format**: Ensure your encrypted secrets use the `!vault |` YAML tag

# Conclusion

`dci-vault` provides a secure, convenient way to manage secrets in your DCI pipelines and inventories. By leveraging your RemoteCI's `DCI_API_SECRET`, it eliminates the need for separate password management while providing automatic isolation between different environments.

For more information, see the [python-dciclient documentation](https://github.com/redhat-cip/python-dciclient) or the [DCI documentation](https://docs.distributed-ci.io/).
