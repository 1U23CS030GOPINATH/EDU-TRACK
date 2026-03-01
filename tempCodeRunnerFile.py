import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import pymongo
from bson.objectid import ObjectId
import traceback
import base64
import os
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
import io

# Database connection parameters
MONGO_URI = "mongodb+srv://gopi:gobi@cluster0.cwonqfl.mongodb.net/student_db"
DB_NAME = "student_db"
COL_STUDENTS = "assignments"
COL_TEACHERS = "teachers"
COL_ADMINS = "admins"
COL_STUDENT_USERS = "student_users"

# Ultra Premium Theme Configuration
COLORS = {
    "bg": "#F8FAFC",          # Soft Slate Gray
    "sidebar": "#0F172A",     # Deep Midnight Blue
    "sidebar_active": "#1E293B",
    "card": "#FFFFFF",        # Pure White
    "accent": "#0EA5E9",      # Vibrant Sky Blue
    "accent_hover": "#0284C7",# Deep Sky Blue
    "text": "#1E293B",        # Slate Dark
    "subtext": "#64748B",     # Muted Slate
    "banner": "#F1F5F9",      # Light Slate Banner
    "border": "#E2E8F0",      # Soft Border
    "success": "#10B981",     # Emerald
    "danger": "#EF4444",      # Rose
    "grad_top": "#0F172A",
    "grad_bot": "#334155"
}

def init_db():
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000, connectTimeoutMS=10000)
        db = client[DB_NAME]
        return db[COL_STUDENTS], db[COL_TEACHERS], db[COL_ADMINS], db[COL_STUDENT_USERS]
    except Exception as e:
        print("DEBUG: DB Init Error:")
        traceback.print_exc()
        messagebox.showerror("Database Error", f"Failed to connect to MongoDB:\n{e}")
        return None, None, None, None

