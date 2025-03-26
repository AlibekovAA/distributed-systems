#!/usr/bin/env python3
import logging
import os
import shutil
import subprocess
import time
from typing import NoReturn


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("test_runner")
    logger.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                                  datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def clean_directory(path: str) -> NoReturn:
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path, exist_ok=True)


def print_container_logs(logger: logging.Logger, service_name: str) -> None:
    try:
        logger.info(f"\n========= Logs for {service_name} =========")
        subprocess.run(
            ['docker', 'compose', '-f', 'docker-compose.test.yml', 'logs', service_name],
            check=True
        )
        logger.info(f"========= End of logs for {service_name} =========")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get logs for {service_name}: {e}")


def run_test_suite(logger: logging.Logger, service_name: str) -> bool:
    try:
        logger.info(f"Running tests for {service_name}...")
        subprocess.run([
            'docker', 'compose', '-f', 'docker-compose.test.yml', 'run',
            '--rm', f'{service_name}-tests'
        ], check=False)
        return True
    except Exception as e:
        logger.error(f"{service_name} tests failed with error: {e}")
        return False


def run_tests() -> NoReturn:
    logger = setup_logger()
    script_dir: str = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    for directory in ['allure-report', 'allure-results']:
        clean_directory(directory)

    test_failures = []

    try:
        subprocess.run(['docker', 'build', '-t', 'base-test:latest', '-f', 'base-test.Dockerfile', '.'], check=True)

        subprocess.run(['docker', 'compose', '-f', 'docker-compose.test.yml', 'build'], check=True)

        subprocess.run([
            'docker', 'compose', '-f', 'docker-compose.test.yml', 'up',
            '-d', 'postgres-test', 'rabbitmq-test'
        ], check=True)

        time.sleep(15)

        subprocess.run([
            'docker', 'compose', '-f', 'docker-compose.test.yml', 'up',
            '-d', 'auth-service', 'product-catalog-service'
        ], check=True)

        if not run_test_suite(logger, "auth"):
            test_failures.append("auth-service")

        if not run_test_suite(logger, "catalog"):
            test_failures.append("product-catalog-service")

        if test_failures:
            logger.error(f"Tests failed for services: {', '.join(test_failures)}")
        else:
            logger.info("All tests completed successfully")

        try:
            subprocess.run([
                'docker', 'run', '--rm',
                '-v', f'{script_dir}/allure-results:/allure-results',
                '-v', f'{script_dir}/allure-report:/allure-report',
                'base-test:latest',
                'allure', 'generate',
                '/allure-results',
                '-o', '/allure-report',
                '--clean',
                '--single-file'
            ], check=True)
            logger.info("Allure reports generated successfully.")
            logger.info(f"Report is available at: {os.path.join(script_dir, 'allure-report')}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate Allure report: {e}")

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        raise
    finally:
        logger.info("Printing final service logs before shutdown...")
        services = [
            "postgres-test",
            "rabbitmq-test",
            "auth-service",
            "product-catalog-service",
            "auth-tests",
            "catalog-tests"
        ]

        for service in services:
            print_container_logs(logger, service)

        logger.info("Shutting down test environment...")
        subprocess.run(['docker', 'compose', '-f', 'docker-compose.test.yml', 'down'], check=False)


if __name__ == "__main__":
    run_tests()
