#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil

from conans import ConanFile, tools, AutoToolsBuildEnvironment, MSBuild


class LcmsConan(ConanFile):
    name = "lcms"
    version = "2.9"
    url = "https://github.com/bincrafters/conan-lcms"
    description = "A free, open source, CMM engine."
    license = "MIT"
    homepage = "https://github.com/mm2/Little-CMS"
    author = "Bicrafters <bincrafters@gmail.com>"
    topics = ("conan", "lcms", "cmm", "icc", "cmm-engine")
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {'shared': False, 'fPIC': True}
    exports = ["LICENSE.md"]
    exports_sources = ["FindLCMS2.cmake"]
    generators = "cmake"
    _source_subfolder = "source_subfolder"

    def build_requirements(self):
        if tools.os_info.is_windows and "CONAN_BASH_PATH" not in os.environ:
            self.build_requires("msys2_installer/latest@bincrafters/stable")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        sha256 = "8e23a09dc81af856db37941a4ea26acdf6a45b0281ec5b7ee94b5a4e9f7afbf7"
        tools.get("{}/archive/lcms{}.tar.gz".format(self.homepage, self.version), sha256=sha256)
        os.rename('Little-CMS-lcms%s' % self.version, self._source_subfolder)

    def _build_visual_studio(self):
        # since VS2015 vsnprintf is built-in
        if int(str(self.settings.compiler.version)) >= 14:
            path = os.path.join(self._source_subfolder, 'src', 'lcms2_internal.h')
            tools.replace_in_file(path, '#       define vsnprintf  _vsnprintf', '')

        with tools.chdir(os.path.join(self._source_subfolder, 'Projects', 'VC2013')):
            target = 'lcms2_DLL' if self.options.shared else 'lcms2_static'
            upgrade_project = True if int(str(self.settings.compiler.version)) > 12 else False
            # run build
            msbuild = MSBuild(self)
            msbuild.build("lcms2.sln", targets=[target], platforms={"x86": "Win32"}, upgrade_project=upgrade_project)

    def _build_configure(self):
        if self.settings.os == "Android" and tools.os_info.is_windows:
            tools.replace_in_file(os.path.join(self._source_subfolder, 'configure'),
                "s/[	 `~#$^&*(){}\\\\|;'\\\''\"<>?]/\\\\&/g", "s/[	 `~#$^&*(){}\\\\|;<>?]/\\\\&/g")
        env_build = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        with tools.chdir(self._source_subfolder):
            args = ['prefix=%s' % self.package_folder]
            if self.options.shared:
                args.extend(['--disable-static', '--enable-shared'])
            else:
                args.extend(['--disable-shared', '--enable-static'])
            env_build.configure(args=args)
            env_build.make()
            env_build.make(args=['install'])

    def build(self):
        if self.settings.compiler == 'Visual Studio':
            self._build_visual_studio()
        else:
            self._build_configure()

    def package(self):
        self.copy("FindLCMS2.cmake")
        self.copy(pattern="COPYING", dst="licenses", src=self._source_subfolder)
        if self.settings.compiler == 'Visual Studio':
            self.copy(pattern='*.h', src=os.path.join(self._source_subfolder, 'include'), dst='include', keep_path=True)
            if self.options.shared:
                self.copy(pattern='*.lib', src=os.path.join(self._source_subfolder, 'bin'), dst='lib', keep_path=False)
                self.copy(pattern='*.dll', src=os.path.join(self._source_subfolder, 'bin'), dst='bin', keep_path=False)
            else:
                self.copy(pattern='*.lib', src=os.path.join(self._source_subfolder, 'Lib', 'MS'), dst='lib',
                          keep_path=False)
        # remove man pages
        shutil.rmtree(os.path.join(self.package_folder, 'share', 'man'), ignore_errors=True)
        # remove binaries
        for bin_program in ['tificc', 'linkicc', 'transicc', 'psicc', 'jpgicc']:
            for ext in ['', '.exe']:
                try:
                    os.remove(os.path.join(self.package_folder, 'bin', bin_program + ext))
                except:
                    pass

    def package_info(self):
        if self.settings.compiler == 'Visual Studio':
            self.cpp_info.libs = ['lcms2' if self.options.shared else 'lcms2_static']
            if self.options.shared:
                self.cpp_info.defines.append('CMS_DLL')
        else:
            self.cpp_info.libs = ['lcms2']
