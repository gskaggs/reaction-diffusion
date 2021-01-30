#!/usr/bin/env python3

import matplotlib.pyplot as plt

from grey_scott import grey_scott

gs = grey_scott()

fig = plt.figure()
ax = plt.contourf(gs.x,gs.y,gs.a)
plt.pause(0.05)

for k in range(100):
  gs.update()
  ax = plt.contourf(gs.x,gs.y,gs.a)
  plt.pause(0.05)

plt.show()
