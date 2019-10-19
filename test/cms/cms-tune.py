import os
import sys
import math
import time
import json
import random
import tempfile
import matplotlib.pyplot as plot
from countminsketch import CountMinSketch

sys.path.append("../../AxProf")
import AxProf
import AxProfTune

import opentuner
from opentuner import IntegerParameter

import numpy as np

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
    # with open(input_file_name) as f:
    #     lst = list(map(lambda l: int(l.strip()), f.readlines()))

    sketch = CountMinSketch(config["m"], config["d"])

    lst = AxProf.zipfGenerator(config["n"], config["skew"], int(time.time() * 1000) % 2 ** 32)

    # measure the running time
    startTime = time.time()
    for num in lst: sketch.add(num)
    endTime = time.time()

    actual_map = actual_count(lst)
    error_map = {}

    for num in set(lst):
        error_map[num] = abs(actual_map[num] - sketch[num])

    return {
        "input": lst,
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

def tune(args, n, eps, delta, skew, m_range, d_range, tune_run=100, spec_run=100, save=None, label=""):
    results = AxProfTune.AxProfTune(
        args,
        {"n": n, "eps": eps, "delta": delta, "skew": skew}, [
            IntegerParameter("m", m_range[0], m_range[1]),
            IntegerParameter("d", d_range[0], d_range[1]),
        ],
        [1 - delta], tune_run, spec_run,
        AxProf.zipfGenerator, input_params, runner, spec, acc_metric,
    )

    opt_config = results[0][1]
    opt_m, opt_d = opt_config["m"], opt_config["d"]

    if save is not None:
        fd, fname = tempfile.mkstemp(
            suffix=".json",
            prefix="dp-n-{}-eps-{}-delta-{}-zipf-{}-".format(n, eps, delta, skew),
            dir=save,
        )

        f = os.fdopen(fd, "w")

        f.write(json.dumps({
            "n": n,
            "eps": eps,
            "delta": delta,
            "skew": skew,
            "m_range": m_range,
            "d_range": d_range,
            "tune_run": tune_run,
            "spec_run": spec_run,
            "opt_m": opt_m,
            "opt_d": opt_d,
            "label": label,
        }))

        f.close()

        print("saved:", fname)

    return opt_m, opt_d

def draw_dp(dir, x_key, y_key, label_keys, filter_func=None):
    files = []

    for root, _, fs in os.walk(dir):
        files += list(map(lambda name: root + "/" + name, filter(lambda name: name.endswith(".json"), fs)))

    datapoints = []

    for file_name in files:
        with open(file_name) as f:
            datapoints.append(json.loads(f.read()))

    if filter_func is not None:
        datapoints = list(filter(filter_func, datapoints))

    groups = {}

    for datapoint in datapoints:
        label = []

        for label_key in label_keys:
            label.append((label_key, datapoint[label_key]))

        label = tuple(label)

        if label not in groups:
            groups[label] = {
                "xs": [],
                "ys": [],
            }

        if isinstance(x_key, tuple):
            groups[label]["xs"].append(x_key[1](datapoint))
        else:
            groups[label]["xs"].append(datapoint[x_key])
    
        if isinstance(y_key, tuple):
            groups[label]["ys"].append(y_key[1](datapoint))
        else:
            groups[label]["ys"].append(datapoint[y_key])

    plot.title("{} against {}".format(y_key, x_key))

    for label in groups:
        plot.scatter(groups[label]["xs"], groups[label]["ys"], marker=".", label=label)
    
    plot.legend()
    plot.show()

if __name__ == '__main__':
    argparser = opentuner.default_argparser()
    
    argparser.add_argument("--cms-save", default="output")
    argparser.add_argument("--cms-eps", default="0.05:0.05:1")
    argparser.add_argument("--cms-delta", default="0.05:0.05:1")
    argparser.add_argument("--cms-skew", default="1.1:1.1:1")
    argparser.add_argument("--cms-n", default="10000:10000:1")
    argparser.add_argument("--cms-m-range", default="1:100")
    argparser.add_argument("--cms-d-range", default="1:10")
    argparser.add_argument("--cms-tune-run", default=100, type=int)
    argparser.add_argument("cms_label")

    args = argparser.parse_args()

    # error: 0.05 - 0.2, 100
    # skew: 1.1 - 2, 10
    # fix delta: 0.05
    # 3 min for each run
    # 5 sets of data for variance

    eps_space = np.linspace(*map(float, args.cms_eps.split(":")))
    delta_space = np.linspace(*map(float, args.cms_delta.split(":")))
    skew_space = np.linspace(*map(float, args.cms_skew.split(":")))
    n_space = np.linspace(*map(float, args.cms_n.split(":")))
    m_range = list(map(int, args.cms_m_range.split(":")))
    d_range = list(map(int, args.cms_d_range.split(":")))

    print("eps_space:", eps_space)
    print("delta_space:", delta_space)
    print("skew_space:", skew_space)
    print("n_space:", n_space)

    for eps in eps_space:
        for delta in delta_space:
            for skew in skew_space:
                for n in n_space:
                    opt_m, opt_d = tune(args,
                        int(n), eps, delta, skew,
                        m_range=m_range, d_range=d_range,
                        tune_run=args.cms_tune_run, spec_run=2,
                        save=args.cms_save,
                        label=args.cms_label,
                    )

                    print("opt config m = {}, d = {}".format(opt_m, opt_d))

    # draw_dp("opt-output", "delta", "opt_d", ("eps", "n"), filter_func=lambda d: d["n"] == 10001)
    # draw_dp("opt-output", "eps", ("mem", lambda dp: dp["opt_m"] * dp["opt_d"]), ("delta", "n"), filter_func=lambda d: d["n"] == 10000)
    # draw_dp("opt-output", "skew", "opt_m", ("eps", "n"), filter_func=lambda d: d["n"] == 10002)
    # draw_dp("opt-output", "delta", "opt_m", ("n"), filter_func=lambda d: d["n"] == 10001)

    # plot.subplot(1, 2, 1)
    # plot.scatter(eps_list, opt_m_list, marker=".")
    # plot.title("eps against opt_m")

    # plot.subplot(1, 2, 2)
    # plot.scatter(eps_list, opt_d_list, marker=".")
    # plot.title("eps against opt_d")

    # plot.show()

    # compare_config(100000, 0.05, 0.1, opt_m, opt_d)
