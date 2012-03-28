from distutils.core import setup

setup(
    name='pydotmailer',
    version=__import__('pydotmailer').__version__,
    description='A reusable python module for driving the dotMailer API',
    author='Mike Austin',
    author_email='mike.austin2012@triggeredmessaging.com',
    url='http://github.com/TriggeredMessaging/pydotmailer/',
    packages=[
        'pydotmailer',
    ],
    package_dir={'pydotmailer': 'pydotmailer'},
)
