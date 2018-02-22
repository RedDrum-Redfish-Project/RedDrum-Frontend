from setuptools import setup

setup(name='RedDrum-Frontend',
      version='0.9.5',
      description='python Redfish Service Frontend backage used by RedDrum-Simulator, RedDrum-OpenBMC, and other backends',
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
      download_url='https://github.com/RedDrum-Redfish-Project/RedDrum-Frontend/archive/0.9.5.tar.gz',
      packages=['reddrum_frontend'],
      install_requires=[
          'passlib==1.7.1',   # used by Frontend
          'Flask',            # used by Frontend
          'pytz'              # used by Frontend
      ],
      include_package_data = True,
      package_data={'reddrum_frontend':['Data/db/*.json','Data/static/*','Data/templates/*.json','Data/registries/*.json','*.conf']}
)
