# OrchidE definition file builder
A tool to generate parser and code definitions for the IntelliJ plugin OrchidE.

The tool generates meta information from Ansible Galaxy collection to be used by OrchidE 
* for parsing Ansible playbooks and roles
* for code completion suggestions
* for various inspection to check for valid code snippets.

## Getting started - ready to use definitions

### Compatiblity of releases

OrchidE-Builder packages for Ansible 4.4.0, 20210816 and newer **require** at least 
[OrchidE plugin](https://plugins.jetbrains.com/plugin/12626-orchide--ansible-language-support) version 2020.1.5.


### Installation

To use the latest definitions of Ansible Galaxy collections bundle with OrchidE:

1. Download the latest definition package from [releases](https://github.com/tfroescher/orchide-builder/releases/latest) or a specific Ansible version 
   [6.5.0](https://github.com/tfroescher/orchide-builder/releases/6.5.0),
   [6.1.0](https://github.com/tfroescher/orchide-builder/releases/6.1.0),
   [5.9.0](https://github.com/tfroescher/orchide-builder/releases/5.9.0),
   [5.7.0](https://github.com/tfroescher/orchide-builder/releases/5.7.0),
   [5.6.0](https://github.com/tfroescher/orchide-builder/releases/5.6.0),
   [5.5.0](https://github.com/tfroescher/orchide-builder/releases/5.5.0),
   [5.3.0](https://github.com/tfroescher/orchide-builder/releases/5.3.0),
   [5.0.1](https://github.com/tfroescher/orchide-builder/releases/5.0.1),
   [4.9.0](https://github.com/tfroescher/orchide-builder/releases/4.9.0),
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
Any collection that documents the meta information as Ansible can be used as a source.

### Pre-requisites
* WSL, Linux or MacOS
* Python 3 (tested with 3.9)
* Python pip3, pipenv
* Bash
* a Java (JDK) version 8 - 14
* Apache Ant
* Git (or download this repository) 

### Install CLI

1. Install Python 3, bash, java and Apache ant via your package manager 
     * e.g for Fedora
         ```shell
         $ dnf install git ant pipenv 
         ```
1. Check out this repository
1. Run
    ```shell
    $ pipenv install 
     ```
    within the repository root folder

### Usage 

1. Configure the Ansible collection

    1. Create a new configuration file from an existing one in the res folder 
       * for latest version copy a file with *date version*
       * for a list of collections with specific version copy a file with Ansible version
    1. Add / remove collections you want 
1. Run
    ```shell
    $ ./build.sh build-4release -a <version number> 
    $ ./build.sh build-4release -a 20210816 
    ``` 
   
1. Copy the built jar (./build/dist/orchide-definitions.jar) to the OrchidE's configured extension directory. 
   (set in Settings > Languages & Frameworks > OrchidE > Extension )
   
## Reporting Issues

If you're missing an Ansible Galaxy collection, experience a problem or have any other issue, please file an issue.
You can also reach out me via [support@orchide.dev](mailto:support@orchide.dev). 


## Acknowledgments

This repository uses code from the Ansible project.

Thank you to the awesome [Ansible](https://github.com/ansible/ansible) project.

## License

[GNU General Public License](LICENSE) v3.0
