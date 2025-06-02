import os
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, F
from tools.models import Tool

class Command(BaseCommand):
    help = 'Export tools to file system for git backup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force export all tools, not just changed ones',
        )
        parser.add_argument(
            '--git-commit',
            action='store_true',
            help='Automatically commit changes to git',
        )

    def handle(self, *args, **options):
        export_dir = getattr(settings, 'TOOLS_EXPORT_DIR', settings.BASE_DIR / 'tools_backup')
        export_dir = Path(export_dir)
        
        # Create export directory if it doesn't exist
        export_dir.mkdir(exist_ok=True)
        (export_dir / 'tools').mkdir(exist_ok=True)
        
        # Get tools that need export
        if options['force']:
            tools_to_export = Tool.objects.all()
            self.stdout.write("Forcing export of all tools...")
        else:
            tools_to_export = Tool.objects.filter(
                Q(last_exported__isnull=True) | 
                Q(updated_at__gt=F('last_exported'))
            )
        
        if not tools_to_export.exists():
            self.stdout.write(self.style.SUCCESS('No tools need exporting. All up to date!'))
            return
        
        exported_count = 0
        errors = []
        
        # Export individual tools
        for tool in tools_to_export:
            try:
                self.export_tool(tool, export_dir)
                tool.last_exported = timezone.now()
                tool.save(update_fields=['last_exported'])
                exported_count += 1
                self.stdout.write(f"✓ Exported: {tool.name}")
            except Exception as e:
                errors.append(f"Error exporting {tool.name}: {str(e)}")
                self.stderr.write(f"✗ Failed: {tool.name} - {str(e)}")
        
        # Create/update manifest
        try:
            self.create_manifest(export_dir)
            self.stdout.write("✓ Updated manifest.json")
        except Exception as e:
            errors.append(f"Error creating manifest: {str(e)}")
        
        # Create README
        try:
            self.create_readme(export_dir)
            self.stdout.write("✓ Updated README.md")
        except Exception as e:
            errors.append(f"Error creating README: {str(e)}")
        
        # Git operations
        if options['git_commit']:
            self.git_commit_changes(export_dir, exported_count)
        
        # Summary
        if exported_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully exported {exported_count} tool(s) to {export_dir}'
                )
            )
        
        if errors:
            self.stdout.write(self.style.ERROR(f'\nErrors occurred:'))
            for error in errors:
                self.stderr.write(f"  - {error}")

    def export_tool(self, tool, export_dir):
        """Export a single tool to the file system"""
        tool_dir = export_dir / 'tools' / tool.slug
        tool_dir.mkdir(exist_ok=True)
        
        # Save HTML content
        html_file = tool_dir / 'index.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(tool.html_content)
        
        # Save metadata
        metadata = {
            'name': tool.name,
            'slug': tool.slug,
            'description': tool.description,
            'is_active': tool.is_active,
            'created_at': tool.created_at.isoformat(),
            'updated_at': tool.updated_at.isoformat(),
            'view_count': tool.view_count,
            'url': f'/tools/{tool.slug}/',
        }
        
        metadata_file = tool_dir / 'metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def create_manifest(self, export_dir):
        """Create a manifest of all exported tools"""
        tools = Tool.objects.all().order_by('name')
        
        manifest = {
            'exported_at': timezone.now().isoformat(),
            'total_tools': tools.count(),
            'active_tools': tools.filter(is_active=True).count(),
            'tools': []
        }
        
        for tool in tools:
            manifest['tools'].append({
                'name': tool.name,
                'slug': tool.slug,
                'description': tool.description,
                'is_active': tool.is_active,
                'created_at': tool.created_at.isoformat(),
                'updated_at': tool.updated_at.isoformat(),
                'view_count': tool.view_count,
                'url': f'/tools/{tool.slug}/',
                'file_path': f'tools/{tool.slug}/index.html'
            })
        
        manifest_file = export_dir / 'manifest.json'
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    def create_readme(self, export_dir):
        """Create a README file explaining the backup"""
        tools = Tool.objects.all().order_by('name')
        active_tools = tools.filter(is_active=True)
        
        readme_content = f"""# Tools Backup

This directory contains exported tools from the website for version control backup.

## Summary
- **Total Tools:** {tools.count()}
- **Active Tools:** {active_tools.count()}
- **Last Updated:** {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

## Structure
```
tools_backup/
├── manifest.json          # Complete manifest of all tools
├── README.md              # This file
└── tools/                 # Individual tool directories
    ├── tool-slug-1/
    │   ├── index.html     # Tool HTML content
    │   └── metadata.json  # Tool metadata
    └── tool-slug-2/
        ├── index.html
        └── metadata.json
```

## Active Tools
"""
        
        for tool in active_tools:
            readme_content += f"- **{tool.name}** (`{tool.slug}`) - {tool.view_count} views\n"
            if tool.description:
                readme_content += f"  - {tool.description}\n"
        
        readme_content += f"""
## Usage
These files are automatically exported from the Django admin when tools are created or updated.

To restore or import these tools, use the Django management command:
```bash
python manage.py import_tools --from-backup
```

## Auto-Export
Tools are automatically exported when:
1. A new tool is created
2. An existing tool is updated
3. The daily cron job runs (if changes detected)

Export command: `python manage.py export_tools`
"""
        
        readme_file = export_dir / 'README.md'
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)

    def git_commit_changes(self, export_dir, exported_count):
        """Commit changes to git if git is available"""
        try:
            import subprocess
            
            # Check if we're in a git repo
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=export_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.stdout.write(self.style.WARNING("Not in a git repository, skipping git commit"))
                return
            
            # Add changes
            subprocess.run(['git', 'add', '.'], cwd=export_dir, check=True)
            
            # Check if there are changes to commit
            result = subprocess.run(
                ['git', 'diff', '--cached', '--quiet'],
                cwd=export_dir,
                capture_output=True
            )
            
            if result.returncode == 0:
                self.stdout.write("No git changes to commit")
                return
            
            # Commit changes
            commit_message = f"Auto-export {exported_count} tool(s) - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=export_dir,
                check=True
            )
            
            self.stdout.write(self.style.SUCCESS(f"✓ Git commit created: {commit_message}"))
            
        except subprocess.CalledProcessError as e:
            self.stderr.write(f"Git operation failed: {e}")
        except ImportError:
            self.stderr.write("subprocess module not available for git operations")

