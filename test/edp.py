import random
import sys
import time
import math

sys.path.append("../AxProf")
import AxProf

config_list = {"n": [1000, 10000], "eps": [0.4, 0.3, 0.2, 0.1, 0.05], "c": [1]}

spec_positive = """
    Input list of real;
    Output real;
    TIME (n ^ 0.5) / eps;
    ACC Probability over runs [Output == 1] == 1
"""

spec_negative = """
    Input list of real;
    Output real;
    TIME (n ^ 0.5) / eps;
    ACC Probability over runs [Output == 0] >= 0.75
"""

def far_from_distinct(config, lst):
    lst.sort()

    dup = 0
    hset = set()

    for e in lst:
        if e in hset:
            dup += 1
        
        hset.add(e)

    return dup >= config["eps"] * len(lst)

def input_params(config, inputNum):
    return [config["n"], config["eps"]]

def runner(input_file_name, config):
    # read list
    with open(input_file_name) as f:
        lst = list(map(lambda l: int(l.strip()), f.readlines()))

    # measure the running time
    startTime = time.time()
    is_distinct = edp(lst, config["eps"], config["c"])
    endTime = time.time()

    # print(is_distinct, far_from_distinct(config, lst))

    # print(endTime - startTime, len(lst))

    return {
        "acc": is_distinct,
        "time": endTime - startTime,
        "space": 0,
    }

def edp(lst, eps, c):
    # sample c * sqrt(n) / eps elements
    sample_size = min(len(lst), int(c * (len(lst) ** 0.5) / eps))

    hset = set()

    # sample without replacement
    for e in random.sample(lst, sample_size):
        if e in hset:
            return 0.0

        hset.add(e)

    return 1.0

def gen_positives(n, eps, seed=None):
    # generate a list of distinginct integers
    random.seed(seed)
    return random.sample(range(0, 2 * n), n)

def gen_negatives(n, eps, seed=None):
    # generate a list of integers with more than eps * n duplicates
    lst = gen_positives(n, eps, seed)

    # sample n * eps elements and make them the same
    eps_n = int(math.ceil(n * eps)) + 1

    while not far_from_distinct({"n": n, "eps": eps}, lst):
        for i in range(eps_n):
            i, j = random.sample(range(len(lst)), 2)
            lst[i] = lst[j]
    
    return lst

if __name__ == '__main__':
    # check positives
    AxProf.checkProperties(
        config_list, None, 1,
        gen_positives,
        input_params, runner, spec=spec_positive,
    )

    # check negatives
    AxProf.checkProperties(
        config_list, None, 1,
        gen_negatives,
        input_params, runner, spec=spec_negative,
    )
