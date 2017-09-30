# How to make this ZAE file:

1. make a catkin workspace "drc_ws"
2. `hg clone https://bitbucket.org/osrf/drcsim` (can delete everything except atlas_description, multisense_sl_description, tools)
3. `catkin_make`
4. `source devel/setup.bash`
5. `cd (..path_to...)/drc_ws/src/drcsim/atlas_description/robots`
6. `rosrun xacro xacro atlas.urdf.xacro > atlas.urdf`
7. `sed 's/<safety_controller[^>]*>//g' atlas.urdf > atlas_no_controller.urdf`
8. `rosrun collada_urdf urdf_to_collada atlas_no_controller.urdf atlas.zae`
