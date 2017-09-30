import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--interactive", action="store_true")
parser.add_argument("--verbose", action="store_true")
parser.add_argument("--veryverbose", action="store_true")
args = parser.parse_args()

from LegOptMergeJSON import merge_json
from LegOptEvalFast import evaluate
import numpy as np
import time


def filter_methods(jsonroot, method_display_names):
  newdata = jsonroot
  for problem in newdata["problems"]:
    # keep only solutions from methods on the list
    problem["solution"] = [sol for sol in problem["solution"] if sol["method"] in method_display_names]
    # change to reader-friendly names
    for solution in problem["solution"]:
      solution["method"] = method_display_names[solution["method"]]
  return newdata


if __name__ == "__main__":

  ### Default paths ###

  resultsdir = "solutions/solutions12-full-with-easy-and-hard-init"

  paths_posture_nominal = [
    resultsdir+"/init-nominal/goodStances.problemsposture.solutions.MySQP.json",
    resultsdir+"/init-nominal/goodStances.problemsposture.solutions.SGD.json",
    resultsdir+"/init-nominal/goodStances.problemsposture.solutions.Adam.json",
    resultsdir+"/init-nominal/goodStances.problemsposture.solutions.Nadam.json",
  ]
  paths_posture_nominal_hard = [
    resultsdir+"/init-nominal-hard/goodStances.problemsposture.solutions.MySQP.json",
    resultsdir+"/init-nominal-hard/goodStances.problemsposture.solutions.SGD.json",
    resultsdir+"/init-nominal-hard/goodStances.problemsposture.solutions.Adam.json",
    resultsdir+"/init-nominal-hard/goodStances.problemsposture.solutions.Nadam.json",
  ]
  paths_motion_nominal = [
    resultsdir+"/init-nominal/goodStances.problemsmotion.solutions.MySQP.json",
    resultsdir+"/init-nominal/goodStances.problemsmotion.solutions.SGD.json",
    resultsdir+"/init-nominal/goodStances.problemsmotion.solutions.Adam.json",
    resultsdir+"/init-nominal/goodStances.problemsmotion.solutions.Nadam.json",
  ]
  paths_motion_nominal_hard = [
    resultsdir+"/init-nominal-hard/goodStances.problemsmotion.solutions.MySQP.json",
    resultsdir+"/init-nominal-hard/goodStances.problemsmotion.solutions.SGD.json",
    resultsdir+"/init-nominal-hard/goodStances.problemsmotion.solutions.Adam.json",
    resultsdir+"/init-nominal-hard/goodStances.problemsmotion.solutions.Nadam.json",
  ]

  ### Default methods ###

  method_display_names = {}
  method_display_names["MySQP,SampleSizeFixed(rnd),100,Line,,,1,"] =                              "SQP     & 0 &100"
  method_display_names["SGD(SGD),SampleSizeFixed,100,StepSizeWolfe,0.9,0,0,0"] =                  "SGD     & 0 &100"
  method_display_names["SGD(Adam),SampleSizeFixed,100,StepSizeWolfe,0.9,0,0,0"] =                 "Adam    & 0 &100"
  method_display_names["SGD(Nadam),SampleSizeFixed,100,StepSizeWolfe,0.9,0,0,0"] =                "Nadam   & 0 &100"

  method_display_names["MySQP(Multistart10),SampleSizeFixed(rnd),100,Line,,,1,"] =                "SQP     &10 &100"
  method_display_names["SGD(SGD)(Multistart10),SampleSizeFixed,100,StepSizeWolfe,0.9,0,0,0"] =    "SGD     &10 &100"
  method_display_names["SGD(Adam)(Multistart10),SampleSizeFixed,100,StepSizeWolfe,0.9,0,0,0"] =   "Adam    &10 &100"
  method_display_names["SGD(Nadam)(Multistart10),SampleSizeFixed,100,StepSizeWolfe,0.9,0,0,0"] =  "Nadam   &10 &100"

  method_display_names["MySQP(Multistart10),SampleSizeFixed(rnd),80,Line,,,0,"] =                 "SQP     &10 & 80"
  method_display_names["SGD(SGD)(Multistart10),SampleSizeFixed,80,StepSizeWolfe,0.9,0,0,0"] =     "SGD     &10 & 80"
  method_display_names["SGD(Adam)(Multistart10),SampleSizeFixed,80,StepSizeWolfe,0.9,0,0,0"] =    "Adam    &10 & 80"
  method_display_names["SGD(Nadam)(Multistart10),SampleSizeFixed,80,StepSizeWolfe,0.9,0,0,0"] =   "Nadam   &10 & 80"

  method_display_names["MySQP(Multistart10),SampleSizeFixed(rnd),80,Line,,,1,"] =                 "I-SQP   &10 & 80"
