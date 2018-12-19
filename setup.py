import setuptools

with open("README.md", "r") as fh:
        long_description = fh.read()

setuptools.setup(
    name="scrabble_solver",
    version="0.0.1",
    author="Dylan Lynch",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dqlynch/scrabblesolver",
    packages=setuptools.find_packages(),
    install_requires=[
      'numpy',
      'DAWG',
      'DAWG-Python',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'wwfsolve = scrabble_solver.solver:solve_board_cli',
			'wwftest = scrabble_solver.solver:main'
        ]
    }
)
