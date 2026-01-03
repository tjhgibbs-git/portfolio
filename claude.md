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

---

## Local Testing in Claude Code Web

### Quick Setup for Testing

When testing locally in Claude Code web environment, follow these steps:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create .env file for testing:**
   ```bash
   cat > .env << 'EOF'
   DJANGO_SECRET_KEY=test-secret-key-for-local-development
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
   MEDIA_URL=/media/
   STATIC_URL=/static/
   EOF
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Test the server:**
   ```bash
   # Start server in background
   python manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
   
   # Wait for server to start
   sleep 5
   
   # Test all main pages
   curl -s -o /dev/null -w "Blog: %{http_code}\n" http://localhost:8000/
   curl -s -o /dev/null -w "Portfolio: %{http_code}\n" http://localhost:8000/projects/
   curl -s -o /dev/null -w "Recipes: %{http_code}\n" http://localhost:8000/recipes/
   curl -s -o /dev/null -w "Tools: %{http_code}\n" http://localhost:8000/tools/
   
   # Clean up
   pkill -f runserver
   ```

### Expected Results
- All pages should return `200` status code
- If you get `500` errors, check that migrations are run and .env exists
- If you get `000` errors, server isn't running - check for port conflicts

### Common Issues

**Database tables don't exist:**
```bash
python manage.py migrate
```

**SECRET_KEY missing:**
Create `.env` file with `DJANGO_SECRET_KEY` set (see step 2 above)

**Server won't start:**
```bash
pkill -f runserver  # Kill any existing servers
python manage.py runserver 0.0.0.0:8000
```

---

## Dark Mode Implementation (Jan 2026)

### Features
- System preference detection via `prefers-color-scheme`
- Manual toggle button in footer with sun/moon icons
- LocalStorage persistence of user preference
- WCAG AA compliant color contrast ratios
- Color blindness accessible (blue/orange palette)
- No flash of unstyled content (FOUC prevention)

### Key Files
- `static/css/main.css` - Core color variables and dark mode
- `static/js/main.js` - Theme detection and toggle logic
- `templates/base.html` - Toggle button and FOUC prevention
- `static/css/about.css` - About page dark mode
- `static/css/contact.css` - Contact page dark mode
- `static/css/blog.css` - Blog page dark mode

### Color Palette
**Light Mode:**
- Primary: #1a5490 (blue)
- Secondary: #0077cc (lighter blue)
- Accent: #ff6b35 (orange)
- Background: #ffffff / #f5f5f5

**Dark Mode:**
- Primary: #4a9eff (bright blue)
- Secondary: #66b3ff (lighter blue)
- Accent: #ff8c5a (bright orange)
- Background: #1a1a1a / #2a2a2a

### Testing Dark Mode
```bash
# Check toggle button exists
curl -s http://localhost:8000/ | grep "theme-toggle"

# Verify theme initialization script
curl -s http://localhost:8000/ | grep "data-theme"
```
