from setuptools import setup, find_packages

setup(
    name="func-to-web",
    version="0.1.0",
    author="Beltrán Offerrall",
    packages=find_packages(),
    package_data={'func_to_web': ['templates/*.html', 'templates/static/*']},
    install_requires=[
        'fastapi',
        'uvicorn',
        'pydantic',
        'jinja2',
        'python-multipart',
    ],
)