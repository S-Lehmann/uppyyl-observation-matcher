# Uppyyl Observation Matcher

The implementations of the Uppyyl observation matcher, a tool used to match observations against Uppaal models.

## Getting Started

In this section, you will find instructions to setup and run the tools on your local machine.
The setup was tested in the [TACAS 23 Artifact Evaluation VM](https://zenodo.org/records/7113223).

### Prerequisites

#### Python

Install Python3.8 for this project.

#### Virtual Environment

If you want to run the project in a dedicated virtual environment, first install virtualenv:
```
python3.8 -m pip install virtualenv
```

And create a virtual environment:

```
cd project_folder
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

To install the Uppyyl Observation Matcher (and the dependencies "Uppaal C Language" and "Uppaal Model"), run the following commands in order:

```
python3.8 -m pip install -e path_to_uppaal_c_language
python3.8 -m pip install -e path_to_uppaal_model
python3.8 -m pip install -e path_to_uppyyl_observation_matcher
```

### Usage

The Uppyyl observation matcher only provides the observation matcher functionality as a library of functions, and is not executable per se.
For usage of the library, see the [Uppyyl Observation Matcher Experiments](https://github.com/S-Lehmann/uppyyl-observation-matcher-experiments).

## Authors

* **Sascha Lehmann** - *Initial work*


## Acknowledgments

* The original Uppaal model checking tool can be found at http://www.uppaal.org/.
* The project is associated with the [Institute for Software Systems](https://www.tuhh.de/sts) at Hamburg University of Technology.
