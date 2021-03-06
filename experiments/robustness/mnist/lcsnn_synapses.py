import os
import torch
import argparse
import numpy as np

from time import time as t

from bindsnet.analysis.plotting import plot_locally_connected_weights
from bindsnet.learning import NoOp
from bindsnet.datasets import MNIST
from bindsnet.encoding import poisson
from bindsnet.network import load_network
from bindsnet.network.monitors import Monitor

from experiments import ROOT_DIR
from experiments.utils import update_curves, print_results


data_path = os.path.join(ROOT_DIR, 'data', 'MNIST')
results_path = os.path.join(ROOT_DIR, 'results', 'mnist', 'crop_locally_connected')


def main(seed=0, p_destroy=0):

    model = '0_16_2_250_4_0.01_0.99_60000_250.0_250_1.0_0.05_1e-07_0.5_0.2_10_250.pt'

    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_default_tensor_type('torch.cuda.FloatTensor')
    torch.cuda.manual_seed_all(seed)

    crop = 4
    time = 250
    n_filters = 250
    intensity = 0.5
    n_examples = 10000
    n_classes = 10

    # Load network.
    network = load_network(
        os.path.join(
            ROOT_DIR, 'params', 'mnist', 'crop_locally_connected', model
        ), learning=False
    )

    network.connections['X', 'Y'].update_rule = NoOp(
        connection=network.connections['X', 'Y'], nu=network.connections['X', 'Y'].nu
    )
    network.layers['Y'].theta_decay = 0
    network.layers['Y'].theta_plus = 0
    network.connections['X', 'Y'].norm = None

    for l in network.layers:
        network.layers[l].dt = network.dt

    for c in network.connections:
        network.connections[c].dt = network.dt

    network.layers['Y'].lbound = None
    network.layers['Y'].one_spike = True

    # Destroy `p_destroy` percentage of synapses (set to 0).
    mask = torch.bernoulli(p_destroy * torch.ones(network.connections['X', 'Y'].w.size())).byte()
    network.connections['X', 'Y'].w[mask] = 0

    conv_size = network.connections['X', 'Y'].conv_size
    conv_prod = int(np.prod(conv_size))
    n_neurons = n_filters * conv_prod

    # Voltage recording for excitatory and inhibitory layers.
    voltage_monitor = Monitor(network.layers['Y'], ['v'], time=time)
    network.add_monitor(voltage_monitor, name='output_voltage')

    # Load MNIST data.
    dataset = MNIST(path=data_path, download=True, shuffle=True)

    images, labels = dataset.get_test()
    images *= intensity
    images = images[:, crop:-crop, crop:-crop]

    update_interval = 250

    # Record spikes during the simulation.
    spike_record = torch.zeros(update_interval, time, n_neurons)

    # Neuron assignments and spike proportions.
    path = os.path.join(
        ROOT_DIR, 'params', 'mnist', 'crop_locally_connected', f'auxiliary_{model}'
    )
    assignments, proportions, rates, ngram_scores = torch.load(open(path, 'rb'))

    # Sequence of accuracy estimates.
    curves = {'all': [], 'proportion': [], 'ngram': []}
    predictions = {
        scheme: torch.Tensor().long() for scheme in curves.keys()
    }

    spikes = {}
    for layer in set(network.layers):
        spikes[layer] = Monitor(network.layers[layer], state_vars=['s'], time=time)
        network.add_monitor(spikes[layer], name=f'{layer}_spikes')

    start = t()
    for i in range(n_examples):
        if i % 10 == 0:
            print(f'Progress: {i} / {n_examples} ({t() - start:.4f} seconds)')
            start = t()

        if i % update_interval == 0 and i > 0:
            if i % len(labels) == 0:
                current_labels = labels[-update_interval:]
            else:
                current_labels = labels[i % len(images) - update_interval:i % len(images)]

            # Update and print accuracy evaluations.
            curves, preds = update_curves(
                curves, current_labels, n_classes, spike_record=spike_record, assignments=assignments,
                proportions=proportions, ngram_scores=ngram_scores, n=2
            )
            print_results(curves)

            for scheme in preds:
                predictions[scheme] = torch.cat([predictions[scheme], preds[scheme]], -1)

        # Get next input sample.
        image = images[i % len(images)].contiguous().view(-1)
        sample = poisson(datum=image, time=time, dt=1)
        inpts = {'X': sample}

        # Run the network on the input.
        network.run(inpts=inpts, time=time)

        retries = 0
        while spikes['Y'].get('s').sum() < 5 and retries < 3:
            retries += 1
            image *= 2
            sample = poisson(datum=image, time=time, dt=1)
            inpts = {'X': sample}
            network.run(inpts=inpts, time=time)

        # Add to spikes recording.
        spike_record[i % update_interval] = spikes['Y'].get('s').t()

        network.reset_()  # Reset state variables.

    print(f'Progress: {n_examples} / {n_examples} ({t() - start:.4f} seconds)')

    i += 1

    if i % len(labels) == 0:
        current_labels = labels[-update_interval:]
    else:
        current_labels = labels[i % len(images) - update_interval:i % len(images)]

    # Update and print accuracy evaluations.
    curves, preds = update_curves(
        curves, current_labels, n_classes, spike_record=spike_record, assignments=assignments,
        proportions=proportions, ngram_scores=ngram_scores, n=2
    )
    print_results(curves)

    for scheme in preds:
        predictions[scheme] = torch.cat([predictions[scheme], preds[scheme]], -1)

    print('Average accuracies:\n')
    for scheme in curves.keys():
        print('\t%s: %.2f' % (scheme, float(np.mean(curves[scheme]))))

    # Save results to disk.
    results = [
        np.mean(curves['all']), np.mean(curves['proportion']), np.mean(curves['ngram']),
        np.max(curves['all']), np.max(curves['proportion']), np.max(curves['ngram'])
    ]

    to_write = [str(x) for x in [seed, p_destroy] + results]
    name = 'synapse_robust.csv'

    if not os.path.isfile(os.path.join(results_path, name)):
        with open(os.path.join(results_path, name), 'w') as f:
            f.write(
                'random_seed,p_destroy\n'
            )

    with open(os.path.join(results_path, name), 'a') as f:
        f.write(','.join(to_write) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', default=0, type=int)
    parser.add_argument('--p_destroy', default=0, type=float)
    args = parser.parse_args()
    args = vars(args)
    main(**args)
