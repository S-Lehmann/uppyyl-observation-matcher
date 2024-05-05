# Uppaal C language

A Python implementation of the parsers and printers for Uppaal C code (and queries).

## Getting Started

In this section, you will find instructions to set up the Uppaal C language on your local machine.

### Prerequisites

#### Python

Install Python >=3.8 for this project.

#### Virtual Environment

If you want to run the project in a dedicated virtual environment, first install virtualenv:
```
python3.8 -m pip install virtualenv
```

And create a virtual environment:

```
cd project_folder
virtualenv venv
```

Then, activate the virtual environment on macOS and Linux via:

```
source ./venv/bin/activate
```

or on Windows via:

```
source .\venv\Scripts\activate
```

### Installing

To install the Uppaal C language directly from GitHub, run the following command:

```
TODO
```

To install the project from a local directory instead, run:

```
python3.8 -m pip install -e path_to_project_root
```

### Usage

The project can be used as a package for other projects.

## Running the tests

To run the tests (and optionally measure coverage), execute either:

```
make run_all_tests
make run_all_coverage
```

## Authors

* **Sascha Lehmann** - *Initial work* - [S-Lehmann](https://github.com/S-Lehmann)

See also the list of [contributors](TODO) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

* The original Uppaal model checking tool can be found at http://www.uppaal.org/.
* The project is associated with the [Institute for Software Systems](https://www.tuhh.de/sts) at Hamburg University of Technology.
