import numpy as np
from scipy.optimize import curve_fit


def model(x, a, k, c):
    return a * np.exp(-k * x) + c


params, covariance = curve_fit(model, x, y, p0=(1.0, 1.0, 0.0))
errors = np.sqrt(np.diag(covariance))
