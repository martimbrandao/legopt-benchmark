import openravepy
import json
import numpy as np
from scipy.spatial import Delaunay
from scipy.spatial import ConvexHull
import os.path
#import pdb


def compute_poly_xy(robot, link_name):

  bb = robot.GetLink(link_name).ComputeLocalAABB()
  points = [[bb.pos()[0] + bb.extents()[0], bb.pos()[1] + bb.extents()[1], bb.pos()[2] - bb.extents()[2]],
            [bb.pos()[0] + bb.extents()[0], bb.pos()[1] - bb.extents()[1], bb.pos()[2] - bb.extents()[2]],
            [bb.pos()[0] - bb.extents()[0], bb.pos()[1] - bb.extents()[1], bb.pos()[2] - bb.extents()[2]],
            [bb.pos()[0] - bb.extents()[0], bb.pos()[1] + bb.extents()[1], bb.pos()[2] - bb.extents()[2]]]
  pose = openravepy.poseFromMatrix(robot.GetLink(link_name).GetTransform())
  pointsT = openravepy.poseTransformPoints(pose, points)[:,:2]
  poly = [tuple(pt) for pt in pointsT]

  return poly


def point_in_hull_of(point, poly, tolerance):

  hull = ConvexHull(poly)
  for j in range(hull.equations.shape[0]):
    if (hull.equations[j,:-1] * point).sum() + hull.equations[j,-1] > tolerance:
      return False

  return True


def get_feet_constraint_waypoints(stances_str):

  feet_constraint_waypoints = []
  for stance_str in stances_str:

    # separate string
    stance = stance_str.split(',')
    if stance[-1] == '':
      stance = stance[:-1]
    assert(len(stance) % 2 == 0)

    # parse poses
    link_poses = []
    for i in range(0,len(stance),2):
      link = stance[i]
      pose_target = np.fromstring(stance[i+1], sep=' ')
      mat_target = openravepy.matrixFromPose(pose_target)
      normal = mat_target[:3,2]
      pose_target[-3:] = pose_target[-3:] + normal * (0.081351 + 0.001)
      link_poses.append((link, pose_target))

    # two waypoints per stance on motion task
    feet_constraint_waypoints.append(link_poses)
    if len(stances_str) > 1:
      feet_constraint_waypoints.append(link_poses)

  return feet_constraint_waypoints


def check_feasibility(x_str, robot, env, collision_checker, feet_constraint_waypoints,
                      lower, upper, tolerance, tolerance_collision, tolerance_self_collision):

  # for each waypoint
  for i, q_str in enumerate(x_str):

    # get dofs
    q = np.fromstring(q_str, sep='\n')
    q[-4:] = q[-4:] / np.linalg.norm(q[-4:])

    # set state (and visualize)
    robot.SetActiveDOFValues(q)

    # check feet poses
    for link, pose_target in feet_constraint_waypoints[i]:
      # get current pose
      pose = openravepy.poseFromMatrix(robot.GetLink(link).GetTransform())
      # pose error and violation
      pose_target_inv = openravepy.invertPoses([pose_target])[0]
      pose_err = openravepy.poseMult(pose_target_inv, pose)[1:]
      viol = np.max(np.abs(pose_err))
      if viol > tolerance:
        return False

    # check zmp
    support_poly = []
    for link, pose_target in feet_constraint_waypoints[i]:
      support_poly = support_poly + compute_poly_xy(robot, link)
    zmp = robot.GetCenterOfMass()[:2]
    if not point_in_hull_of(zmp, support_poly, tolerance):
      return False

    # check joint limits
    if not ((lower <= q + tolerance).all() and (upper >= q - tolerance).all()):
      return False

  # check collision now
  return check_collision(x_str, robot, env, collision_checker, tolerance_collision, tolerance_self_collision)


def check_collision(x_str, robot, env, collision_checker, tolerance_collision, tolerance_self_collision):

  # for each waypoint
  for i, q_str in enumerate(x_str):

    # get dofs
    q = np.fromstring(q_str, sep='\n')
    q[-4:] = q[-4:] / np.linalg.norm(q[-4:])

    # set state (and visualize)
    robot.SetActiveDOFValues(q)

    # check collision
    collision_report = openravepy.CollisionReport()
    env.CheckCollision(robot, report=collision_report)
    collision_ok = all([contact.depth <= tolerance_collision for contact in collision_report.contacts])
    #if (not collision_ok) and solution["success"]:
    #  print('  Collision: ' + str(collision_report.plink1) + ' --- ' + str(collision_report.plink2))
    #  pdb.set_trace()
    if not collision_ok:
      return False

    # check self-collision
    self_collision_report = openravepy.CollisionReport()
    robot.CheckSelfCollision(report=self_collision_report, collisionchecker=collision_checker)
    self_collision_ok = all([contact.depth <= tolerance_self_collision for contact in self_collision_report.contacts])
    #if (not self_collision_ok) and solution["success"]:
    #  print('  Self-Collision: ' + str(self_collision_report.plink1) + ' --- ' + str(self_collision_report.plink2))
    #  depths = []
    #  for c in self_collision_report.contacts:
    #    depths.append(c.depth)
    #  all_depths.append(max(depths))
    #  pdb.set_trace()
    if not self_collision_ok:
      return False

  # all good
  return True


