# Historionomy Dataviz App

This App is a Streamlit Cloud App, aimed at illustrating the principles of [Historionomy](https://www.historionomie.net/)

To understand the deployment, please follow Stream Cloud Documenation [here](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)

## Main structure

When you create a Streamlit Cloud App, you must choose which python file is the "main" file to be launched at the execution of the app

Current "main" file is `historionomy.py`. The app start executing commands after the `APP START` comment block.

## Data

### Historionomical data

The historionomical data comes from [this](https://docs.google.com/spreadsheets/d/1JYrzDxdz_6RMHAhHUshp8gPbejryC0jVq5ufxrqRViM/edit?usp=sharing) Google Sheet

The import script from the [data-tooling](https://github.com/historionomy/data-tooling) project creates the following tables in Supabase :

- countries : current historionomical status of all countries
- history : historionomical courses of all countries over time
- koinons : a list of potential historionomical "koinons"
- labels : a description of the historionomical status
- legend : a legend for a small section of the "countries" table

### Our World in Data metrics

The import script from the [data-tooling](https://github.com/historionomy/data-tooling) project also allows to upload the following datasets from Our World in Data (link [here](https://ourworldindata.org/)) into the Supabase backend:

- Historical Literacy Rates ([link](https://ourworldindata.org/grapher/cross-country-literacy-rates))
- GDP per capita, PPA and constant dollars, from the Penn Database ([link](https://ourworldindata.org/grapher/gdp-per-capita-penn-world-table))
- Government spending ([link](https://ourworldindata.org/grapher/historical-gov-spending-gdp))
- Urbanization rates ([link](https://ourworldindata.org/grapher/long-term-urban-population-region?time=1500..latest))

## Functional logic

### Data Loading and preprocessing

At runtime, the app :

- load the "world map" data with the function `load_world_map`
- load the graphical asset with the function `load_image`. Graphical assets are part of the app code (for the moment)
- load the backend data from a Supabase PostgresQL database with the function `load_backend_data`

Functions for loading the backend data are defined in `backend.py`

Data structure for storing the content of long text content is defined in `text_content.py`

The `languages_map_labels` dict in `historionomy.py` is used to store the multilingual texts of the labels used by the app. There are currently two languages supported, english and french (`EN` and `FR` keys in the dictionary).

### Drawing the frontend

Once data are loaded, the app starts drawing the frontend, starting from the `DRAWING FRONTEND` comment block.

There are currently 5 tabs in the main display :

- introduction
- the historionomical world map, displaying a plotly map
- the data tab, displaying historionomical courses per country, combined with Our World in Data metrics
- the historionomical stages tab, displaying the chart of stages made by Redcrow
- the resources tab, displaying hypertext links to external resources

## Specific features

### World Map

The historionomical world map is produced by the function `create_map` in `historionomy.py`. The map is a Plotly Express Choropleth map

### Courses chart

The datatab combined two charts, whose creation is managed by function `history_chart` in `history_chart.py`

- a Plotly Express Line Chart for the metrics from Our World In Data
- a Plotly Express Bar Chart for the historionomical stages per country

## Dev mode

### Python environment

Install conda, a environment manager for python :

On Linux

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
bash ~/miniconda.sh -b -p $HOME/miniconda
eval "$($HOME/miniconda/bin/conda shell.bash hook)"
conda init
```

On MacOS (you will be prompted for admin password at some moments):

```bash
mkdir -p ~/miniconda3
curl https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh -o ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
~/miniconda3/bin/conda init bash
~/miniconda3/bin/conda init zsh
```

Move to your work folder, and create a conda environment for the project :

```bash
cd $WORKFOLDER ### move to your workfolder
conda create -n histo python=3.11 ### this command create a local environment in python 3.11
```

Now, activate the python 3.11 environment you just created :

```bash
export CONDA_ENV=privacy
conda activate $CONDA_ENV
```

This command will add the name of the environment between parenthesis on your command line prompt.

If you need to exit from the conda environment, simply run :

```bash
conda deactivate
```

### Launch app locally

In `historionomy.py`, at the top of the file, there is a global function `MODE`. Set it to `debug` when you are developing the app, it allows to skip the loading of the World Map and the Stages Chart, and will load backend data from csv files in a folder `../data-tooling` relative to your current app folder.

Launch app locally with command :

```bash
streamlit run historionomy.py
```
