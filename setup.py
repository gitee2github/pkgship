from distutils.core import setup
import os

BASE_PATH = os.path.dirname(__file__)

path = os.path.join(BASE_PATH, 'Lib', 'site-packages', 'package')

configpath = "/etc/pkgship/"

setup(
    name='packageship',
    version='1.0',
    py_modules=[
        'packageship.application.__init__',
        'packageship.application.app_global',
        'packageship.application.apps.__init__',
        'packageship.application.apps.package.serialize',
        'packageship.application.apps.package.url',
        'packageship.application.apps.package.view',
        'packageship.application.apps.package.function.BeDepend',
        'packageship.application.apps.package.function.BuildDepend',
        'packageship.application.apps.package.function.Constants',
        'packageship.application.apps.package.function.InstallDepend',
        'packageship.application.apps.package.function.Packages',
        'packageship.application.apps.package.function.SearchDB',
        'packageship.application.apps.package.function.SelfDepend',
        'packageship.application.initsystem.data_import',
        'packageship.application.initsystem.datamerge',
        'packageship.application.models.package',
        'packageship.application.models.temporarydb',
        'packageship.application.settings',
        'packageship.libs.__init__',
        'packageship.libs.configutils.readconfig',
        'packageship.libs.dbutils.sqlalchemy_helper',
        'packageship.libs.exception.ext',
        'packageship.libs.log.loghelper',
        'packageship.tests.test_build_depend',
        'packageship.tests.test_delete_repodatas',
        'packageship.tests.test_get_repodatas',
        'packageship.tests.test_get_singlepack',
        'packageship.tests.test_install_depend',
        'packageship.tests.test_packages',
        'packageship.tests.test_self_depend',
        'packageship.tests.test_update_singlepack',
        'packageship.tests.test_importdata',
        'packageship.manage',
        'packageship.cli',
        'packageship.selfpkg',
        'packageship.system_config'],
    requires=['prettytable (==0.7.2)',
              'Flask_RESTful (==0.3.8)',
              'Flask_Session (==0.3.1)',
              'Flask_Script (==2.0.6)',
              'Flask (==1.1.2)',
              'marshmallow (==3.5.1)',
              'SQLAlchemy (==1.3.16)',
              'PyYAML (==5.3.1)',
              'requests (==2.21.0)',
              'pyinstall (==0.1.4)',
              'uwsgi (==2.0.18)'],
    license='Dependency package management',
    long_description=open('README.md', encoding='utf-8').read(),
    author='gongzt',
    data_files=[
        (configpath, ['packageship/package.ini',
                      'packageship/uWSGI_service.sh',
                      'packageship/packageship.sh'])]
)
