#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, AutoToolsBuildEnvironment
import os


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
        raise Exception('TODO')

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
        with tools.chdir("sources"):
            self.copy(pattern="COPYING")

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
