cmake_minimum_required(VERSION 3.16)
project(hg_runtime LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(MELONDS_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/../melonDS" CACHE PATH "Pinned, separately patched melonDS source checkout")
set(HG_WAIT_LOOP_TEST_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/wait_loop_test.cpp" CACHE FILEPATH "Optional companion instruction test source")
option(HG_BUILD_WAIT_LOOP_TEST "Build the companion instruction test" ON)
set(BUILD_QT_SDL OFF CACHE BOOL "" FORCE)
set(ENABLE_OGLRENDERER OFF CACHE BOOL "" FORCE)
set(ENABLE_GDBSTUB OFF CACHE BOOL "" FORCE)
set(ENABLE_JIT OFF CACHE BOOL "" FORCE)
set(ENABLE_LTO_RELEASE OFF CACHE BOOL "" FORCE)
find_package(Python3 3.9 REQUIRED COMPONENTS Interpreter)
set(HG_MELONDS_VERIFY_COMMAND
    "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/patch_core.py"
    --source "${MELONDS_SOURCE}" --verify-only
)
execute_process(
    COMMAND ${HG_MELONDS_VERIFY_COMMAND}
    RESULT_VARIABLE HG_MELONDS_VERIFY_RESULT
    OUTPUT_VARIABLE HG_MELONDS_VERIFY_STDOUT
    ERROR_VARIABLE HG_MELONDS_VERIFY_STDERR
)
if(NOT HG_MELONDS_VERIFY_RESULT EQUAL 0)
    message(FATAL_ERROR
        "Rejected melonDS source before CMake evaluation:\n"
        "${HG_MELONDS_VERIFY_STDOUT}${HG_MELONDS_VERIFY_STDERR}")
endif()
find_package(Threads REQUIRED)
add_subdirectory("${MELONDS_SOURCE}" melonds)
add_custom_target(hg_verify_melonds ALL
    COMMAND ${HG_MELONDS_VERIFY_COMMAND}
    COMMENT "Rechecking the pinned melonDS source tree"
    VERBATIM
)
function(hg_require_melonds_verification directory)
    get_property(HG_MELONDS_TARGETS DIRECTORY "${directory}" PROPERTY BUILDSYSTEM_TARGETS)
    foreach(HG_MELONDS_TARGET IN LISTS HG_MELONDS_TARGETS)
        add_dependencies("${HG_MELONDS_TARGET}" hg_verify_melonds)
    endforeach()
    get_property(HG_MELONDS_SUBDIRECTORIES DIRECTORY "${directory}" PROPERTY SUBDIRECTORIES)
    foreach(HG_MELONDS_SUBDIRECTORY IN LISTS HG_MELONDS_SUBDIRECTORIES)
        hg_require_melonds_verification("${HG_MELONDS_SUBDIRECTORY}")
    endforeach()
endfunction()
hg_require_melonds_verification("${MELONDS_SOURCE}")
target_include_directories(core PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_compile_definitions(core PRIVATE HG_RUNTIME_TRACE=1)
add_executable(hg_runtime main.cpp platform.cpp)
target_link_libraries(hg_runtime PRIVATE core Threads::Threads ${CMAKE_DL_LIBS})
if(HG_BUILD_WAIT_LOOP_TEST)
    if(NOT EXISTS "${HG_WAIT_LOOP_TEST_SOURCE}")
        message(FATAL_ERROR "Set HG_WAIT_LOOP_TEST_SOURCE to the companion scripts/wait_loop_test.cpp, or disable HG_BUILD_WAIT_LOOP_TEST")
    endif()
    add_executable(hg_wait_loop_test "${HG_WAIT_LOOP_TEST_SOURCE}" platform.cpp)
    target_link_libraries(hg_wait_loop_test PRIVATE core Threads::Threads ${CMAKE_DL_LIBS})
endif()
