# Uppyyl Observation Matcher

The implementations of the Uppyyl observation matcher, a tool used to match observations against Uppaal models.

## Getting Started

In this section, you will find instructions to setup the Uppyyl observation matcher on your local machine.
The setup was tested in the [TACAS 23 Artifact Evaluation VM](https://zenodo.org/records/7113223).
For the setup in the TACAS 23 VM, execute the initial steps described in the first subsection of the prerequisites section;
otherwise, skip that part.

### Prerequisites

#### Initial setup of the TACAS 23 VM
- Download and install Oracle VM VirtualBox.
  - Note: For MacOS, only Intel hardware is fully supported yet.
- Add a Host-only network adapter in the settings of VirtualBox.
- Download and import the [TACAS 23 Artifact Evaluation VM](https://zenodo.org/records/7113223) appliance to VirtualBox.
- Enable the Host-only adapter:
  - Settings -> Network -> Enable Network Adapter
- (Optional) Add the VBoxGuestAdditions, e.g., for adapting the screen resolution in the VM:
  - Settings -> Storage -> Controller: IDE -> "Add optical drive" button -> Select "VBoxGuestAdditions.iso"
  - In the VM: Open the mounted drive -> execute `./autorun.sh`
- Start the TACAS VM
  - Username / Password: tacas23
- Create a folder in the VM under "Documents" were all data should be stored, and open a `cmd` there for the remaining setup steps.

#### Python

Install Python3.8 for this project.
```
apt-get update
add-apt-repository ppa:deadsnakes/ppa
apt-get install python3.8
apt-get install python3.8-distutils
```

#### Git
```
apt-get update
apt-get install git
```

#### Virtual Environment

If you want to install the project in a dedicated virtual environment, first install virtualenv:
```
python3.8 -m pip install virtualenv
```

You may need to add the path to the virtualenv tool to the `PATH` environment variable:
```
export PATH=<path_to_bin_dir_with_virtualenv>:$PATH
(e.g., export PATH=/home/tacas23/.local/bin:$PATH)
```


Afterwards, create a virtual environment:

```
cd <project_folder>
virtualenv om-env
```

Then, activate the virtual environment on macOS and Linux via:

```
source ./om-env/bin/activate
```

or on Windows via:

```
source .\om-env\Scripts\activate
```

#### Uppaal

The [Uppaal](https://www.uppaal.org/) model checking tool (tested with [version 4.1.24](https://uppaal.org/downloads/other/#uppaal-41)) is required to perform the actual checking on the generated matcher model.

### Installing

To install the Uppyyl Observation Matcher Experiments, first clone the repository:
```
cd <project_folder>
git clone https://github.com/S-Lehmann/uppyyl-observation-matcher.git
```

Then install the Uppyyl Observation Matcher (and the dependencies "Uppaal C Language" and "Uppaal Model") by running the following commands in order:

```
python3.8 -m pip install -e <project_folder>/uppyyl-observation-matcher/uppaal_c_language/
python3.8 -m pip install -e <project_folder>/uppyyl-observation-matcher/uppaal_model/
python3.8 -m pip install -e <project_folder>/uppyyl-observation-matcher/uppyyl_observation_matcher/
```

### Usage

The Uppyyl observation matcher only provides the observation matcher functionality as a library of functions, and is not executable per se.
For usage of the library, see the [Uppyyl Observation Matcher Experiments](https://github.com/S-Lehmann/uppyyl-observation-matcher-experiments).

## Authors

* **Sascha Lehmann** - *Initial work*


## Acknowledgments

* The original Uppaal model checking tool can be found at http://www.uppaal.org/.
* The project is associated with the [Institute for Software Systems](https://www.tuhh.de/sts) at Hamburg University of Technology.
