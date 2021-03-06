#!/usr/bin/env python3
# File       : run_simulation.py
# Created    : Sat Jan 30 2021 09:13:51 PM (+0100)
# Description: Gray-Scott driver.  Use the --help argument for all options
# Copyright 2021 ETH Zurich. All Rights Reserved.
import argparse
import pickle
import os

from python.init_utils import prep_sim, init_chromosomes, param_names, load_args
from python.present_utils import present_chromosomes
from python.simulator import ReactionDiffusionSimulator
from python.ga import apply_selection, set_fitness
from python.process_util import start_processes
from python.process_util import end_processes
from datetime import timedelta
import time
import psutil

def parse_args():
    """
    Driver arguments.  These are passed to the ReactionDiffusionSimulator class
    """
    parser = argparse.ArgumentParser()
    global param_names
    for name in param_names:
        parser.add_argument('-' + name, default=[0, 0, 1], type=float, nargs='+')

    parser.add_argument('-num_iters', default=1, type=int, help='How many generations of ga to run.')
    parser.add_argument('-num_generalized', default=0, type=int, help='How big the population of generalized chromosomes is.')
    parser.add_argument('-num_individuals', default=50, type=int, help='How big the population of chromosomes is.')
    parser.add_argument('-fitness', default='dirichlet', type=str, help='The kind of fitness function to use.')
    parser.add_argument('-rd', default=['gray_scott'], type=str, nargs='+', help='The kind of reaction diffussion equation to use.')

    parser.add_argument('-N', default=256, type=int, help='Final time')
    parser.add_argument('-T', '--end_time', default=200, type=float, help='Final time')
    parser.add_argument('--param_search', action='store_true', help='Run param search')
    parser.add_argument('--resume_file', default='resume.pkl', type=str, help='Where intermediate program values should be stored for genetic algorithm')
    parser.add_argument('--init', default='trefethen', type=str, help='Where intermediate program values should be stored for genetic algorithm')
    parser.add_argument('--resume', action='store_true', help='Restart a simulation with a given setup stored in --resume_file')
    parser.add_argument('--genetic_algorithm', action='store_true', help='Run genetic algorithm')
    parser.add_argument('--test_speed', action='store_true', help='Run genetic algorithm')
    parser.add_argument('--outdir', default='.', type=str, help='Output directory')
    parser.add_argument('--dirichlet_vis', action='store_true', default=False, help='Visualize gradient side by side with sims')
    parser.add_argument('--use_cpu', action='store_true', default=False, help='Use cpu instead of gpu for sims')
    parser.add_argument('-t', '--num_processes', default=6, type=int, help='Number of threads for the simulation')
    return parser.parse_known_args()

def process_function_ga(chromosomes, modified, args):
    while True:
        c = chromosomes.get()
        if c == 'DONE':
            break

        sim = ReactionDiffusionSimulator(chromosome=c, movie=False, outdir="./garbage", initial_condition=args.init, N=args.N, use_cpu=args.use_cpu,rd_types=args.rd)
        pattern, latest, image = sim.integrate(args.end_time, dirichlet_vis=args.dirichlet_vis, fitness=args.fitness) 
        c.fitness = latest
        c.pattern = pattern
        c.image   = image
        modified.put(c)

    modified.put('DONE')


def run_generation(chromosomes, cur_iter, args):
    # Prepare process safe queues
    chromosomes, modified = prep_sim(chromosomes, cur_iter, args)

    # Do the simulations
    start = time.time()
    processes = start_processes(args.num_processes, process_function_ga, (chromosomes, modified, args))
    chromosomes = end_processes(processes, modified, args.num_processes)
    end = time.time()
    if not args.test_speed: 
        print(f'Generation {cur_iter} time taken {timedelta(seconds=end-start)}')

    # Save the results
    chromosomes.sort(key=lambda c: -c.fitness) # sorted by decreasing fitness
    if not args.test_speed:
        present_chromosomes(chromosomes, cur_iter, args)

    return chromosomes


def get_preferred():
    return [1]


def resume_ga(args):
    chromosomes = init_chromosomes(args)
    cur_iter, num_iters = 1, args.num_iters
    
    if os.path.exists(args.resume_file):
        with open(args.resume_file, 'rb') as file:
            chromosomes, cur_iter, num_iters = pickle.load(file)
            preferred = get_preferred()
            set_fitness(chromosomes, preferred)  
            chromosomes = apply_selection(chromosomes)
    else:
        with open(args.resume_file, 'w') as file:
            # Just making the file for now
            pass
    
    chromosomes = run_generation(chromosomes, cur_iter, args)

    with open(args.resume_file, 'wb') as file:
        pickle.dump((chromosomes, cur_iter+1, num_iters), file)


def genetic_algorithm(args):
    chromosomes = init_chromosomes(args)
    num_iters = args.num_iters

    for cur_iter in range(1, num_iters+1):
        chromosomes = run_generation(chromosomes, cur_iter, args)
        chromosomes = apply_selection(chromosomes)


def param_search(args):
    chromosomes = init_chromosomes(args)
    cur_iter = 1
    chromosomes = run_generation(chromosomes, cur_iter, args)


def resume_sim(args):
    chromosomes, cur_iter, args = load_args(args.resume_file)

    if args.param_search:
        param_search(args)
        return

    while cur_iter <= args.num_iters:
        chromosomes = run_generation(chromosomes, cur_iter, args)
        chromosomes = apply_selection(chromosomes)
        cur_iter += 1


def make_output_dirs(args):
    dirs = ['garbage', 'results', f'results/{args.rd}']
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)

def test_speed(args):
    rds = [['gray_scott'], ['gierer_mienhardt'], ['generalized']]
    reps = 1
    args.end_time = 500
    args.num_individuals = 20
    for rd in rds:
        print('Model', rd[0])
        if rd[0] != 'gray_scott':
            args.end_time = 20
        args.rd = rd

        # GPU
        start = time.time()
        args.use_cpu = False
        for _ in range(reps):
            param_search(args)
        end = time.time()

        print(f'GPU took {timedelta(seconds=(end-start)/reps)}')
       
        # CPU-16
        start = time.time()
        args.use_cpu = True
        args.num_processes = 6
        for _ in range(reps):
            param_search(args)
        end = time.time()

        print(f'CPU-{args.num_processes} took {timedelta(seconds=(end-start)/reps)}')

        # CPU-16
        start = time.time()
        args.use_cpu = True
        args.num_processes = 1
        for _ in range(reps):
            param_search(args)
        end = time.time()

        print(f'CPU-{args.num_processes} took {timedelta(seconds=(end-start)/reps)}')


def main():
    args, _ = parse_args()

    print(f'thread count per core: {psutil.cpu_count() // psutil.cpu_count(logical=False)}')
    print(f"Num cores = {psutil.cpu_count(logical=False)}")
    print(f'Num_processes = {args.num_processes}')

    make_output_dirs(args)
    if args.test_speed:
        test_speed(args)
        return

    if args.num_generalized and 'generalized' not in args.rd:
        args.rd.append('generalized')

    if args.resume:
        resume_sim(args)
        return

    if args.param_search:
        param_search(args)
        return

    if args.genetic_algorithm and args.fitness == 'user':
        resume_ga(args)
        return

    if args.genetic_algorithm:
        genetic_algorithm(args)
        return

    print('Sim type not specified')

if __name__ == "__main__":
    main()
