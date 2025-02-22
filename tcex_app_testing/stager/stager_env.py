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
                ex_msg = f'Environment variable {var} is already staged.'
                raise RuntimeError(ex_msg)
            staged_data[var.lower()] = value

        return staged_data
