#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, AutoToolsBuildEnvironment
import os
from xml.dom import minidom


class LibnameConan(ConanFile):
    name = "lcms"
    version = "2.9"
    url = "https://github.com/bincrafters/conan-lcms"
    description = "Keep it short"
    license = "https://github.com/someauthor/somelib/blob/master/LICENSES"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False]}
    default_options = "shared=False"

    def source(self):
        extracted_dir = 'lcms2-%s' % self.version
        archive_name = "%s.tar.gz" % extracted_dir
        source_url = "https://downloads.sourceforge.net/project/lcms/lcms/%s/%s" % (self.version, archive_name)
        tools.get(source_url)
        os.rename(extracted_dir, "sources")

    def build_visual_studio(self):
        with tools.chdir(os.path.join('sources', 'Projects', 'VC2012')):
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

            cmd = tools.msvc_build_command(self.settings, 'lcms2.sln',
                                           targets=[target],
                                           arch='Win32' if self.settings.arch == 'x86' else 'x64')
            self.output.warn(cmd)
            self.run(cmd)

    def build_configure(self):
        env_build = AutoToolsBuildEnvironment(self)
        with tools.chdir('sources'):
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
        self.copy(pattern="COPYING", src='sources')
        if self.settings.compiler == 'Visual Studio':
            self.copy(pattern='*.h', src=os.path.join('sources', 'include'), dst='include', keep_path=True)
            if self.options.shared:
                self.copy(pattern='*.lib', src=os.path.join('sources', 'bin'), dst='lib', keep_path=False)
                self.copy(pattern='*.dll', src=os.path.join('sources', 'bin'), dst='bin', keep_path=False)
            else:
                self.copy(pattern='*.lib', src=os.path.join('sources', 'Lib', 'MS'), dst='lib', keep_path=False)

    def package_info(self):
        if self.settings.compiler == 'Visual Studio':
            self.cpp_info.libs = ['lcms2' if self.options.shared else 'lcms2_static']
            if self.options.shared:
                self.cpp_info.defines.append('CMS_DLL')
        else:
            self.cpp_info.libs = ['lcms2']
