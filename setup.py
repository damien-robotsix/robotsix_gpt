from setuptools import setup, find_packages

setup(
    name="ai_assistant",
    version="0.1",
    packages=find_packages(include=["ai_assistant*"]),
    entry_points={
        'console_scripts': [
            'ai_assistant=ai_assistant.run_assistant:main',
            'ai_commit=ai_assistant.generate_commit:main',
            'ai_squash=ai_assistant.squash_branch:main',
        ],
    },
    install_requires=[
        'requests',
        # Add other dependencies here
    ],
)