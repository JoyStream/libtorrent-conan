from conans import ConanFile, CMake, tools
import os

class Libtorrent(ConanFile):
    name = "Libtorrent"
    version = "1.1.1"
    license = ""
    description = ""
    url = "https://github.com/JoyStream/libtorrent-conan.git"
    source_url = "git@github.com:JoyStream/libtorrent.git"
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    requires = "Boost/1.60.0@lasote/stable" , "OpenSSL/1.0.2j@lasote/stable"
    #exports_sources="*"

    options = {
        # option(shared "build libtorrent as a shared library" ON)
        "shared" : [True, False],
        # option(static_runtime "build libtorrent with static runtime" OFF)
        "static_runtime": [True, False],
        # option(tcmalloc "link against google performance tools tcmalloc" OFF)
        "tcmalloc": [True, False],
        # option(pool-allocators "Uses a pool allocator for disk and piece buffers" ON)
        "pool_allocators": [True, False],
        # option(encryption "link against openssl and enable encryption" ON)
        "encryption": [True, False],
        # option(dht "enable support for Mainline DHT" ON)
        "dht": [True, False],
        # option(resolve-countries "enable support for resolving countries from peer IPs" ON)
        "resolve_countries": [True, False],
        # option(unicode "enable unicode support" ON)
        "unicode": [True, False],
        # option(deprecated-functions "enable deprecated functions for backwards compatibility" ON)
        "deprecated_functions": [True, False],
        # option(exceptions "build with exception support" ON)
        "exceptions": [True, False],
        # option(logging "build with logging" OFF)
        "logging": [True, False],
        # option(build_tests "build tests" OFF)
        "build_tests": [True, False],
        # position independent code so static library can be later added to a shared library
        "fPIC": [True, False]
    }

    default_options = "shared=True", "static_runtime=False", "tcmalloc=False", "pool_allocators=True", "encryption=True", "dht=True", "resolve_countries=True", "unicode=True", "deprecated_functions=True", "exceptions=True", "logging=False", "build_tests=False", "fPIC=True"

    def config(self):
        #TODO: ensure static_runtime option matches settings.compiler.runtime, raise error if not
        # I think this only affects windows and linux
        #if self.settings.compiler.runtime == "static":
        #    if not self.options.static_runtime:
        #        raise Exception("static_runtime option needs to be set for libtorrent")

    def source(self):
        self.run("git clone %s" % self.source_url)
        # joystream fork of libtorrent - tracking RC_1_1 branch - release tag v1.1.1
        # removes 1 MB packet size limit
        # backporting a fix for session hanging and stack allocator
        self.run("cd libtorrent && git checkout 65c4622e8fb3775902852bd8de75a929ab2d3c33")

        tools.replace_in_file("libtorrent/CMakeLists.txt", "project(libtorrent)", '''project(libtorrent)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()''')

    def build(self):
        # Translate the conan package options to libtorrent cmake options
        shared_def = "-Dshared=on" if self.options.shared else ""
        static_runtime_def = "-Dstatic_runtime=on" if self.options.static_runtime else ""
        tcmalloc_def = "-Dtcmalloc=on" if self.options.tcmalloc else ""
        pool_allocators_def = "-Dpool-allocators=on" if self.options.pool_allocators else ""
        encryption_def = "-Dencryption=on" if self.options.encryption else ""
        dht_def = "-Ddht=on" if self.options.dht else ""
        resolve_countries_def = "-Dresolve-countries=on" if self.options.resolve_countries else ""
        unicode_def = "-Dunicode=on" if self.options.unicode else ""
        deprecated_functions_def = "-Ddeprecated-functions=on" if self.options.deprecated_functions else ""
        exceptions_def = "-Dexceptions=on" if self.options.exceptions else ""
        logging_def = "-Dlogging=on" if self.options.logging else ""
        build_tests_def = "-Dbuild_tests=on" if self.options.build_tests else ""
        fpic_def = "-DCMAKE_POSITION_INDEPENDENT_CODE=on" if self.options.fPIC else ""

        defs = '%s %s %s %s %s %s %s %s %s %s %s %s %s' % (shared_def, static_runtime_def,
           tcmalloc_def, pool_allocators_def, encryption_def, dht_def, resolve_countries_def, unicode_def,
           deprecated_functions_def, exceptions_def, logging_def, build_tests_def, fpic_def )

        cmake = CMake(self.settings)
        self.run('cmake libtorrent %s %s' % (cmake.command_line, defs))
        self.run("cmake --build . %s" % cmake.build_config)

    def package(self):
        self.copy("*.hpp", dst="include", src="libtorrent/include/")
        self.copy("*.h", dst="include", src="libtorrent/include/")
        self.copy("*.h", dst="include", src="libtorrent/ed25519/src")
        self.copy("*.a", dst="lib", keep_path=False)
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="lib", keep_path=False)
        self.copy("*.so.*", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["torrent-rasterbar"]
        
        # debug
        if self.settings.build_type == "Debug":
             self.cpp_info.defines.append("TORRENT_DEBUG")

        # build_tests
        if self.options.build_tests:
            self.cpp_info.defines.append("TORRENT_EXPORT_EXTRA")
        
        # encryption
        if self.options.encryption:
            self.cpp_info.defines.append("TORRENT_USE_OPENSSL")
        else:
            self.cpp_info.defines.append("TORRENT_DISABLE_ENCRYPTION")

        #logging
        if not self.options.logging:
            self.cpp_info.defines.append("TORRENT_DISABLE_LOGGING")

        #dht
        if not self.options.dht:
            self.cpp_info.defines.append("DTORRENT_DISABLE_DHT")

        #pool allocators
        if not self.options.pool_allocators:
            self.cpp_info.defines.append("TORRENT_DISABLE_POOL_ALLOCATOR")

        #resolve countries (GeoIP)
        if not self.options.resolve_countries:
            self.cpp_info.defines.append("TORRENT_DISABLE_RESOLVE_COUNTRIES")

        #unicode
        if self.options.unicode:
            self.cpp_info.defines.append("UNICODE")
            self.cpp_info.defines.append("_UNICODE")

        #deprecated functions
        if not self.options.deprecated_functions:
            self.cpp_info.defines.append("TORRENT_NO_DEPRECATE")
        
        # boost package does this. no need to add it again ?
        #if self.settings.compiler == "Visual Studio":
        #    self.cpp_info.defines.extend(["BOOST_ALL_NO_LIB"])

        if self.settings.os == "Windows" :
            if not self.options.shared:
                self.cpp_info.libs.extend(["wsock32", "ws2_32", "Iphlpapi"])
            #probably not necessary for consumers?
            #self.cpp_info.defines.append("_WIN32_WINNT=0x0600")
	        # prevent winsock1 to be included
            #self.cpp_info.defines.append("WIN32_LEAN_AND_MEAN")

        # Do we need to propagate compiler flag to enable/disable exceptions in consuming projects?
        # .. from libtorrent CMakeLists.txt
        # if (exceptions)
        #     if (MSVC)
        #         add_definitions(/EHsc)
        #     else (MSVC)
        #         add_definitions(-fexceptions)
        #     endif (MSVC)
        # else()
        #     if (MSVC)
        #         add_definitions(-D_HAS_EXCEPTIONS=0)
        #     else (MSVC)
        #         add_definitions(-fno-exceptions)
        #     endif (MSVC)
        # endif()

        if self.settings.compiler == "Visual Studio":
            # disable bogus deprecation warnings on msvc8
            self.cpp_info.defines.extend(["_SCL_SECURE_NO_DEPRECATE", "_CRT_SECURE_NO_DEPRECATE"])
            # these compiler settings just makes the compiler standard conforming
            self.cpp_info.cppflags.extend(["/Zc:wchar_t", "/Zc:forScope"])
        
        #libtorrent tries to be compatible with C98 so it produces warnings if you try to use c++11 features
        #we don't want to put this restriction on consumers so these defenitions will not be added
        #elseif self.settings.compiler == "apple-clang":       
            	#add_definitions(-Wno-c++11-extensions)
	            #add_definitions(-fcolor-diagnostics)

        self.cpp_info.defines.extend(["_FILE_OFFSET_BITS=64", "BOOST_EXCEPTION_DISABLE", "BOOST_ASIO_ENABLE_CANCELIO"])

        # add tcmalloc library if option enabled
        if self.options.tcmalloc and not self.options.shared:
            self.cpp_info.libs.extend["tcmalloc"]

        
        