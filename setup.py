"""Setup file for UnleashClient"""
from setuptools import setup, find_packages


def readme():
    """Include README.rst content in PyPi build information"""
    with open('README.md') as file:
        return file.read()


setup(
    name='UnleashClient',
    version='3.0.0',
    author='StoryStream',
    author_email='developers@storystream.it',
    description='Python client for the Unleash feature toggle system!',
    long_description=readme(),
    long_description_content_type="text/markdown",
    url='https://github.com/storystream/unleash-client-python',
    packages=find_packages(),
    install_requires=["requests==2.6.0",
                      "fcache==0.4.7",
                      "mmh3==2.5.1",
                      "apscheduler==3.6.1",
                      "python-dateutil==2.4.2",
                      "chainmap==1.0.3"],
    tests_require=['pytest', "mimesis", "responses"],
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
    ]
)
