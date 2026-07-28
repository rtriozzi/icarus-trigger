import numpy
import matplotlib

def DrawBoxes(
  ax, 
  edges, 
  mc_values,
  mc_errors,
  color='C2', 
  alpha=0.3, 
  zorder=0, 
  label=''
):
    
  edges = numpy.asarray(edges)
  mc_values = numpy.asarray(mc_values)
  mc_errors = numpy.asarray(mc_errors)

  N = len(edges) - 1
  assert mc_values.shape[0] == N
  assert mc_errors.shape == (2, N)

  for i in range(N):
    x0 = edges[i]
    width = edges[i+1] - edges[i]

    lower = mc_errors[0, i]
    upper = mc_errors[1, i]

    y0 = mc_values[i] - lower
    height = lower + upper

    rect = matplotlib.patches.Rectangle(
        (x0, y0), width, height,
        facecolor=color, edgecolor=color,
        alpha=alpha, zorder=zorder,
        label=label if i == 0 else None
    )
    ax.add_patch(rect)