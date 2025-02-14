# Vehicle Simulation Analysis

## Project Overview
This focus of this project is to analyze the simulation data at a container terminal, which is produced by an optimization software. Currently, the project is limited to a deep analysis of the data extracted from the produced simulation 
logs; however, we intend to expand the project by creating suitable objectives and constraints to further optimize the process.


## Project Structure
The project is structured as follows:

- The `vsim` package includes all the required utility and analytics functions
- The `notebooks` directory provides a holistic analysis of the data and the underlying process. It's designed to give the reader of this repository a deep understanding of the problem at hand, and provide useful insights through statistics and 
visualizations.


## Project Setup Guidelines
In order to be able to run the code within the notebooks, some requirements need to be fulfilled:

- `Python` >= *3.10*
- `notebook` >= *7.3.2* (Run ```pip install notebook```). We did not list it under `requirements.txt`, since it's up to you whether you want to run the code via notebooks or not.

Move into the root directory of the project. Run the following command to install third-party packages:
```bash
pip install -r requirements.txt
```

Once the packages are installed, create a directory named `data` in the root of the project. Put the log file (extracted from the zip file) and the metadata (the Excel sheet) under this directory.

