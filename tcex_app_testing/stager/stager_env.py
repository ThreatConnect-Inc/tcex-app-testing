"""TcEx Framework Module"""
# standard library
import os


class StagerEnv:
    """Stages the Redis Data"""

    @staticmethod
    def stage_model_data() -> dict:
        """Stage env data."""
        staged_data = {}
        for var, value in os.environ.items():
            if var.lower() in staged_data:
                raise RuntimeError(f'Environment variable {var} is already staged.')
            staged_data[var.lower()] = value

        return staged_data
