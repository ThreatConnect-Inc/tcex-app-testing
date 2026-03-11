# Release Notes

### 1.0.2

-   APP-5128 - [Message-Broker] Updated message broker connection to not set tls_version
-   APP-5129 - [Message-Broker] Updated Paho MQTT library and message broker reconnect logic
-   APP-5130 - [Misc] Fixed invalid references and copy-paste issues
-   APP-5131 - [Project] Updated pyproject to use bump-my-version

### 1.0.1

-   APP-4723 - Added fake Redis server (only starts if Redis is not running)
-   APP-4724 - Added dotenv support
-   APP-4725 - Updated dependencies for inflect and typer
-   APP-4726 - Updated default values for a few app inputs
-   APP-4727 - Renamed aux.py file to aux_.py to handle restriction on windows
-   APP-4735 - Migrated to "uv" for package management
-   APP-4736 - Switched linters to "ruff" (including linting fixes)

### 1.0.0

-   Initial public release of TcEx App testing framework.
