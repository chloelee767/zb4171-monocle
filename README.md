# Investigating the effect of changing parameters on the trajectories learnt by Monocle 3

By ZB4171 Group 4: Chloe & Daniel

## Requirements

- [Nextflow](https://www.nextflow.io/) version 20.04.1. It's likely that later versions will work too, but we have not tried.
- A Unix system. So far we have only tested on Linux (Manjaro, up-to-date as of 16 Nov 2020)
- Monocle 3: there are numerous ways to install it, but we recommend the docker image `lee0767/monocle3-cli` ([link](https://hub.docker.com/r/lee0767/monocle3-cli)) for compatibility with all the scripts used here.
  - If you just want to follow the quick start or don't intend to run `run_monocle.py` locally, then just Monocle 3 v0.2.2 will suffice.
- For the R scripts, we have used R versions 3.6.X and 4.0.X with success.
- For the Python scripts, we used Python 3.8.x. Python 3.6 onwards should work, but not tested.

## Quick start

### 1. Downloading and preprocessing the Tabula Muris dataset <a id='quick-start-dataset'></a>

1. Download the droplet data from the Tabula Muris dataset 

    ``` sh
    wget https://s3.amazonaws.com/czbiohub-tabula-muris/TM_droplet_mat.rds
    wget https://s3.amazonaws.com/czbiohub-tabula-muris/TM_droplet_metadata.csv
    ```

1. Generate Monocle's `cell_data_set` object from these files, and use `saveRDS` to save it as an RDS file using our script `filter-dataset.R`. `filter-dataset.R` will also select only the data for a specific tissue type.

    ``` sh
    Rscript filter-dataset.R <tissue_type> <path_to_rds_file> <path_to_metadata> <path_to_output_rds_file>
    ```

    - Eg. `Rscript filter-dataset.R Marrow TM_droplet_mat.rds TM_droplet_metadata.csv TM_droplet_Marrow.rds`
    - You can look at the metadata file to see what tissue types are available

### 2. Running the pipeline

#### Running on AWSBatch

**First time setup:**

1. Set up an AWSBatch queue. Make sure the compute environments associated with the queue have the AWS command line tool installed -- you may need to create a custom AMI for this.
1. Create a S3 bucket. The bucket does not need to be public.
1. Set up the AWS CLI tool on the computer that you'll be starting the Nextflow script from, and ensure that it is configured with credentials that will allow you to access your queue and bucket.
1. Update the following values in the `nextflow.config` file:
   - `process.queue`: this should be the name of your queue
   - `aws.region`
   - `aws.batch.cliPath`: this should be the full path to the AWS CLI tool inside the compute environment configured for your queue
1. Upload the following files to your S3 bucket:
   - `run_monocle.py`
   - `extract_info.R`
   - `comparison.R`
   - The RDS file from part 1: [Downloading and preprocessing the Tabula Muris dataset](#quick-start-dataset)
1. Update the following paths inside `run_monocle.nf`.
   - Paths to scripts: look for a script variable under the `input:` section of each process
   - Path to input file: under the input section of the `runMonocle` process, change the `inFile` variable
   - publishDir paths for all processes: this is where Nextflow will store the files listed under `output:` which are created by each process
1. Run the pipeline once with the default Monocle parameters (or whatever settings you wish), excluding the comparison step, to generate reference results to perform future comparison against. 
    - To set the parameters to default, change the following lines in `run_monocle.nf`:
      - Uncomment line 3: `// umapNumNeighbors = Channel.of(15) // default number of neighbours`
      - Comment out line 4: `umapNumNeighbors = Channel.of(25, 35)`
    - Then run:
      ``` sh
      nextflow run run_monocle.nf -profile awsbatch -work-dir <path_to_temp_dir_in_s3_bucket> --skipcomparison
      ```
        - `<path_to_temp_dir_in_s3_bucket>` is the directory that will be used as Nextflow's workDir. Nextflow will create folders in this directory to store any temporary files as well as log files.

1. Update the path to the reference results to the results you have just generated: change the `reference` in the input section of the `compareResults` process. Also reverse the other changes made to `run_monocle.nf` made in the previous step.

**Running the pipeline:**

The same as running Nextflow in the previous section, except without the `--skipcomparison` flag:

``` sh
nextflow run run_monocle.nf -profile awsbatch -work-dir <path_to_temp_dir_in_s3_bucket>
```

**Modifying the pipeline:**

If you want to try different numbers of UMAP neighbours, just modify `umapNumNeighbors` channel in `run_monocle.nf`. Otherwise if you want to and change other parameters, take a look at section on [how to use `run_monocle.py`](#run-monocle-py-usage) (it's much easier than setting up this nextflow pipeline :smiley:)

## Useful scripts

### `filter-dataset.R`: Generate Monocle 3's `cell_data_set` from the Tabula Muris dataset

See the [first quick start section](#quick-start-dataset)

### `run_monocle.py`: Single command for learning a trajectory using Monocle 3

**What it does:** The script `run_monocle.py` is a CLI utility for running all of the Monocle 3 functions (`preprocess_cds`, `reduce_dimension`, `cluster_cells`, `learn_graph, `order_cells`) needed to learn a trajectory, and optionally save the parameters used to run each of these functions in a JSON file.

#### Requirements

If you're not using the `lee0767/monocle3-cli` docker image, you'll need to manually install the following:

- Patched version of [monocle-scripts](https://github.com/chloelee767/monocle-scripts/tree/zb4171), a command line utility which wraps the individual functions in Monocle 3. The script is calling the Monocle functions via this utility. It adds support for more parameters in `reduce_dimension` / `reduceDim` and improves the automagic pseudotime assignments for `order_cells` / `orderCells`. The executable must be added to `PATH`.

#### Usage <a id='run-monocle-py-usage'>

``` sh
python run_monocle.py --input <path_to_input> --output <path_to_output> \ # required
    # the rest of the arguments below are optional:
    --save-config-to <path> \
    --temp-dir <path> \
    ## some examples of monocle parameters
    --preprocess-cds.num-dim <num_dim> --reduce-dimension.umap.n-neighbors <num_neighbors>
```

- `--save-config-to <path>` : where should the script save the JSON file containing all the parameters used by Monocle to? If not specified, this file will not be saved.
- `--temp-dir <path>` : where should the script save temporary files to? if not specified, it will use the current directory.
- The flags for the parameters for the different Monocle 3 functions are named as `--<function_name>.<parameter_name>`, based on the function and parameter names in the R package, with all underscores replaced with dashes.
- For boolean parameter values, `true`, `t`, `false`, `f` may be given.
- Run `python run_monocle.py --help` to view the full list of parameters supported.

**Example:**

``` sh
python run_monocle.py --input cds_droplet_Marrow.rds --output cds_droplet_Marrow.trajectory.rds \
    --save-config-to "monocle-params.json" --temp-dir /tmp \
    --preprocess-cds.num-dim 70 --reduce-dimension.umap.n-neighbors 30
```

#### Limitations
- Some parameters (mainly those that involve passing in a list) are not supported.
- None of `order_cells` inputs are currently supported.

### `extract_info.R`: extracting (partial) trajectory information from Monocle 3's cell_data_set

``` sh
Rscript extract_info.R <path_to_input> <path_to_output>
```

- The input file should be a RDS file with a `cell_data_set` containing the trajectories and pseudotimes learnt by Monocle (ie. up to `order_cells`). This is the output of `run_monocle.py`. 
- The output file will be a CSV file: see `sample/results/marrow_umapNN_15.csv` for an example of what it looks like

#### Limitations
- The script can currently only extract the coordinates of the first 2 UMAP dimensions.

### `comparison.R`: comparing Monocle trajectories

This script compares 2 Monocle trajectories and outputs 2 kinds of metrics for comparison:

1. the similarity of their branches (1 cluster = 1 branch), using the adjusted rand index (ARI)
2. the correlation between their pseudotime assignments, for each partition

This is based on the metrics used in the paper [Reversed graph embedding resolves complex single-cell trajectories](https://www.nature.com/nmeth/journal/vaop/ncurrent/full/nmeth.4402.html).

``` sh
Rscript comparison.R <condensed_trajectory_file_1> <condensed_trajectory_file_2> <ari_file> <correlations_file>
```
- The condensed trajectory files refer to the output of `extract_info.R`
- `<ari_file>` is the output CSV file containing the ARI value (see `sample/results/marrow_umapNN_15_marrow_umapNN_25_graph.csv` for an example)
- `<correlations_file>` is the output CSV file containing the pseudotime correlations (see `sample/results/marrow_umapNN_15_marrow_umapNN_25_partition.csv` for an example)


