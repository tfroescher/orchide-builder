# OrchidE definition file builder
A tool to generate parser and code definitions for the IntelliJ plugin OrchidE.

The tool generates meta information from Ansible Galaxy collection to be used by OrchidE 
* for parsing Ansible playbooks and roles
* for code completion suggestions
* for various inspection to check for valid code snippets.

## Getting started - ready to use definitions

### Installation

To use the latest definitions of Ansible Galaxy collections bundle with OrchidE:

1. Download the latest definition packge from [releases](https://github.com/tfroescher/orchide-builder/releases/latest)
1. Put the downloaded jar into the plugin lib folder of OrchidE: [&lt;IntelliJ user plugins folder>/orchide/lib](https://www.jetbrains.com/help/idea/tuning-the-ide.html#plugins-directory). 

    *Tip:* to find the plugin base folder - open IntelliJ -> Help -> Edit custom properties. 
    Either it shows you the path the properties file, which is in the plugins root folder or it opens an existing properties file which is located in the plugin root folder.
1. Restart IntelliJ

New definition files will now be used.

#### Alternative Method (See https://github.com/tfroescher/orchide-builder/issues/1)

1. Create a directory on your filesystem - p.e. `~/.orchide` and put the downloaded .jar there.
1. Open IDE settings > Languages & Frameworks > OrchidE > Extension.
1. Add the path to your newly created directory and hit `Check for update`.
1. Hit `Apply`.
1. Check if the collections are updated. If not, restart your IDE.

## Getting started - create your own definition package

### General information

To use Ansible collections that are not part of OrchidE, that are newer or that from other sources you can create your own package.
Any collection that documents the meta information as Ansible can be used as a source.

### Pre-requisites
* WSL, Linux or MacOS
* Python 3 (tested with 3.6)
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

    1. Create custom.properties file from the sample file in the root folder
    1. Add your collections to build 
1. Run
    ```shell
    $ ./build.sh build-all
    ``` 
1. Copy the built jar (./build/dist/orchide-definitions.jar) to the OrchidE's plugin lib folder [&lt;IntelliJ plugins folder>/orchide/lib](https://www.jetbrains.com/help/idea/tuning-the-ide.html#plugins-directory)

## Configuration

See [custom.properties.sample](custom.properties.sample) for configuration options.

## Creating a full package 
A full package with OrchidE's builtin Ansible Galaxy collections and your own can be created with

```shell script
$ ./build.sh -i build-all
``` 

## Limitation

* The tool fetches always the latest stable Ansible Galaxy collections. Versioning is not yet supported. 

## Reporting Issues

If you're missing an Ansible Galaxy collection, experience a problem or have any other issue, please file an issue.
You can also reach out me via [support@orchide.dev](mailto:support@orchide.dev). 


## Acknowledgments

This repository uses code from the Ansible project.

Thank you to the awesome [Ansible](https://github.com/ansible/ansible) project.

## License

[GNU General Public License](LICENSE) v3.0
