# Claude Development Guidelines

This document contains important guidelines and conventions for working on this Django portfolio project.

## Git Practices

### Commit Regularly
- Make commits frequently with clear, descriptive messages
- Commit logical chunks of work rather than batching everything at the end
- Use the standard commit message format with context about what changed and why

### Security - .env Files
- **NEVER commit .env files** - they are gitignored for security reasons
- .env contains sensitive data like SECRET_KEY and should remain local only
- Use .env.example as a template for required environment variables
- This is a development server only - production uses different configuration

## Python Environment

### Always Use Virtual Environment (venv)
- All Python/Django commands must be run in the virtual environment
- Activate with: `source venv/bin/activate`
- The venv directory is gitignored
- Dependencies are tracked in requirements.txt

## Django Development

### Running the Development Server
- The server runs locally on port 8000
- This is for development/testing only
- Use: `source venv/bin/activate && python manage.py runserver`

### Database Migrations
- Run migrations after model changes: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`
- The SQLite database (db.sqlite3) is gitignored

## Project Structure

### Apps Follow Consistent Pattern
- Each feature is a separate Django app (main, blog, tools, recipes)
- Apps include: models.py, views.py, urls.py, admin.py, templates/
- All apps registered in mysite/settings/base.py
- URL routing configured in mysite/urls.py

### Admin Interface
- Custom admin forms with helpful interfaces (JSON paste, markdown editors, etc.)
- Color-coded list displays with filters
- Publish/draft workflow for content

## Code Style

### No Emojis
- Do NOT use emojis in code, admin interfaces, UI text, or commit messages unless explicitly requested
- Keep interfaces clean and professional
- Use color coding or text styling instead of emojis for visual distinction

### Commit Messages
- Clear, descriptive first line
- Detailed explanation in body
- Include "Generated with Claude Code" footer
- Include Co-Authored-By line

### Development Workflow
1. Set up virtual environment
2. Install dependencies from requirements.txt
3. Create .env from .env.example
4. Run migrations
5. Start development server
6. Test functionality
7. Commit changes regularly

## Important Files Not to Commit
- .env (environment variables)
- venv/ (virtual environment)
- db.sqlite3 (local database)
- media/ (uploaded files)
- __pycache__/ (Python cache)

All of these are already in .gitignore
