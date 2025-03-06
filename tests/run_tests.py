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


def merge_allure_results() -> NoReturn:
    auth_results = "allure-results/auth"
    product_results = "allure-results/product-catalog"
    merged_results = "allure-results/merged"

    os.makedirs(merged_results, exist_ok=True)

    for directory in [auth_results, product_results]:
        if os.path.exists(directory):
            for result_file in os.listdir(directory):
                shutil.copy2(
                    os.path.join(directory, result_file),
                    os.path.join(merged_results, result_file)
                )


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

        merge_allure_results()

        try:
            subprocess.run([
                'allure', 'generate',
                'allure-results/merged', '-o', 'tests-report', '--clean'
            ], check=True)

            logger.info("Allure report generated successfully.")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate Allure report: {e}")

        subprocess.run(['docker', 'compose', '-f', 'docker-compose.test.yml', 'down'], check=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        subprocess.run(['docker', 'compose', '-f', 'docker-compose.test.yml', 'down'], check=False)
        exit(1)


if __name__ == "__main__":
    run_tests()
