import json
import numpy as np
import os.path


def check_unique_inittype(jsonroot):

  for problem in jsonroot["problems"]:
    if "solution" not in problem:
      continue

    for solution in problem["solution"]:
      if "initType" not in solution:
        return (False,"")
      if "initType" not in locals():
        initType = solution["initType"]
      elif initType != solution["initType"]:
        return (False, "")

  return (True, initType)


def check_valid(jsonroot):

  for problem in jsonroot["problems"]:
    if "solution" not in problem:
      return False
    if "definition" not in problem:
      return False
    if "id" not in problem:
      return False

    for solution in problem["solution"]:
      if "x" not in solution:
        return False
      if "method" not in solution:
        return False
      if "initType" not in solution:
        return False

  return True


def merge_json(base_path, tomerge_paths):

  print("Merging JSON files...")

  ### Read base data ###

  assert os.path.isfile(base_path)
  with open(base_path) as base_data_file:
    base_data = json.load(base_data_file)
  assert check_valid(base_data)

  base_initType_ok, base_initType = check_unique_inittype(base_data)
  assert base_initType_ok

  ### Merge files ###

  merged_data = base_data

  # for each file
  for tomerge_path in tomerge_paths:

    # read file
    assert os.path.isfile(tomerge_path)
    with open(tomerge_path) as data_file:
      data = json.load(data_file)
    assert check_valid(data)

    # check both files use the same method initialization (limitation)
    initType_ok, initType = check_unique_inittype(data)
    assert initType_ok and initType == base_initType

    # for each problem
    for problem2 in data["problems"]:

      # find the same problem on base file
      for p in range(len(base_data["problems"])):
        problem1 = base_data["problems"][p]
        if problem1["id"] == problem2["id"] and problem1["definition"] == problem2["definition"]:

          # for each solution
          for solution2 in problem2["solution"]:

            # check whether it was generated with new method (no solution with same method yet)
            method_is_new = True
            for solution1 in problem1["solution"]:
              if solution1["method"] == solution2["method"] and solution1["initType"] == solution2["initType"]:
                method_is_new = False

            # add solution
            if method_is_new:
              merged_data["problems"][p]["solution"].append(solution2)

  return merged_data


if __name__ == "__main__":

  # default paths
  base_path = "solutions/solutions12-full-with-easy-and-hard-init/init-nominal/goodStances.problemsposture.solutions.MySQP.json"
  tomerge_paths = [
    "solutions/solutions12-full-with-easy-and-hard-init/init-nominal/goodStances.problemsposture.solutions.SGD.json",
    "solutions/solutions12-full-with-easy-and-hard-init/init-nominal/goodStances.problemsposture.solutions.Adam.json",
    "solutions/solutions12-full-with-easy-and-hard-init/init-nominal/goodStances.problemsposture.solutions.Nadam.json",
  ]

  # merge
  merged_data = merge_json(base_path, tomerge_paths)

  # save to file
  with open("merged.json", "w") as outfile:
    json.dump(merged_data, outfile)