def seed_admin(db_admins):
    if db_admins is not None:
        if db_admins.count_documents({"email": "admin@ams.com"}) == 0:
            db_admins.insert_one({"name": "Admin", "email": "admin@ams.com", "password": "admin123"})
            print("DEBUG: Seeded default admin account")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.db_col, self.db_teachers, self.db_admins, self.db_student_users = init_db()
        seed_admin(self.db_admins)
        self.logged_in_user = None
        self.user_role = None
        self.enrollment_prefills = None

        self.title("Academic Management System")
        self.geometry("1200x820")
        self.resizable(True, True)
        ctk.set_appearance_mode("Light")
        self.configure(fg_color=COLORS["bg"])

        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True)
        self.sidebar = None 
        self.show_login()

    def setup_layout(self):
        if self.sidebar: self.sidebar.destroy()
        self.content_area.pack_forget()
        self.sidebar = ctk.CTkFrame(self, width=110, corner_radius=0, fg_color=COLORS["sidebar"], border_width=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.content_area.pack(side="right", fill="both", expand=True)

        # Branding
        ctk.CTkLabel(self.sidebar, text="AMS", font=ctk.CTkFont("Inter", 18, "bold"), text_color=COLORS["accent"]).pack(pady=(40, 30))

        def create_nav_btn(text, cmd):
            btn = ctk.CTkButton(self.sidebar, text=text.upper(), font=ctk.CTkFont("Inter", 10, "bold"),
                height=50, width=80, fg_color="transparent", text_color="white", anchor="center",
                hover_color=COLORS["sidebar_active"], corner_radius=12, command=cmd)
            btn.pack(pady=8, padx=15)
            return btn

        if self.user_role == "Admin":
            create_nav_btn("Users", self.show_admin_users)
            create_nav_btn("Stats", self.show_admin_stats)
        elif self.user_role == "Teacher":
            create_nav_btn("Dash", self.show_dashboard)
            create_nav_btn("Add", self.show_entry_page)
            create_nav_btn("List", self.show_records_page)
        elif self.user_role == "Student":
            create_nav_btn("Portal", self.show_student_dashboard)
            create_nav_btn("Marks", self.show_student_results)

        create_nav_btn("Profile", self.show_profile)

        ctk.CTkButton(self.sidebar, text="LOGOUT", font=ctk.CTkFont("Inter", 10, "bold"),
                      fg_color="transparent", text_color=COLORS["danger"], hover_color=COLORS["sidebar_active"],
                      height=40, width=80, corner_radius=10, command=self.logout).pack(side="bottom", pady=40)
        
        user_info = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_info.pack(side="bottom", pady=(0, 10))
        ctk.CTkLabel(user_info, text=f"{self.user_role.upper()}", font=ctk.CTkFont("Inter", 9, "bold"), text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(user_info, text=f"{self.logged_in_user.upper()}", font=ctk.CTkFont("Inter", 10, "bold"), text_color="white").pack()

    def logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?"):
            self.logged_in_user = None
            self.user_role = None
            if self.sidebar: self.sidebar.destroy()
            self.sidebar = None
            self.content_area.pack_forget()
            self.content_area.pack(fill="both", expand=True)
            self.show_login()

    def switch_view(self, view_func):
        for widget in self.content_area.winfo_children(): widget.destroy()
        view_func(self.content_area)

    def show_profile(self): self.switch_view(self.build_profile_view)
    def build_profile_view(self, parent):
        db = self.db_admins if self.user_role == "Admin" else (self.db_teachers if self.user_role == "Teacher" else self.db_student_users)
        user_data = db.find_one({"name": self.logged_in_user}) or {}
        
        self.create_hero(parent, f"Profile: {self.logged_in_user}", "Manage your personal information and account security.", user_data.get("avatar"))
        
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=30)
        card.pack(fill="both", expand=True, padx=40, pady=(10, 40))
        
        # User Info Section
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(pady=40, padx=60, fill="x")
        
        header = ctk.CTkFrame(info_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="ACCOUNT INFORMATION", font=ctk.CTkFont("Inter", 12, "bold"), text_color=COLORS["accent"]).pack(side="left")
        
        ctk.CTkButton(header, text="📷 CHANGE PHOTO", height=35, corner_radius=10, 
                      fg_color=COLORS["sidebar"], font=ctk.CTkFont("Inter", 11, "bold"),
                      command=lambda: self.upload_avatar(db)).pack(side="right")
        
        def add_info(l, v):
            f = ctk.CTkFrame(info_frame, fg_color="transparent")
            f.pack(fill="x", pady=10)
            ctk.CTkLabel(f, text=l, font=ctk.CTkFont("Inter", 11, "bold"), text_color=COLORS["subtext"]).pack(side="left")
            ctk.CTkLabel(f, text=str(v), font=ctk.CTkFont("Inter", 12, "bold")).pack(side="right")

        add_info("Display Name", user_data.get("name", "N/A"))
        add_info("Email/ID", user_data.get("email", "N/A"))
        add_info("System Role", self.user_role)
        
        ctk.CTkFrame(card, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=60, pady=20)
        
        # Password Update Section
        ctk.CTkLabel(card, text="SECURITY SETTINGS", font=ctk.CTkFont("Inter", 12, "bold"), text_color=COLORS["accent"]).pack(anchor="w", padx=60)
        
        self.new_pass = ctk.CTkEntry(card, placeholder_text="Enter new password", show="*", height=50, width=320, corner_radius=15)
        self.new_pass.pack(pady=20)
        
        def update_pw():
            pw = self.new_pass.get().strip()
            if not pw: return messagebox.showwarning("Input Error", "Please enter a new password")
            db.update_one({"name": self.logged_in_user}, {"$set": {"password": pw}})
            messagebox.showinfo("Success", "Password updated successfully!")
            self.new_pass.delete(0, 'end')

        ctk.CTkButton(card, text="UPDATE PASSWORD", height=50, width=240, corner_radius=15, 
                      fg_color=COLORS["sidebar"], font=ctk.CTkFont("Inter", 12, "bold"), command=update_pw).pack(pady=10)

    def upload_avatar(self, db):
        f_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg")])
        if not f_path: return
        
        try:
            with open(f_path, "rb") as f:
                blob = base64.b64encode(f.read()).decode('utf-8')
            db.update_one({"name": self.logged_in_user}, {"$set": {"avatar": blob}})
            messagebox.showinfo("Success", "Profile photo updated!")
            self.show_profile()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload photo: {e}")

    def show_records_page(self): self.switch_view(self.build_records_page)
    def show_entry_page(self): self.switch_view(self.build_entry_page)
    def show_admin_users(self): self.switch_view(self.build_user_mgmt)

    def show_login(self): self.switch_view(self.build_login_view)
    def build_login_view(self, parent):
        card = ctk.CTkFrame(parent, width=420, height=540, fg_color=COLORS["card"], corner_radius=30)
        card.place(relx=0.5, rely=0.5, anchor="center"); card.pack_propagate(False)
        ctk.CTkLabel(card, text="🎓", font=ctk.CTkFont(size=64)).pack(pady=(50, 10))
        ctk.CTkLabel(card, text="ACADEMIC PORTAL", font=ctk.CTkFont("Inter", 26, "bold"), text_color=COLORS["text"]).pack(pady=(0, 40))
        
        self.login_user = ctk.CTkEntry(card, placeholder_text="Username / Email", height=55, width=320, corner_radius=15, border_width=1)
        self.login_user.pack(pady=10)
        self.login_pass = ctk.CTkEntry(card, placeholder_text="Password", show="*", height=55, width=320, corner_radius=15, border_width=1)
        self.login_pass.pack(pady=10)
        
        ctk.CTkButton(card, text="SECURE LOGIN", height=55, width=320, corner_radius=15, font=ctk.CTkFont("Inter", 14, "bold"), 
                      fg_color=COLORS["sidebar"], command=self.handle_login).pack(pady=(35, 20))
        
        link_frame = ctk.CTkFrame(card, fg_color="transparent")
        link_frame.pack()
        ctk.CTkLabel(link_frame, text="Institutional access?", font=ctk.CTkFont("Inter", 12), text_color=COLORS["subtext"]).pack(side="left")
        ctk.CTkButton(link_frame, text="Admin Signup", font=ctk.CTkFont("Inter", 12, "bold"), text_color=COLORS["accent"], 
                      fg_color="transparent", width=50, hover=False, command=self.show_register).pack(side="left")

    def show_register(self): self.switch_view(self.build_register_view)

    def build_register_view(self, parent):
        card = ctk.CTkFrame(parent, width=420, height=580, fg_color=COLORS["card"], corner_radius=30)
        card.place(relx=0.5, rely=0.5, anchor="center"); card.pack_propagate(False)
        
        ctk.CTkLabel(card, text="�️", font=ctk.CTkFont(size=64)).pack(pady=(40, 5))
        ctk.CTkLabel(card, text="ADMIN SIGNUP", font=ctk.CTkFont("Inter", 26, "bold"), text_color=COLORS["text"]).pack()
        ctk.CTkLabel(card, text="SECURE ADMINISTRATOR REGISTRATION", font=ctk.CTkFont("Inter", 11, "bold"), text_color=COLORS["accent"]).pack(pady=(5, 30))

        self.reg_n = ctk.CTkEntry(card, placeholder_text="Full Name", height=55, width=320, corner_radius=15, border_width=1); self.reg_n.pack(pady=10)
        self.reg_e = ctk.CTkEntry(card, placeholder_text="Email/Username", height=55, width=320, corner_radius=15, border_width=1); self.reg_e.pack(pady=10)
        self.reg_p = ctk.CTkEntry(card, placeholder_text="Create Password", show="*", height=55, width=320, corner_radius=15, border_width=1); self.reg_p.pack(pady=10)
        
        ctk.CTkButton(card, text="REGISTER NOW", height=55, width=320, corner_radius=15, font=ctk.CTkFont("Inter", 14, "bold"),
                      fg_color=COLORS["sidebar"], command=self.handle_register).pack(pady=(25, 10))
        ctk.CTkButton(card, text="Back to Login", fg_color="transparent", text_color=COLORS["subtext"], 
                      font=ctk.CTkFont("Inter", 12), command=self.show_login).pack()

    def handle_register(self):
        n, e, p = self.reg_n.get().strip(), self.reg_e.get().strip(), self.reg_p.get().strip()
        if not n or not e or not p: return messagebox.showwarning("Error", "Fill all fields")
        
        db = self.db_admins
        if db.find_one({"email": e}): return messagebox.showerror("Error", "Admin already exists")
        db.insert_one({"name": n, "email": e, "password": p})
        messagebox.showinfo("Success", "Admin Account Created!"); self.show_login()

    def handle_login(self):
        user, pw = self.login_user.get().strip(), self.login_pass.get().strip()
        print(f"DEBUG: Login attempt for user: {user}")
        if not user or not pw: return messagebox.showwarning("Auth Error", "Fill all fields")
        
        roles_config = [("Admin", self.db_admins), ("Teacher", self.db_teachers), ("Student", self.db_student_users)]
        
        for role, db in roles_config:
            if db is None: 
                print(f"DEBUG: DB for role {role} is None")
                continue
            
            print(f"DEBUG: Checking role: {role}")
            try:
                account = db.find_one({"email": user, "password": pw}) or db.find_one({"name": user, "password": pw})
                if account:
                    print(f"DEBUG: Login successful for role: {role}")
                    self.logged_in_user, self.user_role = account["name"], role
                    self.setup_layout()
                    if role == "Admin": self.show_admin_dashboard()
                    elif role == "Teacher": self.show_dashboard()
                    else: self.show_student_dashboard()
                    return
            except Exception as e:
                print(f"DEBUG: Error checking {role}:")
                traceback.print_exc()
        
        print("DEBUG: No account found")
        messagebox.showerror("Auth Error", "Invalid credentials")

    # TEACHER VIEWS
    def show_dashboard(self): self.switch_view(self.build_dashboard_view)
    # DASHBOARD BUILDERS
    def create_hero(self, parent, title, subtitle, img_data=None):
        hero = ctk.CTkFrame(parent, fg_color=COLORS["banner"], corner_radius=30, height=180)
        hero.pack(fill="x", padx=40, pady=(40, 20)); hero.pack_propagate(False)
        
        # Image on the left if present
        if img_data:
            try:
                raw = base64.b64decode(img_data)
                img = Image.open(io.BytesIO(raw))
                # Professional circular mask logic
                w, h = img.size
                s = min(w, h)
                img = img.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2)).resize((100, 100)).convert("RGBA")
                
                mask = Image.new('L', (100, 100), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 100, 100), fill=255)
                
                output = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
                output.paste(img, (0, 0), mask)
                
                self.hero_avatar = ctk.CTkImage(output, size=(100, 100))
                ctk.CTkLabel(hero, image=self.hero_avatar, text="").pack(side="left", padx=(40, 0), pady=40)
            except Exception as e: print(f"Hero Image Error: {e}")

        text_f = ctk.CTkFrame(hero, fg_color="transparent")
        text_f.pack(side="left", padx=40, pady=45)
        ctk.CTkLabel(text_f, text=title, font=ctk.CTkFont("Inter", 32, "bold"), text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(text_f, text=subtitle, font=ctk.CTkFont("Inter", 14), text_color=COLORS["subtext"]).pack(anchor="w")
        return hero

    def create_stat_card(self, parent, label, value, color):
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=24, height=160, width=200)
        card.pack(side="left", padx=10); card.pack_propagate(False)
        ctk.CTkLabel(card, text=label.upper(), font=ctk.CTkFont("Inter", 11, "bold"), text_color=COLORS["subtext"]).pack(pady=(25, 5))
        ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont("Inter", 42, "bold"), text_color=COLORS["text"]).pack()
        bar = ctk.CTkFrame(card, height=4, width=40, fg_color=color, corner_radius=2)
        bar.pack(pady=12)

    def build_dashboard_view(self, parent):
        t, c, p = self.db_col.count_documents({}), self.db_col.count_documents({"status": "Completed"}), self.db_col.count_documents({"status": "Pending"})
        avg = 0
        res = list(self.db_col.aggregate([{"$group": {"_id": None, "avg": {"$avg": "$marks"}}}]))
        if res: avg = round(res[0]["avg"], 1)

        self.create_hero(parent, f"Hello, {self.logged_in_user}", "Welcome back to your academic overview.")
        
        stats_row = ctk.CTkFrame(parent, fg_color="transparent")
        stats_row.pack(fill="x", padx=30, pady=20)
        
        self.create_stat_card(stats_row, "Assignments", t, COLORS["accent"])
        self.create_stat_card(stats_row, "Success Rate", f"{round((c/t*100) if t else 0)}%", COLORS["success"])
        self.create_stat_card(stats_row, "Pending", p, COLORS["danger"])

        if self.user_role == "Teacher":
            self.build_submissions_list(parent)
            self.build_teacher_student_list(parent)

    def build_submissions_list(self, parent):
        ctk.CTkLabel(parent, text="PENDING SUBMISSIONS", font=ctk.CTkFont("Inter", 12, "bold"), text_color=COLORS["danger"]).pack(anchor="w", padx=40, pady=(20, 10))
        
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=30)
        card.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        self.sub_tree = ttk.Treeview(card, columns=("n", "s", "d"), show="headings", height=5)
        for c, h in zip(("n", "s", "d"), ("STUDENT", "SUBJECT", "DEPT")):
            self.sub_tree.heading(c, text=h); self.sub_tree.column(c, anchor="center")
        self.sub_tree.pack(fill="both", expand=True, padx=40, pady=(30, 10))
        
        # Find submissions for this teacher's assigned students
        my_students = [s["name"] for s in self.db_student_users.find({"assigned_teacher": self.logged_in_user})]
        subs = list(self.db_col.find({"status": "Under Review", "student_name": {"$in": my_students}}))
        
        for s in subs:
            self.sub_tree.insert("", "end", values=(s.get("student_name"), s.get("subject"), s.get("department")), iid=str(s['_id']))
        
        if not subs:
            self.sub_tree.insert("", "end", values=("No pending reviews", "-", "-"))
        else:
            ctk.CTkButton(card, text="VERIFY & GRADE", height=40, width=180, corner_radius=12,
                          fg_color=COLORS["sidebar"], font=ctk.CTkFont("Inter", 11, "bold"),
                          command=self.verify_submission).pack(pady=15)

    def verify_submission(self):
        sel = self.sub_tree.selection()
        if not sel: return messagebox.showwarning("Select", "Choose a submission to verify")
        sid = sel[0]
        rec = self.db_col.find_one({"_id": ObjectId(sid)})
        if not rec: return

        # Modal for review
        m = ctk.CTkToplevel(self); m.title("VERIFY SUBMISSION"); m.geometry("500x400"); m.grab_set()
        card = ctk.CTkFrame(m, fg_color=COLORS["card"], corner_radius=30); card.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(card, text="Verification Bridge", font=ctk.CTkFont("Inter", 20, "bold")).pack(pady=20)
        ctk.CTkLabel(card, text=f"Student: {rec['student_name']}\nSubject: {rec['subject']}", font=ctk.CTkFont("Inter", 12)).pack(pady=10)
        
        def open_pdf():
            template_path = "temp_view.pdf"
            with open(template_path, "wb") as f:
                f.write(base64.b64decode(rec['pdf_data']))
            import os
            os.startfile(template_path)

        ctk.CTkButton(card, text="👁️ VIEW ATTACHED PDF", height=50, width=300, corner_radius=15, 
                      fg_color=COLORS["sidebar"], font=ctk.CTkFont("Inter", 12, "bold"), command=open_pdf).pack(pady=10)
        
        marks_var = ctk.StringVar()
        ctk.CTkEntry(card, placeholder_text="ENTER MARKS", height=50, width=300, corner_radius=15, textvariable=marks_var).pack(pady=10)
        
        def finalize():
            try:
                m_val = int(marks_var.get())
                self.db_col.update_one({"_id": ObjectId(sid)}, {"$set": {"marks": m_val, "status": "Completed"}})
                messagebox.showinfo("Success", "Marks awarded and verified!")
                m.destroy(); self.show_dashboard()
            except: messagebox.showwarning("Error", "Enter valid marks")

        ctk.CTkButton(card, text="AWARD MARKS & VERIFY", height=55, width=300, corner_radius=15, 
                      fg_color=COLORS["success"], font=ctk.CTkFont("Inter", 13, "bold"), command=finalize).pack(pady=20)

    def build_teacher_student_list(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(20, 10))
        
        ctk.CTkLabel(header, text="MY ASSIGNED STUDENTS", font=ctk.CTkFont("Inter", 12, "bold"), text_color=COLORS["accent"]).pack(side="left")
        
        ctk.CTkButton(header, text="+ ADD STUDENT ACCOUNT", height=35, corner_radius=10, 
                      fg_color=COLORS["sidebar"], font=ctk.CTkFont("Inter", 11, "bold"),
                      command=lambda: self.open_user_modal("Student")).pack(side="right", padx=10)
        
        ctk.CTkButton(header, text="EDIT STUDENT", height=35, corner_radius=10, 
                      fg_color=COLORS["success"], font=ctk.CTkFont("Inter", 11, "bold"),
                      command=self.edit_teacher_user).pack(side="right")
        
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=30)
        card.pack(fill="both", expand=True, padx=30, pady=(0, 40))
        
        self.teacher_tree = ttk.Treeview(card, columns=("n", "e"), show="headings", height=8)
        for c, h in zip(("n", "e"), ("STUDENT NAME", "USER ID / EMAIL")):
            self.teacher_tree.heading(c, text=h); self.teacher_tree.column(c, anchor="center")
        self.teacher_tree.pack(fill="both", expand=True, padx=40, pady=30)
        
        assigned = list(self.db_student_users.find({"assigned_teacher": self.logged_in_user}))
        for s in assigned:
            self.teacher_tree.insert("", "end", values=(s.get("name"), s.get("email")), iid=str(s['_id']))
        
        if not assigned:
            self.teacher_tree.insert("", "end", values=("No students assigned yet", "-"))

        def on_double_click(event):
            sel = self.teacher_tree.selection()
            if not sel: return
            item = self.teacher_tree.item(sel[0])
            name, reg = item["values"]
            if name == "No students assigned yet": return
            self.enrollment_prefills = {"name": name, "reg": reg}
            self.show_entry_page()

        self.teacher_tree.bind("<Double-1>", on_double_click)

    def edit_teacher_user(self):
        sel = self.teacher_tree.selection()
        if not sel: return messagebox.showwarning("Select", "Choose a student to edit")
        uid = sel[0]
        user = self.db_student_users.find_one({"_id": ObjectId(uid)})
        if not user: return

        mw = ctk.CTkToplevel(self); mw.title("EDIT STUDENT"); mw.geometry("450x550"); mw.grab_set()
        card = ctk.CTkFrame(mw, fg_color=COLORS["card"], corner_radius=30); card.pack(fill="both", expand=True, padx=30, pady=30)
        ctk.CTkLabel(card, text="Update Student Details", font=ctk.CTkFont("Inter", 20, "bold")).pack(pady=(40, 20))
        
        def add_e(p, val):
            e = ctk.CTkEntry(card, placeholder_text=p, height=50, width=300, corner_radius=15, border_width=1)
            e.pack(pady=10); e.insert(0, val); return e

        n, e = add_e("Full Name", user["name"]), add_e("Email / ID", user["email"])
        p = add_e("New Password (optional)", "")
        
        def save():
            upd = {"name": n.get(), "email": e.get()}
            if p.get().strip(): upd["password"] = p.get().strip()
            self.db_student_users.update_one({"_id": ObjectId(uid)}, {"$set": upd})
            mw.destroy(); self.show_dashboard()
            
        ctk.CTkButton(card, text="SAVE CHANGES", height=55, width=300, corner_radius=15, font=ctk.CTkFont("Inter", 13, "bold"),
                      fg_color=COLORS["sidebar"], command=save).pack(pady=30)

    def build_entry_page(self, parent):
        self.create_hero(parent, "New Enrollment", "Enroll a new student and record their academic data.")
        
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=30)
        card.pack(fill="both", expand=True, padx=40, pady=(10, 40))
        
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(padx=60, pady=60)
        
        def add_f(l, r, c, opt=None):
            f = ctk.CTkFrame(form, fg_color="transparent")
            f.grid(row=r, column=c, padx=20, pady=15)
            ctk.CTkLabel(f, text=l.upper(), font=ctk.CTkFont("Inter", 10, "bold"), text_color=COLORS["subtext"]).pack(anchor="w")
            if opt: w = ctk.CTkComboBox(f, values=opt, height=50, width=320, corner_radius=15, border_width=1)
            else: w = ctk.CTkEntry(f, height=50, width=320, corner_radius=15, border_width=1)
            w.pack(pady=5); return w

        self.en_name, self.en_reg = add_f("FullName", 0, 0), add_f("RegisterID", 0, 1)
        self.en_dept = add_f("Department", 1, 0, ["CS", "IT", "Engineering", "Arts"])
        self.en_sub = add_f("Subject", 1, 1, ["Python", "Java", "Math", "Physics"])
        self.en_marks = add_f("Marks", 2, 0)

        if self.enrollment_prefills:
            self.en_name.insert(0, self.enrollment_prefills["name"])
            self.en_reg.insert(0, self.enrollment_prefills["reg"])
            self.enrollment_prefills = None
        
        self.en_stat = ctk.StringVar(value="Completed")
        rb_frame = ctk.CTkFrame(form, fg_color="transparent")
        rb_frame.grid(row=2, column=1, pady=15)
        ctk.CTkRadioButton(rb_frame, text="Pass", variable=self.en_stat, value="Completed", font=ctk.CTkFont("Inter", 12)).pack(side="left", padx=20)
        ctk.CTkRadioButton(rb_frame, text="Fail", variable=self.en_stat, value="Pending", font=ctk.CTkFont("Inter", 12)).pack(side="left")

        ctk.CTkButton(card, text="SAVE RECORD", height=55, width=240, corner_radius=15, font=ctk.CTkFont("Inter", 14, "bold"), 
                      fg_color=COLORS["sidebar"], command=self.save_record).pack(pady=(0, 40))

    def save_record(self):
        try:
            name, reg = self.en_name.get().strip(), self.en_reg.get().strip()
            dept, sub = self.en_dept.get(), self.en_sub.get()
            marks = int(self.en_marks.get() or 0)
            
            if not name or not reg: return messagebox.showwarning("Error", "Name and ID are required")
            
            d = {
                "student_name": name, 
                "register_no": reg, 
                "department": dept, 
                "subject": sub, 
                "marks": marks, 
                "status": self.en_stat.get(), 
                "recorded_by": self.logged_in_user
            }
            self.db_col.insert_one(d)
            messagebox.showinfo("Success", "Student record saved successfully!")
            self.show_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save record: {e}")

    def build_records_page(self, parent):
        self.create_hero(parent, "Directory", "Search, edit, and manage student performance records.")
        
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=30)
        card.pack(fill="both", expand=True, padx=40, pady=(10, 40))
        
        search_row = ctk.CTkFrame(card, fg_color="transparent")
        search_row.pack(fill="x", padx=40, pady=(40, 20))
        
        self.search_entry = ctk.CTkEntry(search_row, height=50, placeholder_text="Search by name, ID or Dept...", 
                                         corner_radius=15, border_width=1)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 15))
        
        ctk.CTkButton(search_row, text="SEARCH", width=120, height=50, corner_radius=15, fg_color=COLORS["accent"], 
                      font=ctk.CTkFont("Inter", 12, "bold"), command=self.search_records).pack(side="left", padx=(0, 10))
        ctk.CTkButton(search_row, text="RESET", width=100, height=50, corner_radius=15, fg_color=COLORS["banner"], 
                      text_color=COLORS["text"], font=ctk.CTkFont("Inter", 12, "bold"), command=self.clear_search).pack(side="left")

        self.tree = ttk.Treeview(card, columns=("n", "r", "d", "s", "m", "st", "mn"), show="headings")
        for c, h in zip(("n", "r", "d", "s", "m", "st", "mn"), ("NAME", "REG ID", "DEPT", "SUBJ", "MARKS", "STAT", "MENTOR")):
            self.tree.heading(c, text=h); self.tree.column(c, width=130, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(pady=(0, 40), padx=40, fill="x")
        ctk.CTkButton(actions, text="DELETE RECORD", fg_color=COLORS["danger"], corner_radius=12,
                      font=ctk.CTkFont("Inter", 11, "bold"), command=self.delete_record).pack(side="left")
        
        ctk.CTkButton(actions, text="VIEW SUBMISSION", fg_color=COLORS["sidebar"], corner_radius=12,
                      font=ctk.CTkFont("Inter", 11, "bold"), command=self.view_directory_pdf).pack(side="left", padx=10)

        ctk.CTkButton(actions, text="EDIT DETAILS", fg_color=COLORS["success"], corner_radius=12,
                      font=ctk.CTkFont("Inter", 11, "bold"), command=self.edit_record).pack(side="right")
        self.refresh_table()

    def delete_record(self):
        s = self.tree.focus()
        if s: 
            if messagebox.askyesno("Confirm", "Delete this record?"):
                self.db_col.delete_one({"_id": ObjectId(s)})
                self.refresh_table()

    def search_records(self):
        v = self.search_entry.get().strip()
        if not v: self.refresh_table(); return
        q = {"$or": [{"student_name": {"$regex": v, "$options": "i"}}, {"register_no": {"$regex": v, "$options": "i"}}, {"department": {"$regex": v, "$options": "i"}}]}
        self.refresh_table(q)

    def clear_search(self):
        self.search_entry.delete(0, 'end'); self.refresh_table()

    def edit_record(self):
        selected = self.tree.focus()
        if not selected: return messagebox.showwarning("Select", "Choose a record")
        doc = self.db_col.find_one({"_id": ObjectId(selected)})
        if not doc: return

        edit_win = ctk.CTkToplevel(self); edit_win.title("Update Record"); edit_win.geometry("500x700"); edit_win.grab_set()
        ctk.CTkLabel(edit_win, text="EDIT STUDENT DATA", font=ctk.CTkFont("Inter", 20, "bold")).pack(pady=20)
        
        scroll = ctk.CTkScrollableFrame(edit_win, fg_color="transparent"); scroll.pack(fill="both", expand=True, padx=30)
        
        def add_e(l, val):
            ctk.CTkLabel(scroll, text=l.upper(), font=ctk.CTkFont("Inter", 10, "bold"), text_color=COLORS["subtext"]).pack(anchor="w", pady=(10, 0))
            e = ctk.CTkEntry(scroll, height=45); e.pack(fill="x", pady=5); e.insert(0, str(val)); return e

        en_n, en_r = add_e("NAME", doc.get("student_name", "")), add_e("REG ID", doc.get("register_no", ""))
        en_m = add_e("MARKS", doc.get("marks", 0))
        
        def save():
            try:
                self.db_col.update_one({"_id": ObjectId(selected)}, {"$set": {"student_name": en_n.get(), "register_no": en_r.get(), "marks": int(en_m.get())}})
                messagebox.showinfo("Success", "Updated!"); edit_win.destroy(); self.refresh_table()
            except Exception as e: messagebox.showerror("Error", f"Failed: {e}")

        ctk.CTkButton(edit_win, text="SAVE UPDATES", height=50, fg_color=COLORS["sidebar"], command=save).pack(pady=30, padx=50, fill="x")

    def view_directory_pdf(self):
        s = self.tree.focus()
        if not s: return messagebox.showwarning("Select", "Choose a record")
        rec = self.db_col.find_one({"_id": ObjectId(s)})
        if not rec or not rec.get("pdf_data"): return messagebox.showinfo("No PDF", "No submission file found for this record")

        try:
            temp_path = "directory_temp.pdf"
            with open(temp_path, "wb") as f:
                f.write(base64.b64decode(rec['pdf_data']))
            os.startfile(temp_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF: {e}")

    def refresh_table(self, query=None):
        for i in self.tree.get_children(): self.tree.delete(i)
        docs = self.db_col.find(query) if query else self.db_col.find()
        for d in docs:
            stu = self.db_student_users.find_one({"name": d.get("student_name")})
            mentor = stu.get("assigned_teacher", "N/A") if stu else "N/A"
            vals = (d.get("student_name"), d.get("register_no"), d.get("department"), 
                    d.get("subject"), d.get("marks"), d.get("status"), mentor)
            self.tree.insert("", "end", values=vals, iid=str(d["_id"]))

    # ADMIN VIEWS
    def show_admin_dashboard(self): self.switch_view(self.build_admin_dashboard)
    def build_admin_dashboard(self, parent):
        t, s, r = self.db_teachers.count_documents({}), self.db_student_users.count_documents({}), self.db_col.count_documents({})
        self.create_hero(parent, "Control Center", "Manage faculty, students, and institutional data.")
        
        stats_row = ctk.CTkFrame(parent, fg_color="transparent")
        stats_row.pack(fill="x", padx=30, pady=20)
        
        self.create_stat_card(stats_row, "Teachers", t, COLORS["accent"])
        self.create_stat_card(stats_row, "Students", r, COLORS["success"])
        self.create_stat_card(stats_row, "Accounts", s, COLORS["banner"])

    def build_user_mgmt(self, parent):
        self.create_hero(parent, "User Management", "Create and manage accounts for faculty and students.")
        
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=30)
        card.pack(fill="both", expand=True, padx=40, pady=(10, 40))
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(40, 0))
        ctk.CTkButton(header, text="+ ADD TEACHER", corner_radius=12, fg_color=COLORS["sidebar"], 
                      command=lambda: self.open_user_modal("Teacher")).pack(side="left", padx=5)
        ctk.CTkButton(header, text="+ ADD STUDENT", corner_radius=12, fg_color=COLORS["accent"], 
                      command=lambda: self.open_user_modal("Student")).pack(side="left")
        
        self.u_tabs = ctk.CTkTabview(card, fg_color="transparent", segmented_button_fg_color=COLORS["bg"],
                                     segmented_button_selected_color=COLORS["accent"],
                                     segmented_button_selected_hover_color=COLORS["accent_hover"])
        self.u_tabs.pack(fill="both", expand=True, padx=40, pady=(10, 20))
        
        tab_f = self.u_tabs.add("Faculty")
        tab_s = self.u_tabs.add("Students")

        def create_u_tree(p):
            t = ttk.Treeview(p, columns=("n", "e"), show="headings")
            for c, col in zip(("n", "e"), ("NAME", "USER ID / EMAIL")):
                t.heading(c, text=col); t.column(c, anchor="center")
            t.pack(fill="both", expand=True, padx=10, pady=10)
            return t

        self.faculty_tree = create_u_tree(tab_f)
        self.student_tree = create_u_tree(tab_s)

        u_actions = ctk.CTkFrame(card, fg_color="transparent")
        u_actions.pack(fill="x", padx=40, pady=(0, 40))
        ctk.CTkButton(u_actions, text="DELETE USER", fg_color=COLORS["danger"], corner_radius=12,
                      font=ctk.CTkFont("Inter", 11, "bold"), command=self.delete_admin_user).pack(side="left")
        ctk.CTkButton(u_actions, text="EDIT USER", fg_color=COLORS["success"], corner_radius=12,
                      font=ctk.CTkFont("Inter", 11, "bold"), command=self.edit_admin_user).pack(side="right")
        self.refresh_users()

    def refresh_users(self):
        for i in self.faculty_tree.get_children(): self.faculty_tree.delete(i)
        for i in self.student_tree.get_children(): self.student_tree.delete(i)
        for t in self.db_teachers.find(): self.faculty_tree.insert("", "end", values=(t["name"], t["email"]), iid=str(t['_id']))
        for s in self.db_student_users.find(): 
            at = s.get("assigned_teacher", "None")
            self.student_tree.insert("", "end", values=(s["name"], f"{s['email']} (Mentor: {at})"), iid=str(s['_id']))

    def get_active_user_context(self):
        tab = self.u_tabs.get()
        tree = self.faculty_tree if tab == "Faculty" else self.student_tree
        db = self.db_teachers if tab == "Faculty" else self.db_student_users
        sel = tree.selection()
        return tab, tree, db, (sel[0] if sel else None)

    def delete_admin_user(self):
        tab, tree, db, uid = self.get_active_user_context()
        if not uid: return messagebox.showwarning("Select", f"Please select a user from {tab}")
        if not messagebox.askyesno("Confirm", f"Delete this {tab[:-1].lower()} account permanently?"): return
        
        try:
            db.delete_one({"_id": ObjectId(uid)})
            messagebox.showinfo("Deleted", "User removed successfully")
            self.refresh_users()
        except Exception as e: messagebox.showerror("Error", f"Failed to delete: {e}")

    def edit_admin_user(self):
        tab, tree, db, uid = self.get_active_user_context()
        if not uid: return messagebox.showwarning("Select", f"Please select a user from {tab}")
        user = db.find_one({"_id": ObjectId(uid)})
        if not user: return

        mw = ctk.CTkToplevel(self); mw.title(f"EDIT {tab.upper()}"); mw.geometry("450x550"); mw.grab_set()
        card = ctk.CTkFrame(mw, fg_color=COLORS["card"], corner_radius=30); card.pack(fill="both", expand=True, padx=30, pady=30)
        ctk.CTkLabel(card, text="Update Details", font=ctk.CTkFont("Inter", 20, "bold")).pack(pady=(40, 20))
        
        def add_e(p, val):
            e = ctk.CTkEntry(card, placeholder_text=p, height=50, width=300, corner_radius=15, border_width=1)
            e.pack(pady=10); e.insert(0, val); return e

        n, e = add_e("Full Name", user["name"]), add_e("Email / ID", user["email"])
        p = add_e("New Password (optional)", "")
        
        t_sel = None
        if tab == "Students":
            ctk.CTkLabel(card, text="ASSIGN TEACHER", font=ctk.CTkFont("Inter", 10, "bold"), text_color=COLORS["subtext"]).pack(pady=(10, 0))
            teachers = ["None"] + [t["name"] for t in self.db_teachers.find()]
            t_sel = ctk.CTkComboBox(card, values=teachers, height=50, width=300, corner_radius=15)
            t_sel.pack(pady=10)
            if user.get("assigned_teacher"): t_sel.set(user["assigned_teacher"])
        
        def save():
            upd = {"name": n.get(), "email": e.get()}
            if p.get().strip(): upd["password"] = p.get().strip()
            if t_sel: upd["assigned_teacher"] = t_sel.get()
            db.update_one({"_id": ObjectId(uid)}, {"$set": upd})
            mw.destroy(); self.refresh_users()
            
        ctk.CTkButton(card, text="SAVE CHANGES", height=55, width=300, corner_radius=15, font=ctk.CTkFont("Inter", 13, "bold"),
                      fg_color=COLORS["sidebar"], command=save).pack(pady=30)

    def open_user_modal(self, role):
        m = ctk.CTkToplevel(self); m.title(f"NEW {role.upper()}"); m.geometry("450x550"); m.grab_set()
        m.configure(fg_color=COLORS["bg"])
        
        card = ctk.CTkFrame(m, fg_color=COLORS["card"], corner_radius=30)
        card.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(card, text="Create Account", font=ctk.CTkFont("Inter", 20, "bold")).pack(pady=(40, 10))
        ctk.CTkLabel(card, text=f"Adding a new {role.lower()} to the system.", font=ctk.CTkFont("Inter", 12), text_color=COLORS["subtext"]).pack(pady=(0, 30))
        
        def add_m(p):
            e = ctk.CTkEntry(card, placeholder_text=p, height=50, width=300, corner_radius=15, border_width=1)
            e.pack(pady=10); return e

        n, e, p = add_m("Full Name"), add_m("Email / Username"), add_m("Password")
        p.configure(show="*")
        
        t_sel = None
        if role == "Student":
            if self.user_role == "Admin":
                ctk.CTkLabel(card, text="ASSIGN TEACHER", font=ctk.CTkFont("Inter", 10, "bold"), text_color=COLORS["subtext"]).pack(pady=(10, 0))
                teachers = ["None"] + [t["name"] for t in self.db_teachers.find()]
                t_sel = ctk.CTkComboBox(card, values=teachers, height=50, width=300, corner_radius=15)
                t_sel.pack(pady=10)
            else:
                # Teachers auto-assign themselves
                ctk.CTkLabel(card, text=f"ASSIGNED TO: {self.logged_in_user}", font=ctk.CTkFont("Inter", 11, "bold"), text_color=COLORS["success"]).pack(pady=10)

        def save():
            db = self.db_teachers if role == "Teacher" else self.db_student_users
            d = {"name": n.get(), "email": e.get(), "password": p.get()}
            
            if role == "Student":
                if self.user_role == "Teacher":
                    d["assigned_teacher"] = self.logged_in_user
                elif t_sel:
                    d["assigned_teacher"] = t_sel.get()
            
            db.insert_one(d)
            m.destroy(); self.refresh_users() if self.user_role == "Admin" else self.show_dashboard()
            
        ctk.CTkButton(card, text=f"REGISTER {role.upper()}", height=55, width=300, corner_radius=15, 
                      font=ctk.CTkFont("Inter", 13, "bold"), fg_color=COLORS["sidebar"], command=save).pack(pady=30)

    def show_admin_stats(self): self.show_admin_dashboard()

    # STUDENT VIEWS
    def show_student_dashboard(self): self.switch_view(self.build_student_dash)
    def build_student_dash(self, parent):
        recs = list(self.db_col.find({"student_name": self.logged_in_user}))
        avg = round(sum(r.get('marks', 0) for r in recs) / len(recs), 1) if recs else 0
        self.create_hero(parent, f"Hi, {self.logged_in_user}", "View your academic progress and course results.")
        
        stats_row = ctk.CTkFrame(parent, fg_color="transparent")
        stats_row.pack(fill="x", padx=30, pady=20)
        
        self.create_stat_card(stats_row, "Courses", len(recs), COLORS["accent"])
        self.create_stat_card(stats_row, "Average Score", f"{avg}%", COLORS["success"])
        self.create_stat_card(stats_row, "Status", "ACTIVE", COLORS["banner"])

    def upload_assignment(self):
        sel = self.s_tree.selection()
        if not sel: return messagebox.showwarning("Select", "Choose a subject record to upload PDF")
        rid = sel[0]
        rec = self.db_col.find_one({"_id": ObjectId(rid)})
        if not rec: return

        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not file_path: return
        
        try:
            with open(file_path, "rb") as f:
                pdf_blob = base64.b64encode(f.read()).decode('utf-8')
            
            self.db_col.update_one({"_id": ObjectId(rid)}, {"$set": {"pdf_data": pdf_blob, "status": "Under Review"}})
            messagebox.showinfo("Success", f"Assignment for {rec['subject']} uploaded successfully!")
            self.show_student_results()
        except Exception as e:
            messagebox.showerror("Error", f"Upload failed: {e}")

    def show_student_results(self): self.switch_view(self.build_student_results)
    def build_student_results(self, parent):
        self.create_hero(parent, "Academic Results", "Detailed breakdown of your completed courses and marks.")
        
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=30)
        card.pack(fill="both", expand=True, padx=40, pady=(10, 40))
        
        recs = list(self.db_col.find({"student_name": self.logged_in_user}))
        
        self.s_tree = ttk.Treeview(card, columns=("s", "d", "m", "st"), show="headings")
        for c, h in zip(("s", "d", "m", "st"), ("SUBJECT", "DEPT", "MARKS", "STATUS")):
            self.s_tree.heading(c, text=h); self.s_tree.column(c, anchor="center")
        
        for r in recs:
            self.s_tree.insert("", "end", values=(r.get("subject"), r.get("department"), r.get("marks"), r.get("status")), iid=str(r['_id']))
        
        self.s_tree.pack(fill="both", expand=True, padx=40, pady=(40, 10))

        ctk.CTkButton(card, text="↑ UPLOAD PDF FOR SELECTED", height=45, width=300, corner_radius=12, 
                      fg_color=COLORS["sidebar"], font=ctk.CTkFont("Inter", 12, "bold"),
                      command=self.upload_assignment).pack(pady=(0, 40))

if __name__ == "__main__":
    app = App()
    app.mainloop()