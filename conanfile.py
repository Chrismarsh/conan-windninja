from conans import ConanFile, CMake, tools
import os
import glob

class CHMConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
   

    name = "windninja"
    version = "3.5.3"
    license = "https://github.com/firelab/windninja/blob/master/LICENSE"
    author = "firelab"
    url = "https://github.com/firelab/windninja"
    description = "WindNinja is a diagnostic wind model developed for use in wildland fire modeling."
    generators = "cmake_find_package"

    options = {"openmp":[True, False]}

    default_options = {"openmp":False}
 

    def source(self):

        git = tools.Git()
        git.clone("https://github.com/firelab/windninja.git") 
        git.checkout("3.5.3")

        # Needed for Find OMP on MacOS
        tools.replace_in_file("CMakeLists.txt", "cmake_minimum_required(VERSION 2.6)",  "cmake_minimum_required(VERSION 3.16)")

        #ensure we use a C++11 compiler
        tools.replace_in_file("CMakeLists.txt", "project(WindNinja)", ''' project(WindNinja) 
                                                                          set(CMAKE_CXX_STANDARD 14)
                                                                          set(CMAKE_CXX_STANDARD_REQUIRED ON)
                                                                          set(CMAKE_CXX_EXTENSIONS OFF)
                                                                          add_compile_options(-w -Wno-narrowing)''')

        #Absolutely ensure we find it
        if(self.options.openmp):
            tools.replace_in_file("CMakeLists.txt", "FIND_PACKAGE(OpenMP)", "find_package(OpenMP REQUIRED)")

        tools.replace_in_file("CMakeLists.txt", "include(FindBoost)", "find_package(Boost REQUIRED)")

        #changes to support the conan finds
        tools.replace_in_file("CMakeLists.txt", "include(FindNetCDF)", '''find_package(netcdf-c REQUIRED)''')

        tools.replace_in_file("CMakeLists.txt", "include(FindGDAL)", '''find_package(gdal REQUIRED)
                                                                        set(GDAL_LIBRARY "gdal::gdal")''')

        #patches to protect omp sections
        tools.replace_in_file("src/ninja/wxModelInitialization.h","#include <omp.h>", '''#ifdef _OPENMP 
                                                                                            #include <omp.h> 
                                                                                            #endif''')
        tools.replace_in_file("src/ninja/wxModelInitialization.h",'''#include "omp_guard.h"''', '''#ifdef _OPENMP 
                                                                                            #include "omp_guard.h" 
                                                                                            #endif''')

        tools.replace_in_file("src/ninja/wxModelInitialization.h",'''extern omp_lock_t netCDF_lock;''', '''#ifdef _OPENMP 
                                                                                            extern omp_lock_t netCDF_lock;
                                                                                            #endif''')
                                                                                            
        tools.replace_in_file("src/ninja/omp_guard.h","#include <omp.h>", '''#ifdef _OPENMP 
                                                                                            #include <omp.h> 
                                                                                            ''')
        tools.replace_in_file("src/ninja/omp_guard.h","#endif", '''#endif
                                                                    #endif''')
                                                                                           
       


        tools.replace_in_file("src/ninja/wxModelInitialization.cpp","bpt::time_duration td = bpt::hours( varvals[i] );","bpt::time_duration td = bpt::hours( (int) varvals[i] );")

        if(self.options.openmp):
            tools.replace_in_file("autotest/CMakeLists.txt",
                "set(LINK_LIBS",
                "set(LINK_LIBS OpenMP::OpenMP_CXX ")
            tools.replace_in_file("src/solar_grid/CMakeLists.txt",
                "set(LINK_LIBS",
                "set(LINK_LIBS OpenMP::OpenMP_CXX ")
            tools.replace_in_file("src/cli/CMakeLists.txt",
                "set(LINK_LIBS",
                "set(LINK_LIBS OpenMP::OpenMP_CXX ")
            tools.replace_in_file("src/stl_converter/CMakeLists.txt",
                "set(LINK_LIBS",
                "set(LINK_LIBS OpenMP::OpenMP_CXX ")
            tools.replace_in_file("src/fetch_station/CMakeLists.txt",
                "set(LINK_LIBS",
                "set(LINK_LIBS OpenMP::OpenMP_CXX ")
            tools.replace_in_file("src/ninja/CMakeLists.txt",
                "set(LINK_LIBS",
                "set(LINK_LIBS OpenMP::OpenMP_CXX ")
            tools.replace_in_file("src/fetch_dem/CMakeLists.txt",
                "set(LINK_LIBS",
                "set(LINK_LIBS OpenMP::OpenMP_CXX ")
            tools.replace_in_file("src/gui/CMakeLists.txt",
                "set(LINK_LIBS",
                "set(LINK_LIBS OpenMP::OpenMP_CXX ")
            tools.replace_in_file("src/output_converter/CMakeLists.txt",
                "set(LINK_LIBS",
                "set(LINK_LIBS OpenMP::OpenMP_CXX ")
        


    def requirements(self):
        self.requires( "boost/1.71.0@CHM/stable" )
        self.requires( "proj/4.9.3@CHM/stable" )
        self.requires( "gdal/2.4.1@CHM/stable" )
        self.requires( "netcdf-c/4.6.2@CHM/stable")

    def _configure_cmake(self):
        cmake = CMake(self)

      
        cmake.definitions["NINJA_QTGUI"] = False
        cmake.definitions["CMAKE_MODULE_PATH"] = self.build_folder # for the conan finds
        cmake.definitions["NINJAFOAM"] = False
        cmake.definitions["NINJA_SCM_REVISION"] = self.version
        cmake.definitions["OPENMP_SUPPORT"]=False

        if tools.os_info.is_macos:
            cmake.definitions["CMAKE_INSTALL_RPATH"] = "@executable_path/../lib"
        else:
            cmake.definitions["CMAKE_INSTALL_RPATH"] = "\$ORIGIN/../lib"

        cmake.verbose = True

        cmake.configure(source_folder=self.source_folder)

        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()


    def package(self):
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

    def deploy(self):
        self.copy("*")  # copy from current package
        self.copy_deps("*.so*") # copy from dependencies
        self.copy_deps("*.dylib*") # copy from dependencies

    def imports(self):
        self.copy("*.so*", "lib", "lib")  # From bin to bin
        self.copy("*.dylib*", "lib", "lib")  # From lib to bin
