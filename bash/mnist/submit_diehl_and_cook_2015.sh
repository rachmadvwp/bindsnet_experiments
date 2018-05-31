#!/bin/bash
#
#SBATCH --partition=longq
#SBATCH --time=02-00:00:00
#SBATCH --mem=8000
#SBATCH --account=rkozma
#SBATCH --output=../output/diehl_and_cook_2015_mnist_%j.out

seed=${1:-0}
n_neurons=${2:-100}
n_train=${3:-60000}
n_test=${4:-10000}
excite=${5:-25.0}
inhib=${6:-25.0}
time=${7:-350}

cd ../../scripts/mnist/
source activate py36

python diehl_and_cook_2015.py --train --seed $seed --n_neurons $n_neurons --n_train $n_train \
							  --n_test $n_test --excite $excite --inhib $inhib --time $time
python diehl_and_cook_2015.py --test --seed $seed --n_neurons $n_neurons --n_train $n_train \
							  --n_test $n_test --excite $excite --inhib $inhib --time $time
exit
