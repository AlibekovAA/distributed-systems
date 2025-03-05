#!/usr/bin/env python3
import os
import subprocess
import logging
import shutil
from typing import NoReturn


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("test_runner")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                                  datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def clean_directory(path: str) -> NoReturn:
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)
        logging.info(f"Removed old {path} directory")


def run_tests() -> NoReturn:
    logger = setup_logger()
    script_dir: str = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    for directory in ['tests-report', 'allure-results']:
        clean_directory(directory)

    try:
        logger.info("Starting test environment...")

        subprocess.run(['docker', 'compose', '-f', 'docker-compose.test.yml', 'build'], check=True)
        subprocess.run(['docker', 'compose', '-f', 'docker-compose.test.yml', 'up', '--exit-code-from', 'tests'], check=True)

        container_id = subprocess.check_output(
            ['docker', 'ps', '-aq', '--filter', 'name=tests-tests']
        ).decode().strip()

        if not container_id:
            raise Exception("Tests container not found")

        exit_code = subprocess.run(['docker', 'wait', container_id], capture_output=True, text=True).stdout.strip()

        try:
            subprocess.run([
                'docker', 'exec', container_id, 'allure', 'generate',
                '/app/allure-results', '-o', '/app/allure-report', '--clean', '--single-file'
            ], check=True)

            clean_directory(os.path.join(script_dir, 'allure-report'))

            logger.info("Allure report generated successfully.")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate Allure report: {e}")

        subprocess.run(['docker', 'compose', '-f', 'docker-compose.test.yml', 'down'], check=True)

        if exit_code != '0':
            logger.error(f"Tests failed with exit code {exit_code}")
            exit(int(exit_code))
        else:
            logger.info("Tests completed successfully")

    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        subprocess.run(['docker', 'compose', '-f', 'docker-compose.test.yml', 'down'], check=False)
        exit(1)


if __name__ == "__main__":
    run_tests()
