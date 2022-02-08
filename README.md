# Code to the paper "Modeling individual and cross-cultural variation in the mapping of emotions to speech prosody"

This README describes how to reproduce all results in the paper.

The repository contains of the following folders:
- `data` here is the data stored, since we do not own the corpora, the data cannot be shared
- `docs` here go the figures and other relevant documents for the submission. The contents are not under version control
- `results` here go the models and the analyses used for plotting 
- `src` here are all steps to obtain the data, fit the models, and create the figures
  1. `collect_corpora`: Collection of Python scripts to find all available corpora of emotional prosody
  2. `preprocess`: Once we obtained access to a subset of all the requested corpora, we run a preprocessing pipeline on 
  all data making sure all files have the same sampling rate and are mono. We furthermore extract the eGeMAPS features. 
  See README for more information.
  3. `annotate_data`: The next step is to run a factor analysis on all features and combine the features with additional
  meta-data, such as 'sex' or 'country'.
  4. `modelling` contains the code to fit all models. Keep in mind the models will run for a long time. The big model 
  took about 30 days to finish on a 32-core hpc @ 2.3 GHz.
  5. `analysis` performs all analysis used in the figures. All filenames ending with `_hpc` are ran on the hpc.
  6. `figures` are the R scripts to create the figures (the final figures were manually postprocessed).

### What is this repository for? ###

This repository contains all code to run the analysis and create all figures in the manuscript.

### How do I get set up? ###

##### Requirements

You need to have the following things set up to make it work:

- Access to a hpc that uses SLURM job management
- An installation of anaconda (I used Anaconda3, 2019.10)



You need to modify the SLURM jobs to be compatible with your hpc (e.g. change the name of the compute nodes), but this should be easy to do.



##### Setting up the environment

Setup the environment and load the packages

```
# Load conda, e.g.
# module use /hpc/shared/EasyBuild/modules/all; module load Anaconda3/2019.10

# Create the environment
conda create --name production_MAPS

# Activate it
conda activate production_MAPS

# Install R
conda install -c r r

# Install V8 (requirement for brms)
conda install -c conda-forge r-v8

# Create a symbolic link, see http://promberger.info/linux/2009/03/20/r-lme4-matrix-not-finding-librlapackso/
ln -s ~/.conda/envs/production_MAPS/lib/liblapack.so ~/.conda/envs/production_MAPS/lib/libRlapack.so

# Install brms
conda install -c conda-forge r-brms
```



Start an R session and test if `brms` works:

```
R
library(brms)
fit1 <- brms::brm(count ~ zAge + zBase * Trt + (1|patient), data = epilepsy, family = poisson())
```



### Who do I talk to? ###

If you have any questions, please send an email to pol.van-rijn@ae.mpg.de.