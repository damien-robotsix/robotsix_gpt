from setuptools import setup, find_packages

setup(
    name="ai_assistant",
    version="0.1",
    packages=find_packages(include=["ai_assistant*"]),
    package_data={
        'ai_assistant': ['assistant_config.json', 'utils/*.py']
    },
    entry_points={
        'console_scripts': [
            'ai_assistant=ai_assistant.run_assistant:main',
            'ai_commit=ai_assistant.generate_commit:main',
            'ai_squash=ai_assistant.squash_branch:main',
            'ai_init_repo=ai_assistant.create_repo_assistant:main',
            'ai_delete_repo=ai_assistant.delete_repo_assistant:main',
            'ai_update_files=ai_assistant.update_files:main',
            'ai_update_assistant=ai_assistant.update_assistant:main',
        ],
    },
    install_requires=[
        'requests',
        # Add other dependencies here
    ],
)