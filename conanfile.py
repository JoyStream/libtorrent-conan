from conans import ConanFile, CMake, tools
import os

class Libtorrent(ConanFile):
    name = "Libtorrent"
    version = "1.1.1"
    license = "Copyright (c) 2003-2016, Arvid Norberg"
    description = '''
libtorrent is an open source C++ library implementing the BitTorrent protocol, along with most popular extensions, making it suitable for real world deployment. It is configurable to be able to fit both servers and embedded devices.
    '''
    url = "https://github.com/JoyStream/libtorrent-conan.git"
    source_url = "git@github.com:JoyStream/libtorrent.git"
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    requires = "Boost/1.60.0@lasote/stable" , "OpenSSL/1.0.2j@lasote/stable"

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

    def configure(self):
        #TODO: How to handle libtorrent static_runtime options? and how does it relate to self.settings.compiler.runtime

        if self.settings.compiler == "Visual Studio":
          self.options.remove("fPIC")

        return

    def source(self):
        self.run("git clone %s" % self.source_url)
        # joystream fork of libtorrent - tracking RC_1_1 branch - release tag v1.1.1
        # removes 1 MB packet size limit
        # backporting a fix for session hanging and stack allocator
        # building from debug build fix commit
        self.run("cd libtorrent && git checkout 67ab9615f8bd9d9ae222d0f1c0cb238e52535eba")

        tools.replace_in_file("libtorrent/CMakeLists.txt", "project(libtorrent)", '''project(libtorrent)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()''')

    def build(self):
        # Translate the conan package options to libtorrent cmake options
        shared_def = "-Dshared=on" if self.options.shared else "-Dshared=off"
        static_runtime_def = "-Dstatic_runtime=on" if self.options.static_runtime else "-Dstatic_runtime=off"
        tcmalloc_def = "-Dtcmalloc=on" if self.options.tcmalloc else "-Dtcmalloc=off"
        pool_allocators_def = "-Dpool-allocators=on" if self.options.pool_allocators else "-Dpool-allocators=off"
        encryption_def = "-Dencryption=on" if self.options.encryption else "-Dencryption=off"
        dht_def = "-Ddht=on" if self.options.dht else "-Ddht=off"
        resolve_countries_def = "-Dresolve-countries=on" if self.options.resolve_countries else "-Dresolve-countries=off"
        unicode_def = "-Dunicode=on" if self.options.unicode else "-Dunicode=off"
        deprecated_functions_def = "-Ddeprecated-functions=on" if self.options.deprecated_functions else "-Ddeprecated-functions=off"
        exceptions_def = "-Dexceptions=on" if self.options.exceptions else "-Dexceptions=off"
        logging_def = "-Dlogging=on" if self.options.logging else "-Dlogging=off"
        build_tests_def = "-Dbuild_tests=%" if self.options.build_tests else "-Dbuild_tests=off"

        fpic_def = ""
        if self.settings.compiler != "Visual Studio":
            fpic_def = "-DCMAKE_POSITION_INDEPENDENT_CODE=on" if self.options.fPIC else ""

        defs = '%s %s %s %s %s %s %s %s %s %s %s %s %s' % (shared_def, static_runtime_def,
           tcmalloc_def, pool_allocators_def, encryption_def, dht_def, resolve_countries_def, unicode_def,
           deprecated_functions_def, exceptions_def, logging_def, build_tests_def, fpic_def )

        #boost::asio::ip::address_v4::bytes_type and boost::asio::ip::address_v6::bytes_type will differ based on what
        #standard we compile with. So it is important to propagate how we built libtorrent with appropriate cflags when packaging
        #https://github.com/boostorg/asio/blob/d6d2c452f5e874e1cb3dc0bc71eb9b6c57dc2f48/include/boost/asio/ip/address_v4.hpp#L49
        cpp_standard = "-DCMAKE_CXX_STANDARD=11"

        cmake = CMake(self.settings)
        self.run("cmake %s %s %s libtorrent" % (cmake.command_line, defs, cpp_standard))
        self.run("cmake --build . %s" % cmake.build_config)

    def package(self):
        self.copy("*", dst="include", src="libtorrent/include/")
        self.copy("*.h", dst="include/ed25519", src="libtorrent/ed25519/src", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="lib", keep_path=False)
        self.copy("*.so*", dst="lib", keep_path=False, links=True)
        self.copy("*.dylib", dst="lib", keep_path=False, links=True)

    def package_info(self):
        self.cpp_info.libs = ["torrent-rasterbar"]

        #if on linux and using static lib - we need to link to pthread
        if str(self.settings.os) == "Linux" and not self.options.shared:
            self.cpp_info.libs.extend(["pthread"])
            #older linux glibc might also need realitime library  librt ?

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
            self.cpp_info.defines.append("TORRENT_DISABLE_DHT")

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
            self.cpp_info.libs.extend(["wsock32", "ws2_32", "Iphlpapi"])
            #probably not necessary for consumers?
            #self.cpp_info.defines.append("_WIN32_WINNT=0x0600")
	          #prevent winsock1 to be included
            #self.cpp_info.defines.append("WIN32_LEAN_AND_MEAN")

        if self.settings.compiler == "Visual Studio":
            # disable bogus deprecation warnings on msvc8
            self.cpp_info.defines.extend(["_SCL_SECURE_NO_DEPRECATE", "_CRT_SECURE_NO_DEPRECATE"])
            # these compiler settings just makes the compiler standard conforming
            self.cpp_info.cppflags.extend(["/Zc:wchar_t", "/Zc:forScope"])

        self.cpp_info.defines.extend(["_FILE_OFFSET_BITS=64", "BOOST_EXCEPTION_DISABLE", "BOOST_ASIO_ENABLE_CANCELIO"])

        # add tcmalloc library if option enabled
        if self.options.tcmalloc and not self.options.shared:
            self.cpp_info.libs.extend["tcmalloc"]

        #https://github.com/conan-io/conan/issues/217
        #http://blog.conan.io/2016/03/22/From-CMake-syntax-to-libstdc++-ABI-incompatibiliy-migrations-are-always-hard.html
        #https://gcc.gnu.org/onlinedocs/libstdc%2B%2B/manual/using_dual_abi.html
        # Libtorrent and boost are built with c++11 so we need to have consumers build with c++11 standard as well
        if str(self.settings.compiler) != "Visual Studio":
            self.cpp_info.cppflags.append("-std=c++11")
