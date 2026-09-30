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

    @app.cli.command('reverify-products')
    def reverify_products_cmd():
        """Re-run moderation on unverified/legacy products and update moderation status."""
        from backend.app.models.product import Product
        from backend.app.models.moderation_log import ProductModerationLog
        from backend.app.services.moderation_service import moderate_product_image
        from datetime import datetime

        # Find legacy products or unverified products
        products = Product.query.all()
        if not products:
            click.echo("No products found to reverify.")
            return

        click.echo(f"Re-verifying {len(products)} products against content moderation engine...")
        click.echo("=" * 110)
        click.echo(f"{'ID':<5} | {'Name':<22} | {'Old Status':<12} | {'New Status':<12} | {'Reason':<45}")
        click.echo("=" * 110)

        updated_count = 0
        for p in products:
            old_status = p.moderation_status or 'NULL'
            mod_input = p.image
            mod_result = moderate_product_image(mod_input, p.category or 'Vegetables', p.name or 'Fresh Produce')

            new_status = mod_result.get('decision', 'needs_review')
            if new_status == 'unavailable':
                new_status = 'needs_review'
            reason = mod_result.get('reason', 'Re-verification completed.')
            raw_output = mod_result.get('raw_model_output', '')

            p.moderation_status = new_status
            p.moderation_reason = reason
            p.moderated_at = datetime.utcnow()
            p.moderated_by = 'ai_reverify'

            log = ProductModerationLog(
                product_id=p.id,
                user_id=p.user_id,
                decision=new_status,
                reason=reason,
                raw_model_output=raw_output,
                decided_by='ai_reverify',
                created_at=datetime.utcnow()
            )
            db.session.add(log)
            updated_count += 1

            name_disp = p.name[:20] if p.name else 'Unnamed'
            reason_disp = reason[:42] + '...' if len(reason) > 42 else reason
            click.echo(f"{p.id:<5} | {name_disp:<22} | {old_status:<12} | {new_status:<12} | {reason_disp:<45}")

        db.session.commit()
        click.echo("=" * 110)
        click.echo(f"Done! Reverified {updated_count} products.")

