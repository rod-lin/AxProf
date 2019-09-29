import sys
import math
import time
import random
import matplotlib.pyplot as plot
from countminsketch import CountMinSketch

sys.path.append("../AxProf")
import AxProf
import AxProfTune

import opentuner
from opentuner import IntegerParameter

# m = size of hash table
# d = number of hash tables
# n = number of element

spec = """
    Input list of real;
    Output map from real to real;
    TIME n;
    ACC Probability over i in uniques(Input)
        [ Output[i] > eps * len(Input) ] < delta
"""

def ln(x):
    return math.log(x, math.e)

def actual_count(lst):
    actual_map = {}

    for i in lst:
        if i not in actual_map:
            actual_map[i] = 0

        actual_map[i] += 1

    return actual_map

def input_params(config, inputNum):
    return [config["n"], 1.1]

def runner(input_file_name, config):
    # read the list of integers
    with open(input_file_name) as f:
        lst = list(map(lambda l: int(l.strip()), f.readlines()))

    sketch = CountMinSketch(config["m"], config["d"])

    # measure the running time
    startTime = time.time()
    for num in lst: sketch.add(num)
    endTime = time.time()

    actual_map = actual_count(lst)
    error_map = {}

    for num in set(lst):
        error_map[num] = abs(actual_map[num] - sketch[num])

    return {
        "acc": error_map,
        "time": config["m"] * config["d"], # endTime - startTime,
        "space": 0,
    }

# Samples WITH REPLACEMENT integers within [_min,_max]
def uniformIntegerGenerator(length, _min, _max, seed=None):
    lst = []

    random.seed(seed)

    for _ in range(length):
        lst.append(random.randint(_min, _max))

    return lst

# average error
def acc_metric(input, output, params):
    err_count = 0
    unique = set(input)
    actual_map = actual_count(input)

    for i in unique:
        actual = actual_map[i]
        if abs(actual - output[i]) > params["eps"] * len(input):
            err_count += 1

    return 1 - err_count / len(unique)

def plot_error(lst, m, d, color=None, label=None):
    sketch = CountMinSketch(m, d)
    actual_map = actual_count(lst)

    for i in lst: sketch.add(i)

    errors = []
    unique = set(lst)

    for i in unique:
        actual = actual_map[i]
        error = abs(actual - sketch[i])
        errors.append(error)

    print(len(errors))

    plot.hist(errors, bins=len(errors) // 100, color=color, label=label)
    plot.xlim(0, int(len(lst) * 0.1))

def compare_config(n, eps, delta, opt_m, opt_d):
    lst = AxProf.zipfGenerator(n, 1.1)

    m = math.ceil(math.e / eps)
    d = math.ceil(ln(1 / delta))

    print("m = {}, d = {}".format(m, d))
    print("tuned m = {}, d = {}".format(opt_m, opt_d))
    print("threshold {}%% of counts will have error less than {}".format((1 - delta) * 100, eps * n))


    plot_error(lst, opt_m, opt_d, color="red", label="tuned")
    plot_error(lst, m, d, color="blue", label="original")
    plot.legend()
    plot.xlabel("error")
    plot.ylabel("number of elements")
    
    plot.show()

if __name__ == '__main__':
    n = 100000
    eps = 0.05
    delta = 0.1
    
    argparser = opentuner.default_argparser()
    args = argparser.parse_args()

    results = AxProfTune.AxProfTune(
        args,
        {"n": n, "eps": eps, "delta": delta}, [
            IntegerParameter("m", 1, 1000),
            IntegerParameter("d", 1, 10),
        ],
        [1 - delta], 1, 20,
        AxProf.zipfGenerator, input_params, runner, spec, acc_metric,
    )

    opt_config = results[0][1]
    print("opt config", opt_config)

    compare_config(n, eps, delta, opt_config["m"], opt_config["d"])
