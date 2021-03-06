# BindsNET Experiments

Collection of experimental Python and accompanying Bash scripts for training and evaluation of BindsNET networks.
Created for BINDS Lab experiments, specifically geared towards the
[swarm2](https://people.cs.umass.edu/~swarm/index.php?n=Main.NewSwarmDoc) and
[gypsum](http://maxwell.cs.umass.edu/gypsum/index.php?n=Main.UserDoc) clusters.

## Scripts

Python scripts for running training and test phases of spiking neural network (SNN) experiments on various machine
learning datasets and reinforcement learning environments. To run training with default parameters for any script, issue

```bash
python [script_name]
```

followed by

```bash
python [script_name] --test
```

for the test phase. To modify `argparse` parameters,

```bash
python [script_name] --[param1_name] [param1_value] --[param2_name] [param2_value] ...
```

followed by

```bash
python [script_name] --test --[param1_name] [param1_value] --[param2_name] [param2_value] ...
```

The order of command-line arguments doesn't matter.

At the time of writing, this repository has experiments for the MNIST, CIFAR-10, and Fashion-MNIST datasets, a custom
dataset comprised of Atari Breakout game frames paired with a trained DQN's actions (data on request), and the Atari
Breakout reinforcement learning environment itself.

## Bash scripts

In the `bash/` directory are scripts for launching jobs on the `swarm2` (CPU) and `gypsum` (GPU) clusters at UMass
Amherst. The `submit.sh` scripts are used for launching individual train + test jobs (and `test.sh` for individual test
jobs, typically used when the training phase succeeds but the test phase fails for some reason), while the
`grid_search.sh` scripts are used to launch a large number of train + test jobs by searching over a user-specified
grid of hyper-parameters.

## Data

The `data/` directory is where experimental scripts point to in order to store datasets in the pickled PyTorch format.

## Confusion, curves, params, plots, results

- `confusion/`: Saving of confusion matrices plotted at the end of both train and test phases of SNN experiments.
- `curves/`: Accuracy curves for both train and test phases of SNN experiments involving classification.
- `params/`: Saved trained `bindsnet.network.Network` objects and auxiliary variables; e.g., labels of neurons or
average firing rate of neurons over training phase.
- `plots/`: Plots of variables network state variables or classification outcomes.
- `results/`: Averaged and maximum train and test accuracy results from SNN experiments involving classification.