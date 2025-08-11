import sys
import argparse
import uvicorn

# We need to modify the path to ensure 'src' is in the import path
# for when the CLI is called.
from src.cli.main import run_cli
from src.api.main import app

def main():
    # This is a simple top-level parser to select the execution mode: cli or api.
    parser = argparse.ArgumentParser(
        description="Main entry point for the SUNAT File Finder & Processor."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True, help="Execution mode")

    # API sub-parser
    api_parser = subparsers.add_parser("api", help="Run the web API server.")
    api_parser.add_argument("--host", default="127.0.0.1", help="Host for the API server.")
    api_parser.add_argument("--port", type=int, default=8000, help="Port for the API server.")

    # CLI sub-parser
    # We use add_help=False because the CLI module has its own complex parser.
    # It will handle all arguments past 'cli'.
    cli_parser = subparsers.add_parser("cli", help="Run the command-line interface.", add_help=False)

    # Check which mode is being invoked
    # We only parse the first argument to decide between 'cli' and 'api'
    if len(sys.argv) > 1 and sys.argv[1] == 'api':
        args = parser.parse_args()
        print(f"Starting API server on http://{args.host}:{args.port}")
        print("Access interactive docs at http://{args.host}:{args.port}/docs")
        uvicorn.run(app, host=args.host, port=args.port)
    elif len(sys.argv) > 1 and sys.argv[1] == 'cli':
        # The CLI module will handle its own arguments
        # We remove the 'cli' command itself from the list of arguments
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        run_cli()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()