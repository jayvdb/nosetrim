
from setuptools import setup, find_packages

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
    license = 'GNU LGPL',
    packages = find_packages(),
    keywords = 'test unittest nose nosetests',
    entry_points = {
        'nose.plugins': [
            'trim = nosetrim:NoseTrim'
            ]
        },
    )

