import setuptools

setuptools.setup(
    name="cdk-staticsite",
    version="0.0.1",

    author="Manu Chandrasekhar",

    package_dir={"": "lib"},
    packages=setuptools.find_packages(where="lib"),

)
