# National Office Supplies Management System

This is a Desktop Management System developed for the Information Management (BIS) project. The system handles inventory, sales, and payroll, featuring a modular Tkinter frontend and a PostgreSQL backend.

## 🚀 One-Click Start (Recommended)

If you are on Windows, simply double-click the **`START_SYSTEM.bat`** file in the root directory. This script will:

1. Automatically create a local virtual environment.
2. Install all required dependencies (`psycopg2-binary`, `python-dotenv`, `faker`, `customtkinter`, `cryptography`).
3. Launch the application entry point.

## 🛠️ Manual Developer Setup

If you prefer to set up the environment manually, follow these steps:

### 1. Environment Setup

```powershell
# Create and activate the virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r dev-requirements.txt
```

### 3. Database Configuration

Create a file named `.env` in the root directory with your PostgreSQL credentials:

```text
DB_HOST=localhost
DB_NAME=postgres
DB_USER=postgres
DB_PASS=your_password_here
```

Database setup order (important):

1. Run the database schema script to create tables and schema objects.
2. Run the seed data script to populate initial data.

Files:

- `national_office_supply_BIS/national_office_supply_BIS/database/NOS_db_Schema.sql`
- `national_office_supply_BIS/national_office_supply_BIS/database/SeedData.sql`

Examples — PowerShell (non-interactive):

```powershell
#$env:DB_PASS is read from your .env or set directly for this session
#$env:PGPASSWORD avoids interactive password prompt
$env:DB_HOST = 'localhost'
$env:DB_NAME = 'postgres'
$env:DB_USER = 'postgres'
$env:PGPASSWORD = 'your_password_here'

# Run schema first
psql -h $env:DB_HOST -U $env:DB_USER -d $env:DB_NAME -f "national_office_supply_BIS/national_office_supply_BIS/database/NOS_db_Schema.sql"

# Then run seed data
psql -h $env:DB_HOST -U $env:DB_USER -d $env:DB_NAME -f "national_office_supply_BIS/national_office_supply_BIS/database/SeedData.sql"

# Quick verification: list tables
psql -h $env:DB_HOST -U $env:DB_USER -d $env:DB_NAME -c "\dt"
```

Examples — psql interactive (alternative):

```sh
# Open psql, then run inside the prompt:
# \i path/to/NOS_db_Schema.sql
# \i path/to/SeedData.sql
psql -h localhost -U postgres -d postgres
\i national_office_supply_BIS/national_office_supply_BIS/database/NOS_db_Schema.sql
\i national_office_supply_BIS/national_office_supply_BIS/database/SeedData.sql
```

Notes:

- Always run `NOS_db_Schema.sql` before `SeedData.sql` to avoid foreign-key and object-not-found errors.
- If `psql` is not on your PATH, use the full path to the `psql` executable (for example, from the PostgreSQL installation `bin` folder).
- For CI or scripted setups you can export `PGPASSWORD` or use a `.pgpass` file for non-interactive authentication.
- After the DB is prepared, you can run the application using `START_SYSTEM.bat` or the manual steps above.

Files (repo paths):

- `national_office_supply_BIS_project/national_office_supply_BIS/src/database/NOS_db_Schema.sql`
- `national_office_supply_BIS_project/national_office_supply_BIS/src/database/SeedData.sql`
- `national_office_supply_BIS_project/national_office_supply_BIS/src/database/queries.sql`

Database repository structure (quick view):

```
national_office_supply_BIS_project/
└─ national_office_supply_BIS/
	└─ src/
		└─ database/
			├─ NOS_db_Schema.sql        # creates tables, constraints, indexes
			├─ SeedData.sql             # initial data inserts (run after schema)
			└─ queries.sql              # reusable query snippets and views
```

Run the app (recommended):

From the repository root you can run the main module directly. This runs the GUI application entrypoint in `src/__main__.py`:

```powershell
# Run the main script directly (from repo root)
python national_office_supply_BIS_project\national_office_supply_BIS\src\__main__.py
```

Or run as a module if you prefer (may require adjusting PYTHONPATH/installing package):

```powershell
# Example module run (if package is importable)
python -m national_office_supply_BIS.src
```

## 📁 Repository Structure

The project follows a modular MVC (Model-View-Controller) architecture:

- **assets/**: UI style configurations and media files.
- **backend/**: Database connection logic and session management.
- **database/**: SQL schema scripts and Faker-powered data seeders.
- **frontend/**: Modular UI components and individual application tabs.
- **utils/**: Helper functions and data input validators.

## 👥 Access Control

The system implements Role-Based Access Control (RBAC):

- **Manager**: Full access to all modules, including Payroll and Reports.
- **Sales Rep**: Access restricted to Customers, Orders, Inventory and Payroll (to see payroll history).
- **Hourly Employee**: Access restricted to Payroll (to submit timecard and see payroll history) and Reports.

## 🧪 Test Accounts (demo)

Use these demo credentials for quick testing when you don't have DB access or while the database is initializing. The application falls back to these mock accounts if real DB authentication fails (see `src/frontend/tabs/login.py`).

- **Manager**: username `manager` or `msantos` — password `admin123`  (maps to Maria Santos-Reyes)
- **Sales Rep**: username `rep` or `klim` — password `sales123`      (maps to Kevin Lim)
- **Hourly**: username `hourly` or `maquino` — password `worker123`   (maps to Mark Aquino)
