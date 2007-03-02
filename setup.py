
from setuptools import setup

setup(
    name='nosetrim',
    version='0.1',
    zip_safe=False,
    author="Kumar McMillan",
    author_email = "kumar dot mcmillan / gmail.com",
    description = ( 
        "nose plugin that reports only unique exceptions"),
    install_requires='nose',
    license = 'GNU LGPL',
    py_modules = ['nosetrim'],
    keywords = 'test unittest nose nosetests',
    entry_points = {
        'nose.plugins': [
            'trim = nosetrim:NoseTrim'
            ]
        },
    )

