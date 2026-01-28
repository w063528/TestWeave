import uvicorn
import click


@click.command(help="Run TestWeave local server")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=7341, show_default=True, type=int)
@click.option("--reload", is_flag=True, help="Enable auto-reload (dev only)")
def server(host: str, port: int, reload: bool):
    uvicorn.run(
        "testweave.server.app:app",
        host=host,
        port=port,
        reload=reload,
    )