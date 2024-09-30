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
            'ai_init_repo=ai_assistant.create_repo_assistant:main',  # Added CLI command
        ],
    },
    install_requires=[
        'requests',
        # Add other dependencies here
    ],
)