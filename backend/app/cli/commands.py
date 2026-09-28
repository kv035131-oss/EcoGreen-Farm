"""
Flask CLI Custom Commands Module.
"""

import click
from flask import Blueprint
from werkzeug.security import generate_password_hash
from backend.app.extensions import db
from backend.app.models.user import User

cli_bp = Blueprint('cli', __name__)

def register_cli_commands(app):
    """Register custom CLI commands with the Flask app."""

    @app.cli.command('create-admin')
    @click.option('--username', default='admin', help='Admin username')
    @click.option('--email', default='admin@ecogreen.com', help='Admin email')
    @click.option('--password', default='admin123', help='Admin password')
    def create_admin_cmd(username, email, password):
        """Create an administrative user if one does not exist."""
        existing = User.query.filter_by(username=username).first()
        if existing:
            click.echo(f"Admin user '{username}' already exists.")
            return
        admin = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            user_type='admin',
            status='Active'
        )
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Successfully created admin user '{username}'.")

    @app.cli.command('seed-demo-data')
    def seed_demo_data_cmd():
        """Seed demo farmers, consumers, products, orders, transactions, and reviews."""
        from database.seeds.seed_demo import seed_demo_data
        seed_demo_data()
        click.echo("Demo data successfully seeded.")
