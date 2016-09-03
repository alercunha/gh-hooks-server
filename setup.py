from setuptools import setup

setup(
    name='gh-hooks-server',
    version='1.1.0',
    description='GitHub Webhook Server',
    author='Alexandre Cunha',
    author_email='alexandre.cunha@gmail.com',
    license='MIT',
    packages=[
        'ghhooks',
    ],
    install_requires=[
        'tornado>=4.3',
    ],
    entry_points={
        'console_scripts': [
            'ghhooks = ghhooks.server:main',
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    url='https://github.com/alercunha/gh-hooks-server',
)