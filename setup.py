from setuptools import setup
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='RedDrum-Frontend',
      version='v1.0.0',
      description='python Redfish Service Frontend package used by RedDrum-Simulator, RedDrum-OpenBMC, and other RedDrum backends',
      long_description=long_description,
      author='RedDrum-Redfish-Project / Paul Vancil, Dell ESI',
      author_email='redDrumRedfishProject@gmail.com',
      license='BSD License',
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 3.4',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: Libraries :: Embedded Systems',
          'Topic :: Communications'
      ],
      keywords='Redfish RedDrum SPMF OpenBMC ',
      url='https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend',
      download_url='https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/archive/v1.0.0.tar.gz',
      packages=['reddrum_frontend'],
      install_requires=[
          'passlib==1.7.1',   # used by Frontend
          'Flask',            # used by Frontend
          'pytz'              # used by Frontend
      ],
      include_package_data = True,
      package_data={'reddrum_frontend':['Data/db/*.json','Data/static/*','Data/templates/*.json','Data/registries/*.json','*.conf']}
)
