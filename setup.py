from setuptools import setup, find_packages

setup(
    name="ai_assistant",
    version="0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ai_assistant=tools.user_utility.run_assistant:main',
            'ai_commit=scripts.generate_commit:main',
            'ai_squash=scripts.squash_branch:main',
        ],
    },
    install_requires=[
        'requests',
        # Add other dependencies here
    ],
)