def evaluate(data, interactive, verbose):

  ### Parameters ###

  tolerance = 1e-3
  tolerance_collision = 1e-3
  tolerance_self_collision = 1e-3

  ### Env setup ####

  env = openravepy.RaveGetEnvironment(1)
  if env is None:
    env = openravepy.Environment()
    env.StopSimulation()
    loadsuccess = env.Load("robots/atlas_drcsim.zae")
    loadsuccess = loadsuccess and env.Load("LegOptEnv.xml")
    if interactive:
      env.SetViewer('qtcoin')

  robot = env.GetRobots()[0]
  robot.SetDOFValues(np.zeros(robot.GetDOF()))
  robot.SetActiveDOFs(np.arange(robot.GetDOF()), openravepy.DOFAffine.Transform)

  # ignore collisions between pelvis and upper-torso
  # (most algorithms use convex hull collision checks so these two would always be in collision)
  q = np.zeros(robot.GetDOF())
  q[0] = 20 * 3.1415 / 180
  q[2] = 20 * 3.1415 / 180
  robot.SetDOFValues(q)
  robot.SetNonCollidingConfiguration()

  # collision checker
  collision_checker = openravepy.RaveCreateCollisionChecker(env,'ode')
  collision_checker.SetCollisionOptions(openravepy.CollisionOptions.Contacts | openravepy.CollisionOptions.AllLinkCollisions)
  env.SetCollisionChecker(collision_checker)

  # joint limits
  lower,upper = robot.GetActiveDOFLimits()
  lower[-7:] = -np.Inf
  upper[-7:] = np.Inf

  ### Check solutions ###

  all_depths = []

  method_results = {}

  for problem in data["problems"]:

    # check necessary json data
    if "solution" not in problem:
      continue
    if "definition" not in problem:
      continue
    if "id" not in problem:
      continue

    # get target feet poses (for each waypoint)
    feet_constraint_waypoints = get_feet_constraint_waypoints(problem["definition"])

    # for all solutions (e.g. obtained with different methods/parameters/initializations)
    for solution in problem["solution"]:

      # check necessary json data
      if "x" not in solution:
        continue
      if "method" not in solution:
        continue

      # read solution
      x_str = solution["x"]
      constraints_ok = True
      sum_cost = 0
      sum_time = solution["timeSec"]

      # check solution length
      if len(feet_constraint_waypoints) != len(x_str):
        print('Warning: Number of waypoints should be twice the number of stances')
        constraints_ok = False

      # report
      if verbose:
        print('Checking feasibilty for problem ' + str(problem["id"]) + ' [Using ' + solution["method"] + ']')

      # check feasibility
      constraints_ok = constraints_ok and check_feasibility(x_str, robot, env, collision_checker,
                                                            feet_constraint_waypoints, lower, upper,
                                                            tolerance, tolerance_collision,
                                                            tolerance_self_collision)

      # get costs
      for i, q_str in enumerate(x_str):

        # stop if already infeasible
        if not constraints_ok:
          break

        # get dofs
        q = np.fromstring(q_str, sep='\n')
        q[-4:] = q[-4:] / np.linalg.norm(q[-4:])

        # set state (and visualize)
        robot.SetActiveDOFValues(q)

        # check cost
        if len(feet_constraint_waypoints) == 1:
          torques = robot.ComputeInverseDynamics(None)
          cost = sum(torques**2)
          #cost = sum((torques/9.81)**2) # this is similar to what is on trajopt
        elif i > 0:
          cost = np.sum( (q[:-7] - q_prev[:-7]) ** 2 )
        else:
          cost = 0
        sum_cost = sum_cost + cost

        # store q for later
        q_prev = q

      # check consistency
      if "success" in solution:
        if not constraints_ok and solution["success"]:
          print('Warning: Your solution is infeasible but you marked otherwise')
        if constraints_ok and not solution["success"]:
          print('Warning: Your solution is feasible but you marked otherwise')

      # save
      if solution["method"] not in method_results:
        method_results[solution["method"]] = []
      num_waypoints = len(feet_constraint_waypoints)
      method_results[solution["method"]].append([problem["id"], constraints_ok, sum_cost/num_waypoints, sum_time/num_waypoints])

  print('max selfcollision depth = ' + (str(max(all_depths)) if len(all_depths)>0 else 'none'))

  return method_results


if __name__ == "__main__":

  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("path")
  parser.add_argument("--interactive", action="store_true")
  parser.add_argument("--verbose", action="store_true")
  args = parser.parse_args()

  # read file
  assert os.path.isfile(args.path)
  with open(args.path) as data_file:
    data = json.load(data_file)

  # evaluate
  method_results = evaluate(data, args.interactive, args.verbose)

  # display
  for method in method_results:
    results = np.array(method_results[method])
    ids = results[:,0]
    successes = results[:,1]
    costs = results[:,2]
    if len(np.unique(ids)) != results.shape[0]:
      print('Warning: The same method is being applied more than once to some problems')
      continue
    stats = [np.sum(successes), np.mean(costs[successes==True]) if successes.any() else np.nan]
    print("%-70s " % (method + ':') + str(stats))