# method_display_names["SGD(SGD)(Multistart10),SampleSizeFixed,80,StepSizeWolfe,0.9,0,1,0"] =     "I-SGD   &10 & 80"
# method_display_names["SGD(Adam)(Multistart10),SampleSizeFixed,80,StepSizeWolfe,0.9,0,1,0"] =    "I-Adam  &10 & 80"
# method_display_names["SGD(Nadam)(Multistart10),SampleSizeFixed,80,StepSizeWolfe,0.9,0,1,0"] =   "I-Nadam &10 & 80"
#
# method_display_names["MySQP(Multistart10),SampleSizeFixed(rnd),40,Line,,,1,"] =                 "I-SQP   &10 & 40"
  method_display_names["SGD(SGD)(Multistart10),SampleSizeFixed,40,StepSizeWolfe,0.9,0,1,0"] =     "I-SGD   &10 & 40"
  method_display_names["SGD(Adam)(Multistart10),SampleSizeFixed,40,StepSizeWolfe,0.9,0,1,0"] =    "I-Adam  &10 & 40"
  method_display_names["SGD(Nadam)(Multistart10),SampleSizeFixed,40,StepSizeWolfe,0.9,0,1,0"] =   "I-Nadam &10 & 40"

  ### Display order ###

  method_display_order = []
  method_display_order.append("SQP     & 0 &100")
  method_display_order.append("SGD     & 0 &100")
  method_display_order.append("Adam    & 0 &100")
  method_display_order.append("Nadam   & 0 &100")
  method_display_order.append("-")
  method_display_order.append("SQP     &10 &100")
  method_display_order.append("SGD     &10 &100")
  method_display_order.append("Adam    &10 &100")
  method_display_order.append("Nadam   &10 &100")
  method_display_order.append("-")
  method_display_order.append("SQP     &10 & 80")
  method_display_order.append("SGD     &10 & 80")
  method_display_order.append("Adam    &10 & 80")
  method_display_order.append("Nadam   &10 & 80")
  method_display_order.append("-")
  method_display_order.append("I-SQP   &10 & 80")
# method_display_order.append("I-SGD   &10 & 80")
# method_display_order.append("I-Adam  &10 & 80")
# method_display_order.append("I-Nadam &10 & 80")
# method_display_order.append("-")
# method_display_order.append("I-SQP   &10 & 40")
  method_display_order.append("I-SGD   &10 & 40")
  method_display_order.append("I-Adam  &10 & 40")
  method_display_order.append("I-Nadam &10 & 40")

  ### Get data from JSON files ###

  data_posture_nominal = merge_json(paths_posture_nominal[0], paths_posture_nominal[1:])
  data_posture_nominal_hard = merge_json(paths_posture_nominal_hard[0], paths_posture_nominal_hard[1:])
  data_motion_nominal = merge_json(paths_motion_nominal[0], paths_motion_nominal[1:])
  data_motion_nominal_hard = merge_json(paths_motion_nominal_hard[0], paths_motion_nominal_hard[1:])

  ### Choose what to display ###

  data_posture_nominal = filter_methods(data_posture_nominal, method_display_names)
  data_posture_nominal_hard = filter_methods(data_posture_nominal_hard, method_display_names)
  data_motion_nominal = filter_methods(data_motion_nominal, method_display_names)
  data_motion_nominal_hard = filter_methods(data_motion_nominal_hard, method_display_names)

  ### Evaluate ###

  time_start = time.clock()

  results = [
    evaluate(data_posture_nominal, args.interactive, args.verbose),
    evaluate(data_posture_nominal_hard, args.interactive, args.verbose),
    evaluate(data_motion_nominal, args.interactive, args.verbose),
    evaluate(data_motion_nominal_hard, args.interactive, args.verbose),
  ]

  print("Evaluation took %f seconds" % (time.clock() - time_start))

  ### Display ###

  for method in method_display_order:
    # separator
    if method == "-":
      print("-")
      continue

    # results for all conditions in one line: (PG nominal, PG hard, TRAJ nominal, TRAJ hard)
    line = "%s  " % method;
    for result in results:
      vec = np.array(result[method])
      ids = vec[:,0]
      successes = vec[:,1]
      costs = vec[:,2]
      times = vec[:,3]
      if len(np.unique(ids)) != vec.shape[0]:
        print('Warning: The same method is being applied more than once to some problems')
        continue
      # number of successfully solved problems
      num_succ = np.sum(successes)
      # average cost per waypoint (on successfully solved problems)
      avg_cost = np.mean(costs[successes==True]) if successes.any() else 0
      # average computation time per waypoint (on successfully solved problems)
      avg_time = np.mean(times[successes==True]) if successes.any() else 0
      # display: (success rate, cost, time)
      if avg_cost >= 1:
        line = line + ("&%-2d/50 &%-3d &%.2f " % (num_succ, np.round(avg_cost), avg_time))
      else:
        line = line + ("&%-2d/50 &%.2f &%.2f " % (num_succ, avg_cost, avg_time))
    print(line)

  ### HTML table for github ###

  result_sets = [
    [results[0], results[2]],
    [results[1], results[3]],
  ]

  for results in result_sets:
    print '<table>'
    for method in method_display_order:
      # separator
      if method == "-":
        continue
      # results for all conditions in one line: (PG nominal, PG hard, TRAJ nominal, TRAJ hard)
      line = "<tr> <td>%s</td>" % method.replace('&','</td> <td>');
      for result in results:
        vec = np.array(result[method])
        ids = vec[:,0]
        successes = vec[:,1]
        costs = vec[:,2]
        times = vec[:,3]
        if len(np.unique(ids)) != vec.shape[0]:
          print('Warning: The same method is being applied more than once to some problems')
          continue
        num_succ = np.sum(successes)
        avg_cost = np.mean(costs[successes==True]) if successes.any() else 0
        avg_time = np.mean(times[successes==True]) if successes.any() else 0
        # display: (success rate, cost, time)
        line = line + (" <td>%-2d/50</td> <td>%7.2f</td> <td>%7.2f</td>" % (num_succ, avg_cost, avg_time))
      line = line + " </tr>"
      print(line)
    print '</table>'

