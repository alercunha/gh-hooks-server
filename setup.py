from setuptools import setup

setup(
    name='auto-pull-webhooks',
    version='1.0.0',
    description='Auto pull webhook for GitHub',
    author='Alexandre Cunha',
    author_email='alexandre.cunha@gmail.com',
    license='MIT',
    install_requires=[
        'tornado>=4.3',
    ],
    entry_points={
        'console_scripts': [
            'auto-pull-webhooks = server:main',
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    url='https://github.com/alercunha/auto-pull-webhooks',
)