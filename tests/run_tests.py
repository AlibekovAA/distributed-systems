#!/usr/bin/env python3
import os
import platform
import subprocess
import logging
from typing import NoReturn


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("test_runner")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def run_tests() -> NoReturn:
    logger = setup_logger()
    os_type: str = platform.system().lower()

    script_dir: str = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    for directory in ['test-results', 'allure-results']:
        if os.path.exists(directory):
            command = ['rm', '-rf', directory] if os_type != 'windows' else ['rmdir', '/s', '/q', directory]
            try:
                subprocess.run(command, shell=True, check=True)
                logger.info(f"Removed old {directory} directory")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to remove {directory}: {e}")

    try:
        logger.info("Starting test environment...")

        subprocess.run(['docker', 'compose', '-f', 'docker-compose.test.yml', 'build'], check=True)
        subprocess.run(['docker', 'compose', '-f', 'docker-compose.test.yml', 'up', '--exit-code-from', 'tests'], check=True)

        containers = subprocess.check_output(['docker', 'ps', '-aq', '--filter', 'name=tests-tests']).decode().strip()
        if not containers:
            raise Exception("Tests container not found")

        container_id = containers.split('\n')[0]
        exit_code = subprocess.check_output(['docker', 'inspect', container_id, '-f', '{{.State.ExitCode}}']).decode().strip()

        try:
            subprocess.run(['docker', 'run', '-d',
                          '-p', '5051:5051',
                          '-e', 'CHECK_RESULTS_EVERY_SECONDS=3',
                          '-e', 'KEEP_HISTORY=1',
                          '-v', f'{script_dir}/allure-results:/app/allure-results',
                          'frankescobar/allure-docker-service'], check=True)
            logger.info(
                "Allure report is available at: http://localhost:5051/allure-docker-service/projects/default"
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Allure server: {e}")

        if exit_code != '0':
            logger.error(f"Tests failed with exit code {exit_code}")
            exit(int(exit_code))
        else:
            logger.info("Tests completed successfully")

    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        exit(1)


if __name__ == "__main__":
    run_tests()
