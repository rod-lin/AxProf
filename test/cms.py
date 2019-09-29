import sys
import math
import time
import random
from countminsketch import CountMinSketch

sys.path.append("../AxProf")
import AxProf

# m = size of hash table
# d = number of hash tables
# n = number of element

config = {
    "n": [1000, 500],
    "eps": [0.1, 0.05],
    "delta": [0.9, 0.8],
}

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
    return [config["n"], 2]

def runner(input_file_name, config):
    # read the list of integers
    with open(input_file_name) as f:
        lst = list(map(lambda l: int(l.strip()), f.readlines()))

    m = math.ceil(math.e / config["eps"])
    d = math.ceil(ln(1 / config["delta"]))

    # print(m, d)

    sketch = CountMinSketch(m, d)

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

if __name__ == '__main__':
    AxProf.checkProperties(
        config, None, 1,
        AxProf.zipfGenerator,
        input_params, runner, spec=spec,
    )
