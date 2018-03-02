#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from xml.dom import minidom
from conans import ConanFile, tools, AutoToolsBuildEnvironment, VisualStudioBuildEnvironment


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

    def source(self):
        tools.get("https://github.com/mm2/Little-CMS/archive/lcms%s.tar.gz" % self.version)
        os.rename('Little-CMS-lcms%s' % self.version, self.source_subfolder)

    def build_visual_studio(self):
        env_build = VisualStudioBuildEnvironment(self)
        with tools.environment_append(env_build.vars):
            with tools.chdir(os.path.join(self.source_subfolder, 'Projects', 'VC2013')):
                target = 'lcms2_DLL' if self.options.shared else 'lcms2_static'
                vcxproj = os.path.join(target, '%s.vcxproj' % target)
                dom = minidom.parse(vcxproj)
                elements = dom.getElementsByTagName("RuntimeLibrary")
                runtime_library = {'MT': 'MultiThreaded',
                                   'MTd': 'MultiThreadedDebug',
                                   'MD': 'MultiThreadedDLL',
                                   'MDd': 'MultiThreadedDebugDLL'}.get(str(self.settings.compiler.runtime))
                for element in elements:
                    for child in element.childNodes:
                        if child.nodeType == element.TEXT_NODE:
                            child.replaceWholeText(runtime_library)
                with open(vcxproj, 'w') as f:
                    f.write(dom.toprettyxml())

                vcvars_command = tools.vcvars_command(self.settings)
                # sometimes upgrading from 2010 to 2012 project fails with non-error exit code
                try:
                    self.run('%s && devenv lcms2.sln /upgrade' % vcvars_command)
                except:
                    pass
                # run build
                cmd = tools.build_sln_command(self.settings, 'lcms2.sln', upgrade_project=False, targets=[target])
                if self.settings.arch == 'x86':
                    cmd = cmd.replace('/p:Platform="x86"', '/p:Platform="Win32"')
                cmd = '%s && %s' % (vcvars_command, cmd)
                self.output.warn(cmd)
                self.run(cmd)

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
