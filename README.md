# OrchidE definition file builder
A tool to generate parser and code definitions for the IntelliJ plugin OrchidE.

The tool generates meta-information from Ansible Galaxy collections to be used by OrchidE
* for parsing Ansible playbooks and roles
* for code completion suggestions
* for quick documentation of Ansible modules, filters and tests
* for various inspections to check for valid code snippets.

## Getting started—ready to use definitions

### Compatiblity of releases

Support for OrchidE-Builder format V2 **requires** at least [OrchidE plugin](https://plugins.jetbrains.com/plugin/12626-orchide--ansible-language-support) version 2024.1.3. 

Support for Ansible plugins is included in packages for Ansible version 9.0 and newer,
in 8.7.0 Update 1, in 7.7.0 Update 1 and since the package 20240225.

OrchidE-Builder packages for Ansible 4.4.0, 20210816 and newer **require** at least
[OrchidE plugin](https://plugins.jetbrains.com/plugin/12626-orchide--ansible-language-support) version 2020.1.5.

### OrchidE-Builder formats

**V2**:

Version V2 is based on Ansible's ansible-doc JSON output format and provides more comprehensive documentation within OrchidE
and is easier to create.

**V1**:

Version V1 is based on older Ansible build scripts and uses a legacy format and less documentation within OrchidE.

Version V1 is *deprecated*.

### Installation

To use the latest definitions of Ansible Galaxy collections bundle with OrchidE:

1. Download the latest definition package from [releases](https://github.com/tfroescher/orchide-builder/releases/) as 
   a bundle in format [V2](https://github.com/tfroescher/orchide-builder/releases/20251209-v2) or [V1](https://github.com/tfroescher/orchide-builder/releases/latest)
   or a specific Ansible version:
   - V2 bundles
      * [12.2.0](https://github.com/tfroescher/orchide-builder/releases/12.2.0-v2),
      [12.1.0](https://github.com/tfroescher/orchide-builder/releases/12.1.0-v2),
      [12.0.0](https://github.com/tfroescher/orchide-builder/releases/12.0.0-v2),
      * [11.9.0](https://github.com/tfroescher/orchide-builder/releases/11.9.0-v2),
      [11.8.0](https://github.com/tfroescher/orchide-builder/releases/11.8.0-v2),
      [11.7.0](https://github.com/tfroescher/orchide-builder/releases/11.7.0-v2),
      [11.6.0](https://github.com/tfroescher/orchide-builder/releases/11.6.0-v2),
      [11.5.0](https://github.com/tfroescher/orchide-builder/releases/11.5.0-v2),
      [11.4.0](https://github.com/tfroescher/orchide-builder/releases/11.4.0-v2),
      [11.3.0](https://github.com/tfroescher/orchide-builder/releases/11.3.0-v2).
   - V1 bundles 
      * [11.9.0](https://github.com/tfroescher/orchide-builder/releases/11.9.0),
      [11.7.0](https://github.com/tfroescher/orchide-builder/releases/11.7.0),
      [11.6.0](https://github.com/tfroescher/orchide-builder/releases/11.6.0),
      [11.5.0](https://github.com/tfroescher/orchide-builder/releases/11.5.0),
      [11.4.0](https://github.com/tfroescher/orchide-builder/releases/11.4.0),
      [11.3.0](https://github.com/tfroescher/orchide-builder/releases/11.3.0),
      [11.2.0](https://github.com/tfroescher/orchide-builder/releases/11.2.0),
      [11.1.0](https://github.com/tfroescher/orchide-builder/releases/11.1.0),
      [11.0.0](https://github.com/tfroescher/orchide-builder/releases/11.0.0),
      * [10.7.0](https://github.com/tfroescher/orchide-builder/releases/10.7.0),
      [10.6.0](https://github.com/tfroescher/orchide-builder/releases/10.6.0),
      [10.5.0](https://github.com/tfroescher/orchide-builder/releases/10.5.0),
      [10.4.0](https://github.com/tfroescher/orchide-builder/releases/10.4.0),
      [10.3.0](https://github.com/tfroescher/orchide-builder/releases/10.3.0),
      [10.2.0](https://github.com/tfroescher/orchide-builder/releases/10.2.0),
      [10.1.0](https://github.com/tfroescher/orchide-builder/releases/10.1.0),
      [10.0.1](https://github.com/tfroescher/orchide-builder/releases/10.0.1),
      * [9.13.0](https://github.com/tfroescher/orchide-builder/releases/9.13.0),
      [9.12.0](https://github.com/tfroescher/orchide-builder/releases/9.12.0),
      [9.11.0](https://github.com/tfroescher/orchide-builder/releases/9.11.0),
      [9.10.0](https://github.com/tfroescher/orchide-builder/releases/9.10.0),
      [9.9.0](https://github.com/tfroescher/orchide-builder/releases/9.9.0),
      [9.8.0](https://github.com/tfroescher/orchide-builder/releases/9.8.0),
      [9.7.0](https://github.com/tfroescher/orchide-builder/releases/9.7.0),
      [9.6.1](https://github.com/tfroescher/orchide-builder/releases/9.6.1),
      [9.5.1](https://github.com/tfroescher/orchide-builder/releases/9.5.1),
      [9.4.0](https://github.com/tfroescher/orchide-builder/releases/9.4.0),
      [9.3.0](https://github.com/tfroescher/orchide-builder/releases/9.3.0),
      [9.2.0](https://github.com/tfroescher/orchide-builder/releases/9.2.0),
      [9.1.0](https://github.com/tfroescher/orchide-builder/releases/9.1.0),
      [9.0.1](https://github.com/tfroescher/orchide-builder/releases/9.0.1),
      * [8.7.0 Update 1](https://github.com/tfroescher/orchide-builder/releases/8.7.0.1),
      [~~8.7.0~~](https://github.com/tfroescher/orchide-builder/releases/8.7.0),
      [8.6.1](https://github.com/tfroescher/orchide-builder/releases/8.6.1),
      [8.5.0](https://github.com/tfroescher/orchide-builder/releases/8.5.0),
      [8.4.0](https://github.com/tfroescher/orchide-builder/releases/8.4.0),
      [8.3.0](https://github.com/tfroescher/orchide-builder/releases/8.3.0),
      [8.2.0](https://github.com/tfroescher/orchide-builder/releases/8.2.0),
      [8.1.0](https://github.com/tfroescher/orchide-builder/releases/8.1.0),
      [8.0.0](https://github.com/tfroescher/orchide-builder/releases/8.0.0),
      * [7.7.0 Update 1](https://github.com/tfroescher/orchide-builder/releases/7.7.0.1),
      [~~7.7.0~~](https://github.com/tfroescher/orchide-builder/releases/7.7.0),
      [7.3.0](https://github.com/tfroescher/orchide-builder/releases/7.3.0),
      [7.2.0](https://github.com/tfroescher/orchide-builder/releases/7.2.0),
      [7.1.0](https://github.com/tfroescher/orchide-builder/releases/7.1.0),
      [7.0.0](https://github.com/tfroescher/orchide-builder/releases/7.0.0),
      * [6.7.0](https://github.com/tfroescher/orchide-builder/releases/6.7.0),
      [6.6.0](https://github.com/tfroescher/orchide-builder/releases/6.6.0),
      [6.5.0](https://github.com/tfroescher/orchide-builder/releases/6.5.0),
      [6.1.0](https://github.com/tfroescher/orchide-builder/releases/6.1.0),
      * [5.10.0](https://github.com/tfroescher/orchide-builder/releases/5.10.0),
      [5.9.0](https://github.com/tfroescher/orchide-builder/releases/5.9.0),
      [5.7.0](https://github.com/tfroescher/orchide-builder/releases/5.7.0),
      [5.6.0](https://github.com/tfroescher/orchide-builder/releases/5.6.0),
      [5.5.0](https://github.com/tfroescher/orchide-builder/releases/5.5.0),
      [5.3.0](https://github.com/tfroescher/orchide-builder/releases/5.3.0),
      [5.0.1](https://github.com/tfroescher/orchide-builder/releases/5.0.1),
      * [4.9.0](https://github.com/tfroescher/orchide-builder/releases/4.9.0),
      [4.4.0](https://github.com/tfroescher/orchide-builder/releases/4.4.0),
      [4.0.0](https://github.com/tfroescher/orchide-builder/releases/4.0.0),
      [3.4.0](https://github.com/tfroescher/orchide-builder/releases/3.4.0).
2. Create a directory on your filesystem - p.e. `~/.orchide` and put the downloaded .jar there.
3. Open IDE settings > Languages & Frameworks > OrchidE > Extension.
4. Add the path to your newly created directory.
5. Hit `Apply`.
6. Restart your IDE.

## Getting started - create your own definition package

### General information

To use Ansible collections that are not part of OrchidE, that are newer or that from other sources you can create your own package.
Any collection that documents the meta-information as Ansible can be used as a source.

### Pre-requisites
* WSL, Linux or MacOS
* Python 3
* Python pip3, pipenv
* Bash
* Java (JDK)
* jq 

**Important note**

The OrchidE builder can only bundle one version per Ansible collection. 
To prevent duplicate collections being used, a Python virtual environment should be set up. 
If using a system-installed Ansible package, make sure that no other Ansible collections are installed. 
(For example, via the system package manager or within Python's site-packages.)

### Install CLI

1. Install Python 3, bash, java and jq via your package manager
   * e.g for Fedora
       ```shell
       $ dnf install java-latest-openjdk-devel git pipenv jq
       ```
1. Check out this repository
1. Run
    ```shell
    $ pipenv install
     ```
   within the repository root folder

### Configure a galaxy authentication token if required

If you would like to consume collections from
https://console.redhat.com/ansible/automation-hub you need to provide
a token.

add the following to `ansible.cfg` in this directory:

```
[galaxy]
server_list = automation_hub, release_galaxy

[galaxy_server.automation_hub]
url=https://console.redhat.com/api/automation-hub/
auth_url=https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
token=<your token here>

[galaxy_server.release_galaxy]
url=https://galaxy.ansible.com/
```

For creating a token see [Creating the offline token in automation hub](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/managing_automation_content/managing-cert-valid-content#proc-create-api-token_cloud-sync).

### Usage

1. Configure the Ansible collection

   1. Create a new configuration file from an existing one in the res folder
      * for the latest version, copy a file with *date version*
      * for a list of collections with specific version, copy a file with Ansible version
   1. Add / remove collections you want
1. Run
    ```shell
    $ ./bin/dumpModulesFromAnsibleDoc.sh -a <version number>
    $ ./bin/dumpModulesFromAnsibleDoc.sh -a 20250421
    ```

1. Copy the built jar (./_build/orchide-definitions.jar) to the OrchidE's configured extension directory.
   (set in Settings > Languages & Frameworks > OrchidE > Extension)


## DEPRECATED / create V1 definition package
### Pre-requisites
* WSL, Linux or MacOS
* Python 3 (tested with 3.9, <3.12)
* Python pip3, pipenv
* Bash
* a Java (JDK) version 8 - 14
* Apache Ant
* Git (or download this repository)

### Install CLI

1. Install Python 3, bash, java, jq and Apache ant via your package manager
     * e.g for Fedora
         ```shell
         $ dnf install git ant pipenv jq
         ```
1. Check out this repository
1. Run
    ```shell
    $ pipenv install
     ```
    within the repository root folder

### Configure a galaxy authentication token if required

If you would like to consume collections from
https://console.redhat.com/ansible/automation-hub you need to provide
a token.

add the following to `ansible.cfg` in this directory:

```
[galaxy]
server_list = automation_hub, release_galaxy

[galaxy_server.automation_hub]
url=https://console.redhat.com/api/automation-hub/
auth_url=https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
token=<your token here>

[galaxy_server.release_galaxy]
url=https://galaxy.ansible.com/
```

For creating a token see [Creating the offline token in automation hub](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/managing_automation_content/managing-cert-valid-content#proc-create-api-token_cloud-sync).

### Usage

1. Configure the Ansible collection

    1. Create a new configuration file from an existing one in the res folder
       * for the latest version, copy a file with *date version*
       * for a list of collections with specific version, copy a file with Ansible version
    1. Add / remove collections you want
1. Run
    ```shell
    $ ./build.sh build-4release -a <version number>
    $ ./build.sh build-4release -a 20210816
    ```

1. Copy the built jar (./build/dist/orchide-definitions.jar) to the OrchidE's configured extension directory.
   (set in Settings > Languages & Frameworks > OrchidE > Extension)

### Forcing a specific java version

For example under Fedora if `ant` is installed from rpm, it might be
necessary to force `ant` to use the right java version. Even if
`/usr/bin/java` already points to the right version.

For this to work have to set `JAVA_HOME` before calling `build.sh`:

```
export JAVA_HOME=/usr/lib/jvm/jre-11/lib
```

You can verify that `ant` is using the right java version (<= 14 see
above) with

```
ant -diagnostics
```

## Reporting Issues

If you're missing an Ansible Galaxy collection, experience a problem
or have any other issue, please file an issue.  You can also reach out
to me via [support@orchide.dev](mailto:support@orchide.dev).


## Acknowledgments

This repository uses code from the Ansible project.

Thank you for the awesome [Ansible](https://github.com/ansible/ansible) project.

## License

[GNU General Public License](LICENSE) v3.0
