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

## 📁 Repository Structure

The project follows a modular MVC (Model-View-Controller) architecture:

* **assets/**: UI style configurations and media files.
* **backend/**: Database connection logic and session management.
* **database/**: SQL schema scripts and Faker-powered data seeders.
* **frontend/**: Modular UI components and individual application tabs.
* **utils/**: Helper functions and data input validators.

## 👥 Access Control

The system implements Role-Based Access Control (RBAC):

* **Manager**: Full access to all modules, including Payroll and Reports.
* **Sales Rep**: Access restricted to Customers, Orders, Inventory and Payroll (to see payroll history).
* **Hourly Employee**: Access restricted to Payroll (to submit timecard and see payroll history) and Reports.
