from distutils.core import setup

setup(
    name="otp22logbot",
    version="0.0.0",
    author="L0j1k",
    author_email="L0j1k@L0j1k.com",
    url="https://github.com/L0j1k/otp22logbot",
    description="Simple logging bot",
    license="BSD3",
    packages=['otp22logbot'],
    scripts=['scripts/otp22logbot'],
    classifiers=[
        "This line prevents release on PyPI",
        "Programming Language :: Python :: 3.4",
    ]
)
