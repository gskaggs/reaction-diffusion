#!/bin/bash

python3 run_simulation.py --param_search \
-rd gierer_mienhardt \
-t 6 -T 2600 \
-rho .5 \
-mu 1 \
-nu .9 \
-kappa .238 \
--dirichlet_vis