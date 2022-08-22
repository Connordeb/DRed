
if(NOT "/home/connor/PycharmProjects/final/glog-python-master/build/git-glog-prefix/src/git-glog-stamp/git-glog-gitinfo.txt" IS_NEWER_THAN "/home/connor/PycharmProjects/final/glog-python-master/build/git-glog-prefix/src/git-glog-stamp/git-glog-gitclone-lastrun.txt")
  message(STATUS "Avoiding repeated git clone, stamp file is up to date: '/home/connor/PycharmProjects/final/glog-python-master/build/git-glog-prefix/src/git-glog-stamp/git-glog-gitclone-lastrun.txt'")
  return()
endif()

execute_process(
  COMMAND ${CMAKE_COMMAND} -E remove_directory "/home/connor/PycharmProjects/final/glog-python-master/build/glog"
  RESULT_VARIABLE error_code
  )
if(error_code)
  message(FATAL_ERROR "Failed to remove directory: '/home/connor/PycharmProjects/final/glog-python-master/build/glog'")
endif()

# try the clone 3 times in case there is an odd git clone issue
set(error_code 1)
set(number_of_tries 0)
while(error_code AND number_of_tries LESS 3)
  execute_process(
    COMMAND "/usr/bin/git"  clone --no-checkout "https://github.com/karmaresearch/glog.git" "glog"
    WORKING_DIRECTORY "/home/connor/PycharmProjects/final/glog-python-master/build"
    RESULT_VARIABLE error_code
    )
  math(EXPR number_of_tries "${number_of_tries} + 1")
endwhile()
if(number_of_tries GREATER 1)
  message(STATUS "Had to git clone more than once:
          ${number_of_tries} times.")
endif()
if(error_code)
  message(FATAL_ERROR "Failed to clone repository: 'https://github.com/karmaresearch/glog.git'")
endif()

execute_process(
  COMMAND "/usr/bin/git"  checkout origin/compressed_provenance --
  WORKING_DIRECTORY "/home/connor/PycharmProjects/final/glog-python-master/build/glog"
  RESULT_VARIABLE error_code
  )
if(error_code)
  message(FATAL_ERROR "Failed to checkout tag: 'origin/compressed_provenance'")
endif()

set(init_submodules TRUE)
if(init_submodules)
  execute_process(
    COMMAND "/usr/bin/git"  submodule update --recursive --init 
    WORKING_DIRECTORY "/home/connor/PycharmProjects/final/glog-python-master/build/glog"
    RESULT_VARIABLE error_code
    )
endif()
if(error_code)
  message(FATAL_ERROR "Failed to update submodules in: '/home/connor/PycharmProjects/final/glog-python-master/build/glog'")
endif()

# Complete success, update the script-last-run stamp file:
#
execute_process(
  COMMAND ${CMAKE_COMMAND} -E copy
    "/home/connor/PycharmProjects/final/glog-python-master/build/git-glog-prefix/src/git-glog-stamp/git-glog-gitinfo.txt"
    "/home/connor/PycharmProjects/final/glog-python-master/build/git-glog-prefix/src/git-glog-stamp/git-glog-gitclone-lastrun.txt"
  RESULT_VARIABLE error_code
  )
if(error_code)
  message(FATAL_ERROR "Failed to copy script-last-run stamp file: '/home/connor/PycharmProjects/final/glog-python-master/build/git-glog-prefix/src/git-glog-stamp/git-glog-gitclone-lastrun.txt'")
endif()

