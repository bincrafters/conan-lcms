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
    homepage = "http://www.littlecms.com"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    exports = ["LICENSE.md"]
    exports_sources = ["FindLCMS2.cmake"]
    generators = "cmake"
    source_subfolder = "source_subfolder"

    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        tools.get("https://github.com/mm2/Little-CMS/archive/lcms%s.tar.gz" % self.version)
        os.rename('Little-CMS-lcms%s' % self.version, self.source_subfolder)

    def build_visual_studio(self):
        # since VS2015 vsnprintf is built-in
        if int(str(self.settings.compiler.version)) >= 14:
            path = os.path.join(self.source_subfolder, 'src', 'lcms2_internal.h')
            tools.replace_in_file(path, '#       define vsnprintf  _vsnprintf', '')

        with tools.chdir(os.path.join(self.source_subfolder, 'Projects', 'VC2013')):
            target = 'lcms2_DLL' if self.options.shared else 'lcms2_static'
            upgrade_project = True if int(str(self.settings.compiler.version)) > 12 else False
            # run build
            msbuild = MSBuild(self)
            msbuild.build("lcms2.sln", targets=[target], platforms={"x86": "Win32"}, upgrade_project=upgrade_project)

    def build_configure(self):
        env_build = AutoToolsBuildEnvironment(self)
        with tools.chdir(self.source_subfolder):
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
            self.build_visual_studio()
        else:
            self.build_configure()

    def package(self):
        self.copy("FindLCMS2.cmake")
        self.copy(pattern="COPYING", dst="licenses", src=self.source_subfolder)
        if self.settings.compiler == 'Visual Studio':
            self.copy(pattern='*.h', src=os.path.join(self.source_subfolder, 'include'), dst='include', keep_path=True)
            if self.options.shared:
                self.copy(pattern='*.lib', src=os.path.join(self.source_subfolder, 'bin'), dst='lib', keep_path=False)
                self.copy(pattern='*.dll', src=os.path.join(self.source_subfolder, 'bin'), dst='bin', keep_path=False)
            else:
                self.copy(pattern='*.lib', src=os.path.join(self.source_subfolder, 'Lib', 'MS'), dst='lib', keep_path=False)
        # remove man pages
        shutil.rmtree(os.path.join(self.package_folder, 'share', 'man'), ignore_errors=True)
        # remove binaries
        for bin_program in ['tificc', 'linkicc', 'transicc', 'psicc', 'jpgicc']:
            for ext in ['', '.exe']:
                try:
                    os.remove(os.path.join(self.package_folder, 'bin', bin_program+ext))
                except:
                    pass

    def package_info(self):
        if self.settings.compiler == 'Visual Studio':
            self.cpp_info.libs = ['lcms2' if self.options.shared else 'lcms2_static']
            if self.options.shared:
                self.cpp_info.defines.append('CMS_DLL')
        else:
            self.cpp_info.libs = ['lcms2']
