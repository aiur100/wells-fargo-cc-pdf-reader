# CLAUDE.md - Guidelines for Working with this Codebase

## Commands
- Run the application: `python main.py <directory_path>`
- Install dependencies: `pip install -r requirements.txt`
- Formatting: `black .` (recommended, not yet implemented)
- Type checking: `mypy .` (recommended, not yet implemented)

## Code Style Guidelines
- **Imports**: Standard library first, then third-party, then local modules
- **Formatting**: 4-space indentation, 88 char line length (Black-compatible)
- **Types**: Add type hints to function parameters and return values
- **Naming**: 
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`
- **Error Handling**: Use try/except blocks for file operations and parsing
- **Documentation**: Add docstrings to functions explaining parameters and returns
- **Code Organization**: Keep related functionality in the same module

## Project Structure
This project parses Wells Fargo credit card statement PDFs and outputs transaction data to CSV.