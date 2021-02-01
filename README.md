# WP3 Demonstation for D3.4
Demonstrations of the integration with [Musketeer Machine Learning Library (MMLL)](https://github.com/Musketeer-H2020/MMLL) using [Musketeer's pycloudmessenger](https://github.com/IBM/pycloudmessenger/).

The focus of this repository is to demonstrate the integration with WP4 and to highlight the full feature set provided by WP3. This reuses work from the D3.3 demonstrator, adding examples of how to use the extended features since D3.3.

## Linux installation

Use one of the following options:

### Installation creating a virtual environment:
This replies on the MMLL installation, which also requires the installation of the following pacakge:

```
sudo apt install graphviz-dev
```

Once complete, we can create an environment.

```
./create_env.sh
source venv/bin/activate
```

### Installation without virtual environment:

`pip install -r requirements.txt`

Or if you only require pycloudmessenger, then:

`pip install https://github.com/IBM/pycloudmessenger/archive/v0.7.1.tar.gz`

**IMPORTANT NOTE**: The pycloudmessenger package requires a credentials file to access the cloud service. Please, place this file at the `demos/demo_pycloudmessenger/` folder.

## Input data

The datasets needed to run these demos are located at [this link](https://drive.google.com/drive/folders/1-piNDL_tL6V4pCI-En02zeCEqoL-dUUu?usp=sharing). Please, download and place them in your local `input_data/` folder. 

## Usage

Please visit subfolders in `demos/demo_pycloudmessenger/` for a detailed explanation about how to run the demo.
The output files are stored in the corresponding `results/` folder.

This project has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 824988. https://musketeer.eu/
