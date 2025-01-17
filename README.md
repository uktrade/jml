# Leaving DBT Service

## Project documentation

Our project documentation is in the `docs` folder. It is written in Markdown and is compiled into HTML using MkDocs.

https://uktrade.github.io/jml

### How to run MkDocs locally

MkDocs can be run locally using the `make serve-docs` command which runs the `docs`
docker container. Alternatively, you can run the `docs` docker container by enabling the
`docs` compose profile.

The documentation will be served at `http://0.0.0.0:8002`.

Note: you may need the following available if you wish to run this on your local machine:
https://squidfunk.github.io/mkdocs-material/plugins/requirements/image-processing/
For macOS, you can install the required dependencies using Homebrew:
```
brew install cairo freetype libffi libjpeg libpng zlib
```
# Setup DebugPy

Add environment variable in your .env file

    DEBUGPY_ENABLED=True

Create launch.json file inside .vscode directory

    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Remote Attach (DebugPy)",
                "type": "debugpy",
                "request": "attach",
                "connect": {
                    "host": "localhost",
                    "port": 5678
                },
                "pathMappings": [
                    {
                        "localRoot": "${workspaceFolder}",
                        "remoteRoot": "/app/"
                    }
                ],
                "justMyCode": true
            }
        ]
    }

