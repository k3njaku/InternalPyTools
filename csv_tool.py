import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QListWidget, QFileDialog, QLabel,
    QAbstractItemView
)
from PySide6.QtCore import Qt # Qt is often imported directly from QtCore

class CSVColumnSelector(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CSV Column Selector (PySide6)")
        self.setGeometry(100, 100, 600, 450) # Adjusted height slightly for status

        self.dataframe = None  # To hold the loaded pandas DataFrame
        self.current_filepath = None # To store the path of the loaded file
        self.original_columns = [] # To store the original columns of the loaded file

        # --- Widgets ---
        self.open_button = QPushButton("Open CSV File")
        self.open_button.clicked.connect(self.open_csv_file)

        self.column_list_label = QLabel("Available Columns:")
        self.column_list = QListWidget()
        # Allow multiple items to be selected using Ctrl or Shift
        self.column_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.keep_button = QPushButton("Keep Selected Columns")
        self.keep_button.clicked.connect(self.keep_selected_columns)
        self.keep_button.setEnabled(False)  # Disable until file is loaded

        self.remove_button = QPushButton("Remove Selected Columns")
        self.remove_button.clicked.connect(self.remove_selected_columns)
        self.remove_button.setEnabled(False)  # Disable until file is loaded

        self.save_button = QPushButton("Save Modified CSV As...")
        self.save_button.clicked.connect(self.save_csv_file)
        self.save_button.setEnabled(False) # Disable until data is loaded and potentially modified

        self.reset_button = QPushButton("Reset to Original Columns")
        self.reset_button.clicked.connect(self.reset_columns)
        self.reset_button.setEnabled(False)

        self.status_label = QLabel("Please open a CSV file.")
        self.status_label.setWordWrap(True) # Allow status to wrap if long

        # --- Layout ---
        top_controls_layout = QHBoxLayout()
        top_controls_layout.addWidget(self.open_button)
        top_controls_layout.addWidget(self.reset_button)


        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addWidget(self.keep_button)
        action_buttons_layout.addWidget(self.remove_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_controls_layout)
        main_layout.addWidget(self.column_list_label)
        main_layout.addWidget(self.column_list)
        main_layout.addLayout(action_buttons_layout)
        main_layout.addWidget(self.save_button)
        main_layout.addWidget(self.status_label)
        main_layout.addStretch()  # Push everything to the top

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def open_csv_file(self):
        """Opens a file dialog to select a CSV and loads it."""
        file_dialog = QFileDialog(self)
        # Use getOpenFileName for selecting a single file
        filepath, _ = file_dialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")

        if filepath:
            try:
                self.dataframe = pd.read_csv(filepath)
                self.current_filepath = filepath
                self.original_columns = self.dataframe.columns.tolist()
                self.populate_column_list(self.original_columns)
                self.status_label.setText(f"Loaded: {filepath}\n{len(self.original_columns)} columns.")
                self.keep_button.setEnabled(True)
                self.remove_button.setEnabled(True)
                self.save_button.setEnabled(True)
                self.reset_button.setEnabled(True)
            except Exception as e:
                self.dataframe = None
                self.current_filepath = None
                self.original_columns = []
                self.populate_column_list([])
                self.status_label.setText(f"Error loading file: {e}")
                self.keep_button.setEnabled(False)
                self.remove_button.setEnabled(False)
                self.save_button.setEnabled(False)
                self.reset_button.setEnabled(False)

    def populate_column_list(self, columns_to_display):
        """Clears and populates the QListWidget with column names."""
        self.column_list.clear()
        if columns_to_display:
            self.column_list.addItems(columns_to_display)

    def get_selected_columns_from_list(self):
        """Returns a list of text from selected items in the QListWidget."""
        selected_items = self.column_list.selectedItems()
        return [item.text() for item in selected_items]

    def keep_selected_columns(self):
        """Keeps only the selected columns in the DataFrame."""
        if self.dataframe is None:
            self.status_label.setText("No CSV file loaded.")
            return

        selected_cols = self.get_selected_columns_from_list()
        if not selected_cols:
            self.status_label.setText("No columns selected to keep. Please select columns from the list.")
            return

        # Ensure all selected columns actually exist in the current dataframe
        # This check is more robust if the list widget could somehow get out of sync
        valid_selected = [col for col in selected_cols if col in self.dataframe.columns]

        if not valid_selected:
            self.status_label.setText("Selected columns not found in current data. This shouldn't happen if list is correct.")
            return

        if len(valid_selected) == len(self.dataframe.columns):
            self.status_label.setText("All current columns are selected. No change made.")
            return

        try:
            self.dataframe = self.dataframe[valid_selected]
            self.populate_column_list(self.dataframe.columns.tolist())
            self.status_label.setText(f"Kept {len(valid_selected)} columns. Save the file to persist changes.")
        except Exception as e:
            self.status_label.setText(f"Error keeping columns: {e}")

    def remove_selected_columns(self):
        """Removes the selected columns from the DataFrame."""
        if self.dataframe is None:
            self.status_label.setText("No CSV file loaded.")
            return

        selected_cols_to_remove = self.get_selected_columns_from_list()
        if not selected_cols_to_remove:
            self.status_label.setText("No columns selected to remove. Please select columns from the list.")
            return

        # Filter out columns that might have been already removed or don't exist
        actual_cols_to_remove = [col for col in selected_cols_to_remove if col in self.dataframe.columns]

        if not actual_cols_to_remove:
            self.status_label.setText("None of the selected columns are present in the current dataset.")
            return

        try:
            self.dataframe = self.dataframe.drop(columns=actual_cols_to_remove)
            self.populate_column_list(self.dataframe.columns.tolist())
            self.status_label.setText(f"Removed {len(actual_cols_to_remove)} columns. Save the file to persist changes.")
        except Exception as e:
            self.status_label.setText(f"Error removing columns: {e}")

    def reset_columns(self):
        """Resets the DataFrame to its originally loaded state."""
        if self.current_filepath and self.original_columns:
            try:
                # Re-read the original file to ensure a clean state
                self.dataframe = pd.read_csv(self.current_filepath)
                # Or, if you want to avoid re-reading and trust the stored original_columns:
                # self.dataframe = self.dataframe[self.original_columns] # This assumes self.dataframe wasn't set to None
                self.populate_column_list(self.original_columns)
                self.status_label.setText(f"Columns reset to original state from: {self.current_filepath}")
            except Exception as e:
                self.status_label.setText(f"Error resetting columns: {e}")
        else:
            self.status_label.setText("No file loaded or original state not available to reset.")


    def save_csv_file(self):
        """Saves the (potentially modified) DataFrame to a new CSV file."""
        if self.dataframe is None:
            self.status_label.setText("No data to save.")
            return

        file_dialog = QFileDialog(self)
        # Use getSaveFileName for saving a file
        filepath, _ = file_dialog.getSaveFileName(self, "Save CSV File As...", "", "CSV Files (*.csv);;All Files (*)")

        if filepath:
            try:
                # Ensure .csv extension if not provided by user
                if not filepath.lower().endswith(".csv"):
                    filepath += ".csv"
                self.dataframe.to_csv(filepath, index=False) # index=False is common for CSVs
                self.status_label.setText(f"File saved successfully to: {filepath}")
            except Exception as e:
                self.status_label.setText(f"Error saving file: {e}")

# --- Application Entry Point ---
if __name__ == "__main__":
    app = QApplication(sys.argv)  # QApplication instance
    window = CSVColumnSelector()  # Create an instance of our main window
    window.show()                 # Show the window
    sys.exit(app.exec())          # Start the Qt event loop
