import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from config import DB_PATH

DB_NAME = DB_PATH


class ClassTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("English Class Tracker")
        self.root.geometry("900x550")

        self.selected_id = None

        self.init_db()
        self.build_ui()
        self.load_records()

    # ---------- DATABASE ----------
    def init_db(self):
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_number INTEGER NOT NULL,
                    date_taken  TEXT NOT NULL,
                    topic       TEXT,
                    notes       TEXT,
                    status      TEXT DEFAULT 'Pending'
                )
            """)

    def db_execute(self, query, params=()):
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.execute(query, params)
            conn.commit()
            return cur

    def db_fetch(self, query, params=()):
        with sqlite3.connect(DB_NAME) as conn:
            return conn.execute(query, params).fetchall()

    # ---------- UI ----------
    def build_ui(self):
        # Form frame
        form = ttk.LabelFrame(self.root, text="Class Details", padding=10)
        form.pack(fill="x", padx=10, pady=8)

        ttk.Label(form, text="Class #:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.entry_class = ttk.Entry(form, width=10)
        self.entry_class.grid(row=0, column=1, padx=5, pady=4, sticky="w")

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.entry_date = ttk.Entry(form, width=14)
        self.entry_date.grid(row=0, column=3, padx=5, pady=4, sticky="w")
        self.entry_date.insert(0, str(date.today()))

        ttk.Label(form, text="Topic:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.entry_topic = ttk.Entry(form, width=40)
        self.entry_topic.grid(row=1, column=1, columnspan=3, padx=5, pady=4, sticky="we")

        ttk.Label(form, text="Status:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.combo_status = ttk.Combobox(
            form, values=["Pending", "In Progress", "Completed"], state="readonly", width=15
        )
        self.combo_status.current(0)
        self.combo_status.grid(row=2, column=1, padx=5, pady=4, sticky="w")

        ttk.Label(form, text="Notes:").grid(row=3, column=0, sticky="nw", padx=5, pady=4)
        self.text_notes = tk.Text(form, height=3, width=70)
        self.text_notes.grid(row=3, column=1, columnspan=3, padx=5, pady=4, sticky="we")

        # Buttons
        btns = ttk.Frame(self.root)
        btns.pack(fill="x", padx=10, pady=4)

        ttk.Button(btns, text="➕ Add", command=self.add_record).pack(side="left", padx=4)
        ttk.Button(btns, text="✏️ Update", command=self.update_record).pack(side="left", padx=4)
        ttk.Button(btns, text="🗑️ Delete", command=self.delete_record).pack(side="left", padx=4)
        ttk.Button(btns, text="🧹 Clear Form", command=self.clear_form).pack(side="left", padx=4)

        # Search
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill="x", padx=10, pady=4)
        ttk.Label(search_frame, text="Search (class # or topic):").pack(side="left")
        self.entry_search = ttk.Entry(search_frame, width=30)
        self.entry_search.pack(side="left", padx=6)
        ttk.Button(search_frame, text="🔍 Filter", command=self.load_records).pack(side="left", padx=4)
        ttk.Button(search_frame, text="↻ Show All", command=self.show_all).pack(side="left", padx=4)

        # Table
        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=10, pady=8)

        cols = ("id", "class_number", "date_taken", "topic", "status", "notes")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        headers = {
            "id": ("ID", 40),
            "class_number": ("Class #", 70),
            "date_taken": ("Date", 100),
            "topic": ("Topic", 220),
            "status": ("Status", 100),
            "notes": ("Notes", 280),
        }
        for c, (label, w) in headers.items():
            self.tree.heading(c, text=label)
            self.tree.column(c, width=w, anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    # ---------- CRUD ----------
    def validate_form(self):
        cnum = self.entry_class.get().strip()
        dt = self.entry_date.get().strip()
        if not cnum.isdigit():
            messagebox.showerror("Validation", "Class number must be a number.")
            return None
        try:
            date.fromisoformat(dt)
        except ValueError:
            messagebox.showerror("Validation", "Date must be in YYYY-MM-DD format.")
            return None
        return cnum, dt

    def add_record(self):
        v = self.validate_form()
        if not v:
            return
        cnum, dt = v
        topic = self.entry_topic.get().strip()
        notes = self.text_notes.get("1.0", "end").strip()
        status = self.combo_status.get()

        self.db_execute(
            "INSERT INTO classes (class_number, date_taken, topic, notes, status) VALUES (?,?,?,?,?)",
            (int(cnum), dt, topic, notes, status),
        )
        self.clear_form()
        self.load_records()
        messagebox.showinfo("Saved", f"Class #{cnum} added.")

    def update_record(self):
        if self.selected_id is None:
            messagebox.showwarning("Select", "Please select a record to update.")
            return
        v = self.validate_form()
        if not v:
            return
        cnum, dt = v
        topic = self.entry_topic.get().strip()
        notes = self.text_notes.get("1.0", "end").strip()
        status = self.combo_status.get()

        self.db_execute(
            """UPDATE classes SET class_number=?, date_taken=?, topic=?, notes=?, status=?
               WHERE id=?""",
            (int(cnum), dt, topic, notes, status, self.selected_id),
        )
        self.clear_form()
        self.load_records()
        messagebox.showinfo("Updated", "Record updated.")

    def delete_record(self):
        if self.selected_id is None:
            messagebox.showwarning("Select", "Please select a record to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected record?"):
            return
        self.db_execute("DELETE FROM classes WHERE id=?", (self.selected_id,))
        self.clear_form()
        self.load_records()

    # ---------- HELPERS ----------
    def load_records(self):
        search = self.entry_search.get().strip()
        if search:
            rows = self.db_fetch(
                """SELECT id, class_number, date_taken, topic, status, notes
                   FROM classes
                   WHERE CAST(class_number AS TEXT) LIKE ? OR topic LIKE ?
                   ORDER BY class_number DESC""",
                (f"%{search}%", f"%{search}%"),
            )
        else:
            rows = self.db_fetch(
                """SELECT id, class_number, date_taken, topic, status, notes
                   FROM classes ORDER BY class_number DESC"""
            )
        self.populate_tree(rows)

    def show_all(self):
        self.entry_search.delete(0, "end")
        self.load_records()

    def populate_tree(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in rows:
            self.tree.insert("", "end", values=r)

    def on_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self.selected_id = int(vals[0])

        self.entry_class.delete(0, "end"); self.entry_class.insert(0, vals[1])
        self.entry_date.delete(0, "end"); self.entry_date.insert(0, vals[2])
        self.entry_topic.delete(0, "end"); self.entry_topic.insert(0, vals[3])

        idx = ["Pending", "In Progress", "Completed"].index(vals[4]) if vals[4] in ["Pending", "In Progress", "Completed"] else 0
        self.combo_status.current(idx)

        self.text_notes.delete("1.0", "end"); self.text_notes.insert("1.0", vals[5])

    def clear_form(self):
        self.selected_id = None
        self.entry_class.delete(0, "end")
        self.entry_date.delete(0, "end"); self.entry_date.insert(0, str(date.today()))
        self.entry_topic.delete(0, "end")
        self.combo_status.current(0)
        self.text_notes.delete("1.0", "end")
        for item in self.tree.selection():
            self.tree.selection_remove(item)


if __name__ == "__main__":
    root = tk.Tk()
    app = ClassTrackerApp(root)
    root.mainloop()