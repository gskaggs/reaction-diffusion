#!/bin/bash

python3 run_simulation.py --param_search \
-t 1 -T 3000 \
-p_a 0 1 10 \
-p_a0 0 0 1 \
-u_a 0 .5 3 \
-p_h 0 1 10 \
-p_h0 0 0 1 \
-u_h 0 .5 3 \
-kappa 0 .54 2 \
--dirichlet_vis