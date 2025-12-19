#!/bin/bash
#############################################
# AdSphere Hybrid System Setup Script
# Automates database setup and migration
#############################################

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DB_DIR="$SCRIPT_DIR/app/database"
BACKUP_DIR="$SCRIPT_DIR/backups"

echo "========================================="
echo "  AdSphere Hybrid System Setup"
echo "========================================="
echo ""

# Check PHP
if ! command -v php &> /dev/null; then
    echo "❌ PHP is not installed. Please install PHP first."
    exit 1
fi

echo "✅ PHP found: $(php -v | head -n 1)"
echo ""

# Check SQLite extension
if ! php -m | grep -q "sqlite3"; then
    echo "❌ PHP SQLite3 extension not found. Please install it."
    exit 1
fi

echo "✅ SQLite3 extension found"
echo ""

# Create backup directory
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    echo "✅ Created backup directory"
fi

# Backup existing data
echo "📦 Creating backup of existing data..."
BACKUP_FILE="$BACKUP_DIR/adsphere_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" app/companies/data app/companies/metadata 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backup created: $BACKUP_FILE"
else
    echo "⚠️  Backup failed or no data found (this is OK for new installations)"
fi
echo ""

# Create database directory
if [ ! -d "$DB_DIR" ]; then
    mkdir -p "$DB_DIR"
    echo "✅ Created database directory"
fi

# Create locks directory
if [ ! -d "$DB_DIR/locks" ]; then
    mkdir -p "$DB_DIR/locks"
    echo "✅ Created locks directory"
fi

# Create backups directory
if [ ! -d "$DB_DIR/backups" ]; then
    mkdir -p "$DB_DIR/backups"
    echo "✅ Created database backups directory"
fi

echo ""
echo "========================================="
echo "  Database Migration Options"
echo "========================================="
echo ""
echo "1. Dry Run (preview migration)"
echo "2. Full Migration (migrate all data)"
echo "3. Skip migration (manual later)"
echo ""

read -p "Select option (1-3): " OPTION

case $OPTION in
    1)
        echo ""
        echo "🔍 Running dry run..."
        php "$DB_DIR/migrate.php" --dry-run
        ;;
    2)
        echo ""
        echo "⚠️  WARNING: This will migrate all data to the database."
        echo "A backup has been created at: $BACKUP_FILE"
        echo ""
        read -p "Continue with migration? (yes/no): " CONFIRM

        if [ "$CONFIRM" = "yes" ]; then
            echo ""
            echo "🚀 Starting migration..."
            echo "yes" | php "$DB_DIR/migrate.php"

            if [ $? -eq 0 ]; then
                echo ""
                echo "✅ Migration completed successfully!"
                echo ""
                echo "Database created at: $DB_DIR/adsphere.db"
                echo "Database size: $(du -h "$DB_DIR/adsphere.db" | cut -f1)"
                echo ""
            else
                echo ""
                echo "❌ Migration failed. Check error messages above."
                echo "Your original data is safe in: $BACKUP_FILE"
                exit 1
            fi
        else
            echo "Migration cancelled."
        fi
        ;;
    3)
        echo "Skipping migration. You can run it manually later:"
        echo "  cd app/database"
        echo "  php migrate.php"
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "✅ Hybrid system is ready!"
echo ""
echo "Next steps:"
echo "  1. Upload a test ad to verify it works"
echo "  2. Check database: sqlite3 app/database/adsphere.db"
echo "  3. Monitor performance improvements"
echo ""
echo "Database location: $DB_DIR/adsphere.db"
echo "Backup location: $BACKUP_FILE"
echo ""
echo "For help, see: HYBRID_SYSTEM_COMPLETE.md"
echo ""

