import csv
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import messagebox
import traceback
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
import threading
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import os

class UtilityTool(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Utility Tool")
        self.geometry("1000x1000")

        # Create input fields and labels for the database, user, and password
        tk.Label(self, text="Database Name:").grid(row=0, column=0, sticky="w")
        self.db_name_entry = tk.Entry(self)
        self.db_name_entry.grid(row=0, column=1)

        tk.Label(self, text="Table Name:").grid(row=1, column=0, sticky="w")
        self.table_name_entry = tk.Entry(self)
        self.table_name_entry.grid(row=1, column=1)

        tk.Label(self, text="Host:").grid(row=2, column=0, sticky="w")
        self.host_entry = tk.Entry(self)
        self.host_entry.grid(row=2, column=1)

        tk.Label(self, text="User:").grid(row=3, column=0, sticky="w")
        self.user_entry = tk.Entry(self)
        self.user_entry.grid(row=3, column=1)

        tk.Label(self, text="Password:").grid(row=4, column=0, sticky="w")
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.grid(row=4, column=1)

        # Create a button to create a database
        self.create_database_button = tk.Button(self, text="Create Database", command=self.create_database)
        self.create_database_button.grid(row=5, column=0, columnspan=2)

        # Create a button to load a CSV file
        self.load_csv_button = tk.Button(self, text="Load CSV", command=self.load_csv)
        self.load_csv_button.grid(row=6, column=0, columnspan=2)

        # Add a "Show Databases" button
        self.show_databases_button = tk.Button(self, text="Show Databases", command=self.show_databases)
        self.show_databases_button.grid(row=7, column=0, columnspan=2)

        # Create a Treeview widget for displaying databases, tables, and columns
        self.tree = ttk.Treeview(self)
        self.tree.grid(row=8, column=0, columnspan=2, sticky="nsew")
        self.tree.heading("#0", text="Databases")

        # Create input fields and labels for start and end dates
        tk.Label(self, text="Start Date:").grid(row=9, column=0, sticky="w")
        self.start_date_entry = tk.Entry(self)
        self.start_date_entry.grid(row=9, column=1)

        tk.Label(self, text="End Date:").grid(row=10, column=0, sticky="w")
        self.end_date_entry = tk.Entry(self)
        self.end_date_entry.grid(row=10, column=1)

        # Create a button to plot data
        self.plot_data_button = tk.Button(self, text="Plot Data", command=self.plot_data)
        self.plot_data_button.grid(row=11, column=0, columnspan=2)
        
        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.grid(row=12, column=0, columnspan=2, sticky="nsew")
        # Configure the new frame's row and column for resizing
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        # Create a canvas and add it to the new frame
        figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = figure.add_subplot(111)  # Initialize the axis
        self.canvas = FigureCanvasTkAgg(figure, self.canvas_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        # Create a new frame for the toolbar
        self.toolbar_frame = tk.Frame(self)
        self.toolbar_frame.grid(row=13, column=0, columnspan=2, sticky="ew")

        # Add the toolbar to the toolbar frame
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()
        # Bind the Treeview select event to the on_treeview_select method
        self.selected_item = None
        self.tree.bind("<<TreeviewSelect>>", self.on_treeview_select)

        # Add a MySQL connection instance variable
        self.connection = None

        # Bind the app closing event to close the connection
        self.protocol("WM_DELETE_WINDOW", self.disconnect)

        # Connect to the MySQL server using the configuration file
        self.connect()

        # Configure the rows and columns for resizing
        for i in range(12):
            self.grid_rowconfigure(i, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)


    def connect(self):
        if self.connection is not None:
            return

        # Read the configuration file
        config = {}
        with open("/Users/nicolaguarnera/Documents/Lavoro/CBM/config.txt", "r") as config_file:
            for line in config_file:
                key, value = line.strip().split(" = ")
                config[key] = value
        self.host = config["host"]
        self.user = config["user"]
        self.password = config["password"]
        self.db_name = config["db_name"]
        # Connect to the MySQL server using the configuration values
        self.connection = mysql.connector.connect(
            host=config["host"], user=config["user"], password=config["password"], 
            allow_local_infile=True)
       

    def create_database(self):
        # Retrieve db name for creating a database
        db_name = self.db_name_entry.get()

        # Connect to MySQL server and create a new database
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
            self.connection.commit()
            self.connection.close()
            print(f"Database '{db_name}' created successfully.")
        except mysql.connector.Error as error:
            print(f"Failed to create database: {error}")

    def load_csv(self):
        # Start a separate thread to load the CSV file
        threading.Thread(target=self.load_csv_thread).start()

    def load_csv_thread(self):
        cursor = self.connection.cursor()
        # Show a file dialog to select a CSV file
        file_path = filedialog.askopenfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        print(f'File Path: {file_path}')
        if not file_path:
            return

        # Retrieve table name for loading the CSV file
        table_name = self.table_name_entry.get()
        print(f'Inserted table_name: {table_name}')

        # Load the CSV file into the specified table in the MySQL database
        try:
            # Get the column names from the CSV file
            with open(file_path) as csvfile:
                reader = csv.reader(csvfile)
                column_names = next(reader)

            # Create the table with the appropriate columns
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join([f'{column_name} TEXT' for column_name in column_names])});"
            cursor.execute(create_table_query)

            # Use LOAD DATA INFILE to load the CSV file into the table
            load_data_query = f"""LOAD DATA LOCAL INFILE '{os.path.abspath(file_path)}'
                                INTO TABLE {table_name}
                                FIELDS TERMINATED BY ','
                                ENCLOSED BY '"'
                                LINES TERMINATED BY '\\n'
                                IGNORE 1 LINES;"""
            cursor.execute(load_data_query)

            self.connection.commit()
            # Close the cursor
            cursor.close()
            print(f"CSV file loaded into '{table_name}' table.")
        except Exception as error:
            print(f"Failed to load CSV file: {error}")


    def show_databases(self):
        # Start a separate thread to populate the Treeview widget
        threading.Thread(target=self.show_databases_thread).start()

    def show_databases_thread(self):
        cursor = self.connection.cursor()

        # Clear the existing Treeview items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Retrieve and display the databases
        cursor.execute("SHOW DATABASES")
        for db in cursor.fetchall():
            db_name = db[0]

            # Skip the "information_schema" database
            if db_name == "information_schema":
                continue

            db_item = self.tree.insert("", "end", text=db_name)

            # Retrieve and display the tables within each database
            cursor.execute(f"USE {db_name}")
            cursor.execute("SHOW TABLES")
            for table in cursor.fetchall():
                table_name = table[0]
                table_item = self.tree.insert(db_item, "end", text=table_name)

                # Retrieve and display the columns within each table
                cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                for column in cursor.fetchall():
                    column_name = column[0]
                    self.tree.insert(table_item, "end", text=column_name)
        # Close the cursor
        cursor.close()
    
    def on_treeview_select(self, event):
        selected_item = event.widget.selection()[0]
        item_data = self.tree.item(selected_item)
        parent = self.tree.parent(selected_item)
        item_data['parent'] = parent
        self.selected_item = item_data
        print(f"Selected item: {self.selected_item}")
        
        # Check if the selected item is a column
        if parent:
            grandparent = self.tree.parent(parent)
            item_data['grandparent'] = grandparent

            if grandparent:
                self.selected_column = item_data['text']
                self.selected_table = self.tree.item(parent)['text']
                print(f"Selected column: {self.selected_column}")
                print(f"Selected table: {self.selected_table}")
            else:
                self.selected_column = None
                self.selected_table = item_data['text']
                print(f"Selected table: {self.selected_table}")
        else:
            self.selected_column = None
            self.selected_table = None

        self.selected_item = item_data

        
        
    #schedules the plot_data method to run in the different thread:
    def plot_data(self):
        plot_thread = threading.Thread(target=self.plot_data_thread)
        plot_thread.start()

    def plot_data_thread(self):
        cursor = self.connection.cursor()
        print("Plot data called")
        if not self.selected_item or 'parent' not in self.selected_item:
            print("No table selected")
            return
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        if not start_date or not end_date:
            print("Start date or end date not provided")
            return
        self.plot_data_button.config(state="disabled")  
        print(f"Start date: {start_date}, End date: {end_date}")
        sql_query = f"SELECT timestamp, {self.selected_column} FROM {self.selected_table} WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}'"
        print(f"SQL query: {sql_query}")
        cursor.execute(sql_query)

        # Fetch the result
        result = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]

        # Convert the result into a pandas DataFrame
        df = pd.DataFrame(result, columns=column_names)
        # Close the cursor
        cursor.close()

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        # Sort the DataFrame by timestamp and the selected column
        df_selected = pd.DataFrame(pd.to_numeric(df[self.selected_column], errors='coerce'), columns=df.columns)
        # Clear the previous plot if any
        self.ax.cla()

        # Plot the data
        self.ax.plot(df.index,df_selected[self.selected_column])
        self.ax.set_facecolor('white')
        # Set the labels and title
        self.ax.set_xlabel('timestamp')
        self.ax.set_ylabel(self.selected_column)
        self.ax.set_title(f"{self.selected_column} vs Timestamp")
        # Limit the number of ticks on the y-axis
        self.ax.yaxis.set_major_locator(ticker.MaxNLocator(10))
        self.ax.grid()
        
        # Redraw the figure on the canvas
        self.canvas.draw()

        self.plot_data_button.config(state="normal")
    
    def disconnect(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

        # Close the app
        self.destroy()

if __name__ == "__main__":
    app = UtilityTool()
    app.mainloop()
