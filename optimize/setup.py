from setuptools import setup, Extension
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(["liked_profiles.pyx", "train.pyx", "auth.pyx", "authgateway.pyx", "main.pyx"]),
)
