from setuptools import setup

setup (name="ldapy",
        version="0.1",
        description="Commandline LDAP browser",
        long_description="A simple commandline LDAP browser written in Python.",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
            "Programming Language :: Python :: 2.7",
            "Topic :: Database :: Front-Ends"],
        keywords="ldap browser commandline",
        url="http://github.com/rootmos/ldapy",
        license="GPL",
        packages=["ldapy"],
        scripts=["scripts/ldapy"],
        include_package_data=True,
        zip_safe=True)
