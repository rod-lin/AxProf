import sys
import math
import time
import random
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
        [ abs(count(i, Input) - Output[i]) > eps * len(Input) ] < 1 - delta
"""

def ln(x):
    return math.log(x, math.e)

def count(i, lst):
    c = 0

    for j in lst:
        if j == i: c += 1

    return c

def input_params(config, inputNum):
    return [config["n"], 0, 999]

def runner(input_file_name, config):
    # read the list of integers
    with open(input_file_name) as f:
        lst = list(map(lambda l: int(l.strip()), f.readlines()))

    sketch = CountMinSketch(config["m"], config["d"])

    # measure the running time
    startTime = time.time()
    for num in lst: sketch.add(num)
    endTime = time.time()

    result = {}

    for num in lst:
        result[num] = sketch[num]

    return {
        "acc": result,
        "time": endTime - startTime,
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
def accMetric(input, output, params):
    err_count = 0
    unique = set(input)

    for i in unique:
        actual = count(i, input)
        if abs(actual - output[i]) > params["eps"] * len(input):
            err_count += 1

    return 1 - err_count / len(unique)

if __name__ == '__main__':
    argparser = opentuner.default_argparser()
    args = argparser.parse_args()

    results = AxProfTune.AxProfTune(
        args,
        {"n": 50000, "eps": 0.001, "delta": 0.95}, [
            IntegerParameter("m", 1, 1000),
            IntegerParameter("d", 1, 10),
        ],
        [0.95], 3, 20,
        uniformIntegerGenerator, input_params, runner, spec, accMetric,
    )

    print(results)
