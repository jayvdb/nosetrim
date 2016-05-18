
from setuptools import setup, find_packages

extras_require = {
    ':python_version=="2.6"': ['unittest2'],
}

setup(
    name='nosetrim',
    version='0.1',
    download_url="http://nosetrim.googlecode.com/svn/trunk/#egg=nosetrim-dev",
    zip_safe=False,
    author="Kumar McMillan",
    author_email = "kumar dot mcmillan / gmail.com",
    description = ( 
        "A nose plugin that reports only unique exceptions"),
    install_requires='nose',
    extras_require=extras_require,
    license = 'GNU LGPL',
    packages = find_packages(),
    keywords = 'test unittest nose nosetests',
    entry_points = {
        'nose.plugins': [
            'trim = nosetrim:NoseTrim'
            ]
        },
    tests_require=['tempdir'],
    classifiers=[
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Testing',
    ],
)
