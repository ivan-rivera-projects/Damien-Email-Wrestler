import click
from damien_cli.features.ai_intelligence.commands import ai_group

@click.group()
def damien():
    """Main Damien CLI group"""
    pass

# Add AI commands group
damien.add_command(ai_group)

if __name__ == "__main__":
    damien()