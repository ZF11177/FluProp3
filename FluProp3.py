# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 16:56:47 2025

@author: Zoé
"""

import tkinter as tk
from tkinter import ttk, colorchooser
import tkinter.messagebox
from CoolProp import CoolProp
from CoolProp.Plots import PropertyPlot, StateContainer
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from tkinter import filedialog
import io
import csv
import numpy as np
import random
from matplotlib.backend_bases import MouseButton
import matplotlib.pylab as plt
import matplotlib.pyplot as plot
from matplotlib.ticker import LogLocator, LogFormatter, AutoMinorLocator
from tkinter import *
import itertools
import json
from datetime import datetime
import os
from matplotlib.ticker import FuncFormatter



# Hauptfenster erstellen
window = tk.Tk()
window.title("FluProp 3")
window.geometry("1280x800")
window.resizable(False, False)



# Haupt-Frame für die Anordnung
main_frame = tk.Frame(window)
main_frame.grid(row=0, column=0, sticky="nsew")
main_frame.columnconfigure(1, minsize=250, weight=0)

#main_frame.configure(background="red")

# Variable zum Speichern der ausgewählten Einheiten
selected_vars = {}
axis_names = {}
selected_row_values = None
mouse_event_triggered = False
cursor_annotation = None
persisted_isolines = []  # Liste mit Dicts oder Tupeln
legende_var = tk.BooleanVar()
legende_set = tk.BooleanVar()
legende_var.set(False)
legende_set.set(False)
## Variables
#Edit Isolines
isobar_var = tk.BooleanVar()
isotherm_var = tk.BooleanVar()
isochor_var = tk.BooleanVar()
isentropic_var = tk.BooleanVar()
isenthalpic_var = tk.BooleanVar()
isovapore_var = tk.BooleanVar()

# Set initial state for checkboxes
isobar_var.set(False)
isotherm_var.set(False)
isochor_var.set(False)
isentropic_var.set(False)
isenthalpic_var.set(False)
isovapore_var.set(False)


# Set number of Isolines
isobar_num = float()
isotherm_num = float()
isochor_num = float()
isentropic_num = float()
isenthalpic_num = float()
isovapore_num = float()

#für die Einstellungen
default_settings = {
    "left": 17,
    "right": 90,
    "top": 94,
    "bottom": 17
}

# Tkinter-Variablen erst nach der Erstellung des Hauptfensters initialisieren
left_var = tk.IntVar(value=default_settings["left"])
right_var = tk.IntVar(value=default_settings["right"])
top_var = tk.IntVar(value=default_settings["top"])
bottom_var = tk.IntVar(value=default_settings["bottom"])


isolines = ["Isobare", "Isotherme", "Isochore", "Isentrope", "Isenthalpe", "Isovapore", "Siedelinie", "Taulinie"]
data = ["Daten", "ausgewählte Daten", "Kritischer Punkt", "Tripelpunkt"]

farben_iso = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff", "#aa00ff", "#00ffaa"]
farben_data = ["#ff0000", "#00ff00", "#0000ff", "#ffff00"]

linienstile = ["-", "--", "-."]
dotstyle = ["o", "O", "-", "*","x", "+", "-", ".", "^"]

style_comboboxes = []
kreis_canvas_list = []
kreis_canvas_data_list = []
anzahl_comboboxes = []
dicke_comboboxes = []




# Variable für das Canvas (wird später überschrieben)
canvas = None

def load_subplot_settings():
    global isoline_frame, data_frame
    try:
        with open('subplot_settings.json', 'r') as file:
            settings = json.load(file)

        # Subplot-Ränder
        left_var.set(settings.get("left", 17))
        right_var.set(settings.get("right", 90))
        top_var.set(settings.get("top", 94))
        bottom_var.set(settings.get("bottom", 17))

        # Isolines
        for i, iso in enumerate(settings.get("isolines", [])):
            if i < len(farben_iso):
                farben_iso[i] = iso.get("farbe", "#000000")
                if i < len(kreis_canvas_list):
                    kreis_canvas_list[i].itemconfig("kreis", fill=farben_iso[i])
                if i < len(style_comboboxes):
                    style_comboboxes[i].set(iso.get("stil", "-"))
                dicke = iso.get("dicke", "1") or "1"
                if i < len(isoline_frame.grid_slaves()):
                    isoline_frame.grid_slaves(row=i+4, column=3)[0].set(dicke)

                # Nur wenn vorhanden:
                if "anzahl" in iso and i < len(anzahl_comboboxes):
                    anzahl_comboboxes[i].set(iso["anzahl"])
                    print("Test erfolgreich")

        # Datenpunkte
        for i, data_s in enumerate(settings.get("data", [])):
            if i < len(farben_data):
                farben_data[i] = data_s.get("farbe", "#000000")
                if i < len(kreis_canvas_data_list):
                    kreis_canvas_data_list[i].itemconfig("kreis", fill=farben_data[i])
                if i + len(isolines) < len(style_comboboxes):
                    style_comboboxes[len(isolines)+i].set(data_s.get("marker", "o"))
                größe = data_s.get("größe", "1") or "1"
                if i + len(isolines) < len(data_frame.grid_slaves()):
                    data_frame.grid_slaves(row=i+4, column=3)[0].set(größe)

    except Exception as e:
        print("Fehler beim Laden der Einstellungen:", e)


def save_subplot_settings():
    isoline_settings = []
    print("Anzahl-Comboboxes:", len(anzahl_comboboxes))
    print("Inhalt:", [cb.get() for cb in anzahl_comboboxes])

    for i, name in enumerate(isolines):
        einstellung = {
            "name": name,
            "farbe": farben_iso[i],
            "stil": style_comboboxes[i].get(),
           # "dicke": isoline_frame.grid_slaves(row=i+4, column=3)[0].get(),
            "dicke": dicke_comboboxes[i].get(),
            "anzahl": anzahl_comboboxes[i].get() if i < len(anzahl_comboboxes) else "6"

        }

        anzahl_comboboxes[6].set(1)
        anzahl_comboboxes[7].set(1)
        isoline_settings.append(einstellung)

    # Verarbeite auch die Daten
    data_settings = []
    for i, name in enumerate(data):
        einstellung = {
            "name": name,
            "farbe": farben_data[i],
            "marker": style_comboboxes[len(isolines)+i].get(),
            "größe": data_frame.grid_slaves(row=i+4, column=3)[0].get()
            
        }
        data_settings.append(einstellung)

    settings = {
        "left": left_var.get(),
        "right": right_var.get(),
        "top": top_var.get(),
        "bottom": bottom_var.get(),
        "isolines": isoline_settings,
        "data": data_settings
    }

    # DEBUG-Ausgabe
    print("Gespeicherte Einstellungen:")
    print(json.dumps(settings, indent=4))

    try:
        with open('subplot_settings.json', 'w') as file:
            json.dump(settings, file, indent=4)
    except Exception as e:
        print("Fehler beim Speichern:", e)

    save_label = ttk.Label(main_frame, text="✔ Einstellungen wurden gespeichert")
    save_label.configure(foreground="green")
    save_label.grid(row=0, column=4, padx=(10,0), columnspan=3)
    save_label.after(3500, save_label.destroy)



def get_subplot_settings():
    # Standardwerte
    default_settings = {
        "left": 17,
        "right": 90,
        "top": 94,
        "bottom": 17,
        "isolines": [],
        "data": []
    }

    try:
        with open('subplot_settings.json', 'r') as file:
            settings = json.load(file)
            # Fallback mit Defaults, falls Felder fehlen
            return {
                "left": settings.get("left", default_settings["left"]) / 100,
                "right": settings.get("right", default_settings["right"]) / 100,
                "top": settings.get("top", default_settings["top"]) / 100,
                "bottom": settings.get("bottom", default_settings["bottom"]) / 100,
                "isolines": settings.get("isolines", default_settings["isolines"]),
                "data": settings.get("data", default_settings["data"])
            }

    except FileNotFoundError:
        # Wenn Datei fehlt, gib Defaults zurück
        return {
            "left": default_settings["left"] / 100,
            "right": default_settings["right"] / 100,
            "top": default_settings["top"] / 100,
            "bottom": default_settings["bottom"] / 100,
            "isolines": [],
            "data": []
        }

def hole_plotstil(einstellungen, name, defaults=None):
    defaults = defaults or {
        "farbe": "#000000",
        "dicke": 1.5,
        "stil": "-",
        "marker": "o",
        "größe": 5,
        "anzahl": "6",  # Füge einen Standardwert für "anzahl" hinzu
    }

    # Suche in den Isolinen
    for item in einstellungen.get("isolines", []):
        if item.get("name") == name:
            return {
                "farbe": item.get("farbe", defaults["farbe"]),
                "dicke": float(item.get("dicke", defaults["dicke"])),
                "stil": item.get("stil", defaults["stil"]),
                "marker": defaults["marker"],  # Isolinien brauchen keinen Marker
                "größe": defaults["größe"],
                "anzahl": item.get("anzahl", defaults["anzahl"]),  # Hole den Wert von "anzahl"
            }


    for item in einstellungen.get("data", []):
        if item.get("name") == name:
            größe_str = item.get("größe", str(defaults["größe"]))
            größe = int(größe_str) if größe_str.isdigit() else defaults["größe"]
            return {
                "farbe": item.get("farbe", defaults["farbe"]),
                "marker": item.get("marker", defaults["marker"]),
                "größe": größe,
                "dicke": defaults["dicke"],  # für Daten irrelevant
                "stil": defaults["stil"],
            }

    return defaults




settings = get_subplot_settings()

stil_siedelinie = hole_plotstil(settings, "Siedelinie")
stil_taulinie = hole_plotstil(settings, "Taulinie")
stil_isochore = hole_plotstil(settings, "Isochore")
stil_isotherme = hole_plotstil(settings, "Isotherme")
stil_isobare = hole_plotstil(settings, "Isobare")
stil_isentrope = hole_plotstil(settings, "Isentrope")
stil_isenthalpe = hole_plotstil(settings, "Isenthalpe")
stil_isovapore = hole_plotstil(settings, "Isovapore")
stil_krit = hole_plotstil(settings, "Kritischer Punkt")
stil_tripel = hole_plotstil(settings, "Tripelpunkt")
stil_daten = hole_plotstil(settings, "Daten")
stil_datenaus = hole_plotstil(settings, "ausgewählte Daten")
#-----------------------------------------------------------------------------------------------------
#Verlauf speichern


cache_reinstoffe = []
cache_kreisprozesse = []
history_reinstoffe = []
history_kreisprozesse = []
MAX_HISTORY = 30

HISTORY_FILE = "history_data.json"


# def append_to_history(history_list, new_row):
#     """Fügt einen neuen Eintrag in die Historie hinzu."""
#     timestamped_row =  (datetime.now().strftime("%d-%m-%Y, %H:%M"),)+ tuple(new_row) + selected_vars.get()
#     #history_list.append(timestamped_row)
#     history_list.insert(0, timestamped_row)
#     if len(history_list) > MAX_HISTORY:
#         #history_list.pop(0)
#         history_list.pop()
#     save_history_to_file()
    
def append_to_history(history_list, new_row):
    """Fügt einen neuen Eintrag in die Historie hinzu, inkl. aktueller Einheiten."""
    #einheiten_tuple = tuple(var.get() for var in selected_vars.values())
    einheiten_string = ", ".join(var.get() for var in selected_vars.values())

    #timestamped_row = (datetime.now().strftime("%d-%m-%Y, %H:%M"),) + tuple(new_row) + einheiten_tuple
    timestamped_row = (datetime.now().strftime("%d-%m-%Y, %H:%M"),) + tuple(new_row) + (einheiten_string, )
    history_list.insert(0, timestamped_row)
    if len(history_list) > MAX_HISTORY:
        history_list.pop()
    save_history_to_file()
    print(einheiten_string)
   
def append_to_cache(cache_list, new_row):
    """Fügt einen Eintrag zum Cache hinzu (ohne neuen Timestamp)."""
    cache_list.append(tuple(new_row))  # Kein Timestamp!



def update_history_treeview(treeview, history_list):#läd die Werte in die Tabelle
    """Aktualisiert die Treeview mit den Daten der Historie."""
    treeview.delete(*treeview.get_children())  # Alte Zeilen löschen
    for row in history_list:
        # Setzt den Timestamp in die erste Spalte und fügt die restlichen Werte an
        treeview.insert("", "end", values=row)

def update_cache_treeview(treeview, cache_list):
    """Zeigt Cache-Daten ohne Timestamp."""
    treeview.delete(*treeview.get_children())
    for row in cache_list:
        treeview.insert("", "end", values=row)



def save_history_to_file():
    """Speichert die Historie in einer Datei."""
    data = {
        "reinstoffe": history_reinstoffe,
        "kreisprozesse": history_kreisprozesse,
        "cache_reinstoffe": cache_reinstoffe,
        "cache_kreisprozesse": cache_kreisprozesse
    }
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    
    # print("Gespeicherte Einstellungen:")
    # print(json.dumps(data, indent=4))


def load_history_from_file():#läd Werte aus json in python in die zwei Variablen
    """Lädt die Historie aus der Datei."""
    global history_reinstoffe, history_kreisprozesse, cache_reinstoffe, cache_kreisprozesse
    
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            history_reinstoffe = [tuple(row) for row in data.get("reinstoffe", [])]
            history_kreisprozesse = [tuple(row) for row in data.get("kreisprozesse", [])]
            cache_reinstoffe = [tuple(row) for row in data.get("cache_reinstoffe", [])]
            cache_kreisprozesse = [tuple(row) for row in data.get("cache_kreisprozesse", [])]
        #print("Load erfolgreich", "cache_reinstoffe ist:", cache_reinstoffe)
        #print("Load erfolgreich", "cache_reinstoffe ist:", history_reinstoffe)
            

#Vorbereitung
#-----------------------------------------------------------------------------------------------------
#Menü erstellen
tree = None
tree2 = None

# # Funktion zum Wechseln der Ansicht
def switch_view(view_name):
        
    for widget in main_frame.winfo_children():
        if widget.winfo_exists():
            widget.destroy()
    if view_name == "Startseite":
        show_startseite()
    elif view_name == "Reinstoffe":
        
        show_reinstoffe()
    elif view_name == "Stoffgemische":
        show_stoffgemische()
    elif view_name == "Kreisprozesse":
        show_kreisprozesse()
    elif view_name == "Einstellungen":
        show_einstellungen()
    elif view_name == "Verlauf":
        show_verlauf()
    



# Menüleiste erstellen
menu_bar = tk.Menu(window)
window.config(menu=menu_bar)

# Menüoptionen
menu_bar.add_command(label="Startseite", command=lambda: switch_view("Startseite"))
menu_bar.add_command(label="Reinstoffe", command=lambda: switch_view("Reinstoffe"))
menu_bar.add_command(label="Stoffgemische", command=lambda: switch_view("Stoffgemische"))
menu_bar.add_command(label="Kreisprozesse", command=lambda: switch_view("Kreisprozesse"))
menu_bar.add_command(label="Verlauf", command=lambda: switch_view("Verlauf"))
menu_bar.add_command(label="Einstellungen", command=lambda: switch_view("Einstellungen"))

def convert_to_SI(value, quantity_type, unit):
    """Konvertiert den gegebenen Wert in die SI-Einheit basierend auf Größe und Einheit"""
    
    if quantity_type == "temperature":
        if unit == "Celsius":
            return value + 273.15
        elif unit == "Fahrenheit":
            return (value - 32) * 5/9 + 273.15
        elif unit == "Rankine":
            return value * 5/9
        elif unit == "Kelvin":
            return value

    elif quantity_type == "pressure":
        if unit == "bar":
            return value * 1e5
        elif unit == "atm":
            return value * 101325
        elif unit == "Pa":
            return value

    elif quantity_type == "density":
        if unit == "g/m³":
            return value / 1000
        elif unit == "kg/l":
            return value * 1000
        elif unit == "g/l":
            return value
        elif unit == "kg/m³":
            return value

    elif quantity_type == "enthalpy" or quantity_type == "internal_energy":
        if unit == "J/g":
            return value * 1000
        elif unit == "J/kg":
            return value

    elif quantity_type == "entropy" or quantity_type == "cp" or quantity_type == "cv":
        if unit == "J/g*K":
            return value * 1000
        elif unit == "J/kg*K":
            return value

    elif quantity_type == "volume":
        if unit == "m³/g":
            return value * 1000
        elif unit == "l/kg":
            return value / 1000
        elif unit == "l/g":
            return value
        elif unit == "m³/kg":
            return value

    return value  # Keine Umrechnung bei ungültigen Angaben

def convert_from_SI(value, quantity_type, unit):
    """Konvertiert den gegebenen Wert von der SI-Einheit zurück in die angegebene Einheit"""
    
    if quantity_type == "temperature":
        if unit == "Celsius":
            return value - 273.15
        elif unit == "Fahrenheit":
            return (value - 273.15) * 9/5 + 32
        elif unit == "Rankine":
            return value * 9/5
        elif unit == "Kelvin":
            return value

    elif quantity_type == "pressure":
        if unit == "bar":
            return value * 1e-5
        elif unit == "atm":
            return value / 101325
        elif unit == "Pa":
            return value

    elif quantity_type == "density":
        if unit == "g/m³":
            return value * 1000
        elif unit == "kg/l":
            return value / 1000
        elif unit == "g/l":
            return value
        elif unit == "kg/m³":
            return value

    elif quantity_type == "enthalpy" or quantity_type == "internal_energy":
        if unit == "J/g":
            return value / 1000
        elif unit == "J/kg":
            return value

    elif quantity_type == "entropy" or quantity_type == "cp" or quantity_type == "cv":
        if unit == "J/g*K":
            return value / 1000
        elif unit == "J/kg*K":
            return value

    elif quantity_type == "volume":
        if unit == "m³/g":
            return value / 1000
        elif unit == "l/kg":
            return value * 1000
        elif unit == "l/g":
            return value
        elif unit == "m³/kg":
            return value

    return value  # Keine Umrechnung bei ungültigen Angaben




#Menü erstellen
#-----------------------------------------------------------------------------------------------------
#Seite Reinstoffe

def show_reinstoffe():
    # Einheitenspeicherung für spätere Nutzung
    global temp_unit, pressure_unit, density_unit, volume_unit,i_energy_unit, enthalpy_unit, entropy_unit, viscosity_unit, cp_unit, cv_unit, tree
    for widget in main_frame.winfo_children():
        widget.destroy()
    
    def on_row_select(event):
        global selected_row_values
    
        # Alte Markierung entfernen
        for row in tree.get_children():
            tree.item(row, tags=())
    
        # Aktuell ausgewählte Zeile markieren
        selected_item = tree.focus()
        tree.item(selected_item, tags=("highlight",))
        tree.tag_configure("highlight", background="red", foreground="white")
    
        # Daten der ausgewählten Zeile speichern
        selected_row_values = tree.item(selected_item, "values")
        print("Ausgewählte Zeile:", selected_row_values)  # Optional: Debug-Ausgabe
    
    
    # Tabelle erstellen-------------------------------------------------------------------------------------
  

    tree_frame = tk.Frame(main_frame, width=1000, height=180)
    tree_frame.grid(row=11, column=0, columnspan=4, sticky="nsew", padx=40, pady=10)
    tree_frame.grid_propagate(False)
    
    tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
    tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
    
    
    tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
    tree["columns"] = ["temperatur", "pressure", "density", "volume", "internal energy", "enthalpy", "entropy", "viscosity", "state","vapor_quality","cp", "cv" ]
    tree.column("#0", width=0)          #damit 0. Spalte nicht sichtbar ist
    tree.bind('<Motion>', 'break')      #damit Spaltenbreite unveränderbar ist für User
    
    
    for col in tree["columns"]:
        tree.column(col, width=122, anchor="center")

    tree_scroll_y.config(command = tree.yview)
    tree_scroll_x.config(command = tree.xview)
    
    tree.grid(row=0, column=0, sticky="nsew")
    tree_scroll_y.grid(row=0, column=1, sticky="ns")
    tree_scroll_x.grid(row=1, column=0, sticky="ew")
    
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)
    
    tree.bind("<<TreeviewSelect>>", on_row_select)
    
    #-------------

    
    #Updates Einheiten überall---------------------------------------------------------------------------
    
    def update_units(*args):        #args damit die Einheiten jederzeit verändert werden, wenn sie geändert werden
       window.update_idletasks()  # Stellt sicher, dass Tkinter die Variablen aktualisiert hat
   
       global temp_unit, pressure_unit, density_unit, volume_unit,i_energy_unit, enthalpy_unit, entropy_unit, viscosity_unit, cp_unit, cv_unit, axis_names
       
       temp_unit = selected_vars["Temperatur T"].get()
       pressure_unit = selected_vars["Druck p"].get()
       density_unit = selected_vars["Dichte rho"].get()
       volume_unit = selected_vars["Volumen v"].get()       #0.0010029231088 für 298K und 100000Pa
       i_energy_unit = selected_vars ["Innere Energie u"].get()
       enthalpy_unit = selected_vars["Spezifische Enthalpie h"].get()
       entropy_unit = selected_vars["Spezifische Entropie s"].get()
       viscosity_unit = selected_vars["Viskosität eta"].get()
       cp_unit = selected_vars["Cp"].get()
       cv_unit = selected_vars["Cv"].get()
       
       selected_input1 = selected_variable1.get()       #Label 1 ändern
       if selected_input1 == "Dichte rho":
           input1unit_label["text"] = density_unit
       elif selected_input1 == "Druck p":
           input1unit_label["text"] = pressure_unit
       elif selected_input1 == "Temperatur T":
           input1unit_label["text"] = temp_unit
       elif selected_input1 == "Spezifische Enthalpie h":
           input1unit_label["text"] = enthalpy_unit
       elif selected_input1 == "Spezifische Entropie s":
           input1unit_label["text"] = entropy_unit
       elif selected_input1 == "Dampfqualität x":
           input1unit_label["text"] = "kg/kg"
       elif selected_input1 == "Volumen v":
           input1unit_label["text"] = volume_unit
       elif selected_input1 == "Innere Energie u":
           input1unit_label["text"] = i_energy_unit
       # elif selected_input1 == "Viskosität eta":
       #     input1unit_label["text"] = viscosity_unit
       # elif selected_input1 == "Cp":
       #     input1unit_label["text"] = cp_unit
       # elif selected_input1 == "Cv":
       #     input1unit_label["text"] = cv_unit
           
       selected_input2 = selected_variable2.get()       #Label 2 ändern
       if selected_input2 == "Dichte rho":
           input2unit_label["text"] = density_unit
       elif selected_input2 == "Druck p":
           input2unit_label["text"] = pressure_unit
       elif selected_input2 == "Temperatur T":
           input2unit_label["text"] = temp_unit
       elif selected_input2 == "Spezifische Enthalpie h":
           input2unit_label["text"] = enthalpy_unit
       elif selected_input2 == "Spezifische Entropie s":
           input2unit_label["text"] = entropy_unit
       elif selected_input2 == "Dampfqualität x":
           input2unit_label["text"] = "kg/kg"
       elif selected_input2 == "Volumen v":
           input2unit_label["text"] = volume_unit
       elif selected_input2 == "Innere Energie u":
           input2unit_label["text"] = i_energy_unit
       # elif selected_input2 == "Viskosität eta":
       #     input2unit_label["text"] = viscosity_unit
       # elif selected_input2 == "Cp":
       #     input2unit_label["text"] = cp_unit
       # elif selected_input2 == "Cv":
       #     input2unit_label["text"] = cv_unit
       
       columns = {
            "temperatur": f"Temperatur [{temp_unit}]",
            "pressure": f"Druck [{pressure_unit}]",
            "density": f"Dichte [{density_unit}]",
            "volume":f"Volumen [{volume_unit}]", 
            "internal energy":f"Innere Energie [{i_energy_unit}]",
            "enthalpy": f"Enthalpie [{enthalpy_unit}]",
            "entropy": f"Entropie [{entropy_unit}]",
            "vapor_quality": f"Dampfqualität [%]",
            "viscosity": f"Viskosität [{viscosity_unit}]", 
            "cp": f"Cp [{cp_unit}]", 
            "cv": f"Cv [{cv_unit}]", 
            "state": f"Aggregatszustand"
       }
       
       for col, heading in columns.items():
            tree.heading(col, text=heading)
       
       axis_names = {
            "temperatur": f"Temperatur [{temp_unit}]",
            "pressure": f"Druck [{pressure_unit}]",
            "density": f"Dichte [{density_unit}]",
            "volume":f"Volumen [{volume_unit}]", 
            "enthalpy": f"Enthalpie [{enthalpy_unit}]",
            "entropy": f"Entropie [{entropy_unit}]"}

       
       return axis_names
        
       
       
       
       
    row_index = 3
    
    
    heading_label = tk.Label(main_frame, text="Reinstoffe", font=("Arial", 20, "bold"),  width=40)
    heading_label.grid(row=0, column=0,  padx=20, pady=7, sticky="w", columnspan=3)
    heading_label.configure(background="lightblue")
    
    stoffauswahl_label = tk.Label(main_frame, text="1. Bitte wählen Sie den gewünschten Stoff aus:", font=("Arial", 12, "bold"))
    stoffauswahl_label.grid(row=1, column=0,  padx=20, pady=5, sticky="w")
    
    selected_fluid = tk.StringVar()         #Dropdownmenü Fluidauswahl
    selected_fluid.set("Water") 
    cp_fluids = CoolProp.FluidsList()
    fluid_combobox = ttk.Combobox(main_frame, width=38, textvariable=selected_fluid, values=cp_fluids, state="readonly")
    fluid_combobox.grid(row=1, column=1, padx=2, pady=5, sticky="w") 
    fluid_combobox.set("Water")
    
    einheiten_label = tk.Label(main_frame, text="2. Bitte wählen Sie die gewünschten Einheiten aus:", font=("Arial", 12, "bold"))
    einheiten_label.grid(row=2, column=0, columnspan=1, padx=20, pady=5, sticky="w")
    
    einheiten = {
        "Temperatur T": ["Kelvin", "Celsius", "Fahrenheit", "Rankine"],
        "Druck p": ["Pa", "bar", "atm"],
        "Dichte rho": ["kg/m³", "g/m³", "kg/l", "g/l"],
        "Volumen v": ["m³/kg", "m³/g", "l/kg", "l/g"],
        "Innere Energie u": ["J/kg", "J/g"],
        "Spezifische Enthalpie h": ["J/kg", "J/g"],
        "Spezifische Entropie s": ["J/kg*K", "J/g*K"],
        "Viskosität eta": ["Pa*s"],
        "Cp": ["J/kg*K", "J/g*K"],
        "Cv": ["J/kg*K", "J/g*K"]

        
    }
    
    einheiten_list =["Temperatur T", "Druck p", "Dichte rho", "Volumen v", "Innere Energie u", "Spezifische Enthalpie h", "Spezifische Entropie s","Dampfqualität x"]
    
   
    einheiten_frame = ttk.LabelFrame(main_frame, text="Einheiten")
    einheiten_frame.grid(row=3, column=0, columnspan=1, padx=20, pady=5, sticky="w")


    #Einheiten in Frames einsetzen
    for label, options in einheiten.items():
        size_label = ttk.Label(einheiten_frame, text=label + ":", font=("Arial", 10))
        size_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")
    
        selected_var = tk.StringVar(value=options[0])
        selected_vars[label] = selected_var
    
        dropdown = ttk.Combobox(einheiten_frame, textvariable=selected_var, values=options, state="readonly", width=20)
        dropdown.grid(row=row_index, column=1, padx=10, pady=5, sticky="w")
    
        selected_var.trace_add("write", update_units)
        row_index += 1

    temp_unit = selected_vars["Temperatur T"].get()
    pressure_unit = selected_vars["Druck p"].get()
    density_unit = selected_vars["Dichte rho"].get()
    volume_unit = selected_vars["Volumen v"].get()
    i_energy_unit = selected_vars ["Innere Energie u"].get()
    enthalpy_unit = selected_vars["Spezifische Enthalpie h"].get()
    entropy_unit = selected_vars["Spezifische Entropie s"].get()
    viscosity_unit = selected_vars["Viskosität eta"].get()
    cp_unit = selected_vars["Cp"].get()
    cv_unit = selected_vars["Cv"].get()

    
    # Werteeingabe
    eingabe_label = tk.Label(main_frame, text="3. Bitte wählen Sie zwei Input-Variablen aus und tragen Sie die Werte ein:", font=("Arial", 12, "bold") )
    eingabe_label.grid(row=8, column=0, columnspan=2, padx=20, pady=5, sticky="w")
    
    eingabe_label = tk.Label(main_frame, text="Input-Variable 1", font=("Arial", 10))
    eingabe_label.grid(row=9, column=0, padx=20, pady=5, sticky="w")
    
    eingabe_label = tk.Label(main_frame, text="Input-Variable 2", font=("Arial", 10))
    eingabe_label.grid(row=10, column=0, padx=20, pady=5, sticky="w")
    
    

    input1unit_label = ttk.Label(main_frame, text=temp_unit)
    input1unit_label.grid(row=9, column=1, padx=70, sticky="W")
    
    input2unit_label = ttk.Label(main_frame, text=temp_unit)
    input2unit_label.grid(row=10, column=1, padx=70,sticky="W")
    
    eingabe1_var = tk.StringVar()
    eingabe1_entry = ttk.Entry(main_frame, textvariable=eingabe1_var, width=10)
    eingabe1_entry.grid(row=9, column=1, padx=1, pady=5, sticky="w")
    
    eingabe2_var = tk.StringVar()
    eingabe2_entry = ttk.Entry(main_frame, textvariable=eingabe2_var, width=10)
    eingabe2_entry.grid(row=10, column=1, padx=1, pady=5, sticky="w")
    
    def on_select_inpu1(event):
        update_units()
        
    def on_select_inpu2(event):
        update_units()
    
    
    
    selected_variable1 = tk.StringVar(value="Temperatur T") #welche Größe ausgewählt
    input1_combobox = ttk.Combobox(main_frame, width=22, textvariable=selected_variable1, values=list(einheiten_list), state="readonly")
    input1_combobox.grid(row=9, column=0, padx=150, sticky="W")
    input1_combobox.bind_all("<<ComboboxSelected>>", on_select_inpu1)
    #input1_combobox.bind("<<ComboboxSelected>>", on_select_inpu1, add="+") 
    
    selected_variable2 = tk.StringVar(value="Druck p")
    input2_combobox = ttk.Combobox(main_frame, width=22, textvariable=selected_variable2, values=list(einheiten_list), state="readonly")
    input2_combobox.grid(row=10, column=0, padx=150,sticky="W")
    input2_combobox.bind("<<ComboboxSelected>>", on_select_inpu2)
     
    update_units()  #damit die Einheiten jederzeit verändert werden, wenn sie geändert werden
    
    #----------- Wertebereich ---------------------------------
    # Checkbox hinzufügen
                   
    #Startwert
    wertemin_label = tk.Label(main_frame, text="Startwert:", font=("Arial", 10), fg="light gray")
    wertemin_label.grid(row=9, column=2, padx=20, pady=5, sticky="w")
    
    wertemin_num=tk.DoubleVar(value=0)
   
    wertemin_entry = ttk.Entry(main_frame, textvariable=wertemin_num, width=10)
    wertemin_entry.grid(row=9, column=2, padx=100, pady=5, sticky="w")
    wertemin_entry.config(style="Custom.TEntry")

    
    #Endwert
    wertemax_label = tk.Label(main_frame, text="Endwert:", font=("Arial", 10), fg="light gray")
    wertemax_label.grid(row=10, column=2, padx=20, pady=5, sticky="w")
    
    wertemax_num=tk.DoubleVar(value=0)
   
    wertemax_entry = ttk.Entry(main_frame, textvariable=wertemax_num, width=10)
    wertemax_entry.grid(row=10, column=2, padx=100, pady=5, sticky="w")
    wertemax_entry.config(style="Custom.TEntry")
    
    #Schrittweite
    schritte_label = tk.Label(main_frame, text="Schrittweite:", font=("Arial", 10), fg="light gray")
    schritte_label.grid(row=9, column=3, padx=20, pady=5, sticky="w")
    
    schritte_num=tk.DoubleVar(value=0) 
    
    schritte_entry = ttk.Entry(main_frame, textvariable=schritte_num, width=10)
    schritte_entry.grid(row=9, column=3, padx=100, pady=5, sticky="w")
    schritte_entry.config(style="Custom.TEntry")
    
    
    #Fluidinformationen---------------------------------
    
    #alle labels erstellen ohne einfügen von Werten
    infos_frame = ttk.LabelFrame(main_frame, text="Fluidinformationen", relief="flat")
    infos_frame.grid(row=2, column=1, columnspan=1,rowspan=6, padx=2, pady=5, sticky="ew")
    infos_frame.configure(style="Custom.TLabelframe")
    
    
    pure_info_label = ttk.Label(infos_frame, text="- Reines Fluid:",font=("Arial", 10))
    pure_info_label.grid(row=0, column=0, columnspan=1, padx=5, sticky="W")
    
    molarmass_info_label = ttk.Label(infos_frame, text= "- Molare Masse: ", font=("Arial", 10))       #molare Masse
    molarmass_info_label.grid(row=2, column=0, padx=5,columnspan=2, sticky="W") 
    
    gasconstant_info_label = ttk.Label(infos_frame, text = "- Spez. Gaskonstante: ", font=("Arial", 10))     #Gaskonstante
    gasconstant_info_label.grid(row=3, column=0, columnspan=2, padx=5,sticky="W")


    # Critical Point Label
    ctp_label = ttk.Label(infos_frame, text="Kritischer Punkt:", font=("Arial", 10, "underline"))
    ctp_label.grid(row=5, column=0,padx=5, pady=10, sticky="W")
    
    ctp_pressure_label = ttk.Label(infos_frame,text= "- Druck: ", font=("Arial", 10))
    ctp_pressure_label.grid(row=6, column=0, columnspan=1, padx=5,sticky="W")
    
    ctp_temp_label = ttk.Label(infos_frame,text = "- Temperatur: ",font=("Arial", 10))
    ctp_temp_label.grid(row=7, column=0,padx=5, sticky="W")
    
    ctp_den_label = ttk.Label(infos_frame, text = "- Dichte: " , font=("Arial", 10))
    ctp_den_label.grid(row=8, column=0,padx=5, sticky="W")

    # Triple Point Label
    tp_label = ttk.Label(infos_frame, text="Tripelpunkt:", font=("Arial", 10, "underline"))
    tp_label.grid(row=9, column=0,padx=5, pady=5, sticky="W")
    
    tp_pressure_label = ttk.Label(infos_frame, text= "- Druck: " , font=("Arial", 10))
    tp_pressure_label.grid(row=10, column=0,padx=5, sticky="W")
    
    tp_temp_label = ttk.Label(infos_frame, text= "- Temperatur: " , font=("Arial", 10))
    tp_temp_label.grid(row=11, column=0,padx=5, sticky="W")

    # Fluidlimits Label
    limit_label = ttk.Label(infos_frame, text="Fluidgrenzen:", font=("Arial", 10, "underline"))
    limit_label.grid(row=12, column=0, padx=5,pady=5, sticky="W")
    
    maxtemp_label = ttk.Label(infos_frame, text="- Max. Druck: ", font=("Arial", 10))
    maxtemp_label.grid(row=16, column=0,padx=5, sticky="W")
    
    mfloatemp_label = ttk.Label(infos_frame, text = "- Max. Temperatur: " ,font=("Arial", 10))
    mfloatemp_label.grid(row=14, column=0,padx=5, sticky="W")
    
    maxp_label = ttk.Label(infos_frame, text= "- Min. Druck: ", font=("Arial", 10))
    maxp_label.grid(row=15, column=0,padx=5, sticky="W")
    
    minp_label = ttk.Label(infos_frame,text="- Min. Temperatur: ", font=("Arial", 10))
    minp_label.grid(row=13, column=0, padx=5,sticky="W")

    maxp=float()
    maxtemp=float()
    minp=float()
    mfloatemp=float()
    
    
    
    def fluid_info(selected_fluid):
        pure_info = CoolProp.get_fluid_param_string(selected_fluid.get(), "pure")
        print(pure_info)
        if pure_info == "true":
            pure_info_label["text"] = "- Reines Fluid: Ja"
        elif pure_info == "false":
            pure_info_label["text"] = "- Reines Fluid: Nein"

        # Molar Mass
        molarmass_info = CoolProp.PropsSI("M", selected_fluid.get())
        molarmass_info_label["text"] = "- Molare Masse: " + str(round(molarmass_info * 1000, 3)) + " g/mol"    #mol masse auf 3 Stellen nach Komma
        gascostant = CoolProp.PropsSI("gas_constant", selected_fluid.get())
        gasconstant_info_label["text"] = "- Spez. Gaskonstante: " + str(round(gascostant / molarmass_info, 1)) + " J/kg*K"    #Gaskonstante auf eine Nachkommastelle genau

        # Critical Point
        ctp_pressure = CoolProp.PropsSI("pcrit", selected_fluid.get())
        ctp_pressure_label["text"] = "- Druck: " + str(round(ctp_pressure,3)) + " Pa"
        ctp_temp = CoolProp.PropsSI("Tcrit", selected_fluid.get())
        ctp_temp_label["text"] = "- Temperatur: " + str(round(ctp_temp,3)) + " Kelvin"
        ctp_den = CoolProp.PropsSI("rhocrit", selected_fluid.get())
        ctp_den_label["text"] = "- Dichte: " + str(round(ctp_den, 3)) + " kg/m³"

        # Triple Point
        tp_pressure = CoolProp.PropsSI("ptriple", selected_fluid.get())
        tp_pressure_label["text"] = "- Druck: " + str(round(tp_pressure, 3)) + " Pa"
        tp_temp = CoolProp.PropsSI("Ttriple", selected_fluid.get())
        tp_temp_label["text"] = "- Temperatur: " + str(round(tp_temp,3)) + " Kelvin"

        # Fluidlimits
       
        maxp = CoolProp.PropsSI("pmax", selected_fluid.get())
        maxp_label["text"] = "- Max. Druck: " + str(round(maxp,3)) + " Pa"
        maxtemp = CoolProp.PropsSI("Tmax", selected_fluid.get())
        maxtemp_label["text"] = "- Max. Temperatur: " + str(round(maxtemp,3)) + " Kelvin"
        minp = CoolProp.PropsSI("pmin", selected_fluid.get())
        minp_label["text"] = "- Min. Druck: " + str(round(minp, 3)) + " Pa"
        mfloatemp = CoolProp.PropsSI("Tmin", selected_fluid.get())
        mfloatemp_label["text"] = "- Min. Temperatur: " + str(round(mfloatemp, 3)) + " Kelvin"
    
    maxtemp = CoolProp.PropsSI("Tmax", selected_fluid.get())
    mfloatemp = CoolProp.PropsSI("Tmin", selected_fluid.get())
    maxp = CoolProp.PropsSI("pmax", selected_fluid.get())
    minp = CoolProp.PropsSI("pmin", selected_fluid.get())

    # Diagramm erstellen-----------------------------------------------------------------------------------
    
    # Diagram Frame
    diagram_frame = ttk.LabelFrame(main_frame, text="Diagramm")
    diagram_frame.grid(row=1, column=2, rowspan=7, columnspan=2, padx=20, pady=1, sticky="nw")
    
    # Isolinien Frame
    iso_frame = ttk.LabelFrame(diagram_frame, text="Isolinien Ein-/Ausblenden")
    iso_frame.grid(row=7, column=1, columnspan=1, padx=10, sticky="W")
    # Set initial state for checkboxes
    
    wertebereich_label = ttk.Label(diagram_frame, text="Wertebereich Diagramm:", font=("Arial", 12, "underline"))
    wertebereich_label.grid(row=0, column=1, columnspan=1, padx=10, sticky="W")
    
    x_ax_label = ttk.Label(diagram_frame, text="1. x-Achse:", font=("Arial", 10))
    x_ax_label.grid(row=1, column=1, columnspan=1, padx=10, sticky="W")
    
    minx_label = ttk.Label(diagram_frame, text="min:", font=("Arial", 10))
    minx_label.grid(row=2, column=1, columnspan=1, padx=10, sticky="W")
    
    minx_var = tk.DoubleVar(value=0)
    minx_entry = ttk.Entry(diagram_frame, textvariable=minx_var, width=10)
    minx_entry.grid(row=2, column=1, columnspan=1, padx=80, sticky="W")
    
    maxx_label = ttk.Label(diagram_frame, text="max:", font=("Arial", 10))
    maxx_label.grid(row=3, column=1, columnspan=1, padx=10, sticky="W")
    
    maxx_var = tk.DoubleVar(value=0)
    maxx_entry = ttk.Entry(diagram_frame, textvariable=maxx_var, width=10)
    maxx_entry.grid(row=3, column=1, columnspan=1, padx=80, sticky="W")
    
    y_ax_label = ttk.Label(diagram_frame, text="2. y-Achse:", font=("Arial", 10))
    y_ax_label.grid(row=4, column=1, columnspan=1, padx=10, sticky="W")
    
    miny_label = ttk.Label(diagram_frame, text="min:", font=("Arial", 10))
    miny_label.grid(row=5, column=1, columnspan=1, padx=10, sticky="W")
    
    miny_var = tk.DoubleVar(value=0)
    miny_entry = ttk.Entry(diagram_frame, textvariable=miny_var, width=10)
    miny_entry.grid(row=5, column=1, columnspan=1, padx=80, sticky="W")
    
    maxy_label = ttk.Label(diagram_frame, text="max:", font=("Arial", 10))
    maxy_label.grid(row=6, column=1, columnspan=1, padx=10, sticky="W")
    
    maxy_var = tk.DoubleVar(value=0)
    maxy_entry = ttk.Entry(diagram_frame, textvariable=maxy_var, width=10)
    maxy_entry.grid(row=6, column=1, columnspan=1, padx=80, sticky="W")
    
    

    # Labels im Diagramm-Frame
    
    diagrams = ["T-s-Diagramm", "log(p)-h-Diagramm", "h-s-Diagramm", "p-T-Diagramm", "T-v-Diagramm", "p-v-Diagramm"]
    diagram_get = []

    # Diagramm Combobox (Auswahl Diagramm)
    selected_diagram = tk.StringVar()
    diagram_combobox = ttk.Combobox(diagram_frame, width=30, textvariable=selected_diagram, values=diagrams, state="readonly")
    diagram_combobox.grid(row=0, column=0, padx=15, sticky="NW")
    diagram_combobox.set("T-s-Diagramm")
    

    
   
    def on_select_check():
        create_figure(selected_fluid.get())
        print("")
    
    # Checkboxes Isolines
    isobar_check = tk.Checkbutton(iso_frame, text="Isobare", variable=isobar_var, onvalue=True, offvalue=False, command=on_select_check, selectcolor=stil_isobare["farbe"])
    isobar_check.grid(row=0, column=0, sticky = "W")
    isotherm_check = tk.Checkbutton(iso_frame, text="Isotherme", variable=isotherm_var, onvalue=True, offvalue=False,  command=on_select_check, selectcolor=stil_isotherme["farbe"])
    isotherm_check.grid(row=1, column=0, sticky = "W")
    isochor_check = tk.Checkbutton(iso_frame, text="Isochore", variable=isochor_var, onvalue=True, offvalue=False,  command=on_select_check, selectcolor=stil_isochore["farbe"])
    isochor_check.grid(row=2, column=0, sticky = "W")
    isentropic_check = tk.Checkbutton(iso_frame, text="Isentrope", variable=isentropic_var, onvalue=True, offvalue=False,  command=on_select_check, selectcolor=stil_isentrope["farbe"])
    isentropic_check.grid(row=3, column=0, sticky = "W")
    isenthalpic_check = tk.Checkbutton(iso_frame, text="Isenthalpe", variable=isenthalpic_var, onvalue=True, offvalue=False,  command=on_select_check, selectcolor=stil_isenthalpe["farbe"])
    isenthalpic_check.grid(row=4, column=0, sticky = "W")
    isovapore_check = tk.Checkbutton(iso_frame, text="Isovapore", variable=isovapore_var, onvalue=True, offvalue=False, command=on_select_check, selectcolor=stil_isovapore["farbe"])
    isovapore_check.grid(row=5, column=0, sticky = "W")
    
    
    def mouse_event(event):
        global mouse_event_triggered
        global x_SI, y_SI  # Speichern zur weiteren Verwendung

        if event.xdata is None or event.ydata is None:
            return
        
        toolbar = event.canvas.toolbar if hasattr(event.canvas, 'toolbar') else None

        # Abbrechen, wenn gerade gezoomt oder gepannt wird
        if toolbar and toolbar.mode != "":
            return 
        
        x = round(event.xdata, 3)
        y = round(event.ydata, 3)
        eingabe1_var.set(y_SI)
        eingabe2_var.set(x_SI)


        print("x=", x, "y=", y)
        
        current_ax.plot(x, y, 'ro')  # ro = red circle
        current_canvas.draw()
        mouse_event_triggered = True  # merkt sich, dass Mouse-Event ausgelöst wurde
        #tree.insert("", "end", values=(x,y))
        
        if selected_diagram.get() =="T-s-Diagramm":
            input1_combobox.set("Temperatur T")
            input1unit_label["text"] = temp_unit     
            input2_combobox.set("Spezifische Entropie s")
            input2unit_label["text"] = entropy_unit
            #tree.insert("", "end", values=(x,y))
            calc()
                           
        elif selected_diagram.get() == "log(p)-h-Diagramm":
            input1_combobox.set("Druck p")
            input1unit_label["text"] = pressure_unit
            input2_combobox.set("Spezifische Enthalpie h")
            input2unit_label["text"] = enthalpy_unit
            calc()
            
            
        elif selected_diagram.get() == "h-s-Diagramm":
            input1_combobox.set("Spezifische Enthalpie h")
            input1unit_label["text"] = enthalpy_unit       
            input2_combobox.set("Spezifische Entropie s")
            input2unit_label["text"] = entropy_unit
            calc()

                 
        elif selected_diagram.get() == "p-T-Diagramm":
            input1_combobox.set("Druck p")
            input1unit_label["text"] = pressure_unit     
            input2_combobox.set("Temperatur T")
            input2unit_label["text"] = temp_unit
            calc()
            
            
            
        elif selected_diagram.get() == "T-v-Diagramm":
            input1_combobox.set("Temperatur T")
            input1unit_label["text"] = temp_unit      
            input2_combobox.set("Volumen v")
            input2unit_label["text"] = volume_unit
            calc()
            
        elif selected_diagram.get() == "p-v-Diagramm":
            input1_combobox.set("Druck p")
            input1unit_label["text"] = pressure_unit      
            input2_combobox.set("Volumen v")
            input2unit_label["text"] = volume_unit
            calc()
        
        
        
        
    # diagram(selected_diagram.get())
    toolbar_frame = ttk.LabelFrame(diagram_frame,  relief="flat")
    toolbar_frame.grid(row=8, column=0, sticky="NW")  
    
    
    def get_column_values(columns):
        # Liste der Werte für die angegebene Spalte erstellen
        column_values = []
        
        # Alle Zeilen durchlaufen
        for item_id in tree.get_children():
            # Die Werte der Zeile abrufen
            item = tree.item(item_id)
            values = item['values']
            
            # Den Index der gewünschten Spalte finden
            if columns == "temperatur":
                column_values.append(float(values[0]))  
            elif columns == "pressure":
                column_values.append(float(values[1]))  
            elif columns == "volume":
                column_values.append(float(values[3])) 
            elif columns == "enthalpy":
                column_values.append(float(values[5])) 
            elif columns == "entropy":
                column_values.append(float(values[6]))  

        
        return column_values
    

    def calculate_step_size(min_value, max_value):
        range_value = max_value - min_value
        # Bestimme eine geeignete Schrittweite
        if range_value <= 10:
            step_size = 2
        elif range_value <= 100:
            #print("range value kleiner 100")
            step_size = 20
        elif range_value <= 200:
            #print("range value kleiner 100")
            step_size = 40
        elif range_value <= 500:
            #print("range value kleiner 500")
            step_size = 100
        elif range_value <= 1000:
            #print("range value kleiner 1000")
            step_size = 200
        elif range_value <= 1500:
            #print("range value kleiner 1500")
            step_size = 300
        elif range_value <= 3000:
            #print("range value kleiner 3000")
            step_size = 500
        elif range_value <= 5000:
            #print("range value kleiner 5000")
            step_size = 500
        elif range_value <= 10000:
            #print("range value kleiner 10000")
            step_size = 1000
        elif range_value <= 15000:
            #print("range value kleiner 15000")
            step_size = 1500
        elif range_value <= 100000:
            #print("range value kleiner 100000")
            step_size = 10000
        elif range_value <= 1000000:
            #print("range value kleiner 1000000")
            step_size = 100000
        elif range_value <= 2000000:
            #print("range value kleiner 2000000")
            step_size = 200000
        elif range_value <= 5000000:
            #print("range value kleiner 5000000")
            step_size = 500000
        else:
            #print("range value größer 5000000")
            step_size = 2000000 
        # Wenn der Bereich zu groß ist, justiere die Schrittweite
        if range_value / step_size > 20:
            step_size = (range_value // 20)
        # Der Schrittwert muss eine runde Zahl sein (z. B. 10, 50, 100, ...), nicht 33, 37, ...
        step_size = np.round(step_size, -int(np.floor(np.log10(step_size))))  # Runde auf die nächste 10er Potenz
        return step_size
    
  

    def plot_saturation_lines_general(ax, fluid, diagram_type="T-s-Diagramm", units=None):
        fluid_name = selected_fluid.get() if callable(getattr(fluid, "get", None)) else selected_fluid.get()
        
    
        T_trip = CoolProp.PropsSI("Ttriple", fluid_name)
        T_crit = CoolProp.PropsSI("Tcrit", fluid_name)
        T_range = np.linspace(T_trip , T_crit , 300)
        
        print("T_trip=", T_trip, "T_crit=", T_crit)
        
        data_liq = []
        data_vap = []
        x_vals = []
        h_l, h_v = [], []
        s_l, s_v = [], []
        
        for T in T_range:
            try:
                if diagram_type == "T-s-Diagramm":
                    s_liq = CoolProp.PropsSI("S", "T", T, "Q", 0, fluid_name)
                    s_vap = CoolProp.PropsSI("S", "T", T, "Q", 1, fluid_name)
                    data_liq.append(s_liq)
                    data_vap.append(s_vap)
                    x_vals.append(T)
    
                elif diagram_type == "log(p)-h-Diagramm":
                    h_liq = CoolProp.PropsSI("H", "T", T, "Q", 0, fluid_name)
                    h_vap = CoolProp.PropsSI("H", "T", T, "Q", 1, fluid_name)
                    p = CoolProp.PropsSI("P", "T", T, "Q", 0, fluid_name)
                    data_liq.append(h_liq)
                    data_vap.append(h_vap)
                    x_vals.append(p)
    
                elif diagram_type == "h-s-Diagramm":
                   
                    h_liq = CoolProp.PropsSI("H", "T", T, "Q", 0, fluid_name)
                    h_vap = CoolProp.PropsSI("H", "T", T, "Q", 1, fluid_name)
                    s_liq = CoolProp.PropsSI("S", "T", T, "Q", 0, fluid_name)
                    s_vap = CoolProp.PropsSI("S", "T", T, "Q", 1, fluid_name)
                    h_l.append(h_liq)
                    h_v.append(h_vap)
                    s_l.append(s_liq)
                    s_v.append(s_vap)
                 
                    
                elif diagram_type == "p-T-Diagramm":
                    p = CoolProp.PropsSI("P", "T", T, "Q", 0, fluid_name)
                    data_liq.append(p)
                    x_vals.append(T)
    
                elif diagram_type == "T-v-Diagramm":
                    rho_liq = CoolProp.PropsSI("D", "T", T, "Q", 0, fluid_name)
                    rho_vap = CoolProp.PropsSI("D", "T", T, "Q", 1, fluid_name)
                    v_liq = 1 / rho_liq
                    v_vap = 1 / rho_vap
                    data_liq.append(v_liq)
                    data_vap.append(v_vap)
                    x_vals.append(T)
    
                elif diagram_type == "p-v-Diagramm":
                    p = CoolProp.PropsSI("P", "T", T, "Q", 0, fluid_name)
                    rho_liq = CoolProp.PropsSI("D", "T", T, "Q", 0, fluid_name)
                    rho_vap = CoolProp.PropsSI("D", "T", T, "Q", 1, fluid_name)
                    v_liq = 1 / rho_liq
                    v_vap = 1 / rho_vap
                    data_liq.append((v_liq, p))
                    data_vap.append((v_vap, p))
    
            except:
                continue

        if units is not None:
            def conv_list(values, qtype, unit):
                return [convert_from_SI(val, qtype, unit) for val in values]
    
            if diagram_type == "T-s-Diagramm":
                x_vals = conv_list(x_vals, "temperature", units["y"])
                data_liq = conv_list(data_liq, "entropy", units["x"])
                data_vap = conv_list(data_vap, "entropy", units["x"])
    
            elif diagram_type == "log(p)-h-Diagramm":
                x_vals = conv_list(x_vals, "pressure", units["y"])
                data_liq = conv_list(data_liq, "enthalpy", units["x"])
                data_vap = conv_list(data_vap, "enthalpy", units["x"])
    
            elif diagram_type == "h-s-Diagramm":
                h_l = conv_list(h_l, "enthalpy", units["y"])
                h_v = conv_list(h_v, "enthalpy", units["y"])
                s_l = conv_list(s_l, "entropy", units["x"])
                s_v = conv_list(s_v, "entropy", units["x"])
    
            elif diagram_type == "p-T-Diagramm":
                x_vals = conv_list(x_vals, "temperature", units["x"])
                data_liq = conv_list(data_liq, "pressure", units["y"])
    
            elif diagram_type == "T-v-Diagramm":
                x_vals = conv_list(x_vals, "temperature", units["x"])
                data_liq = conv_list(data_liq, "volume", units["y"])
                data_vap = conv_list(data_vap, "volume", units["y"])
    
            elif diagram_type == "p-v-Diagramm":
                data_liq = [(convert_from_SI(v, "volume", units["x"]), convert_from_SI(p, "pressure", units["y"])) for v, p in data_liq]
                data_vap = [(convert_from_SI(v, "volume", units["x"]), convert_from_SI(p, "pressure", units["y"])) for v, p in data_vap]


        # Plotten je nach Diagrammtyp
        if diagram_type == "h-s-Diagramm":
            ax.plot(s_l, h_l, label="Siedelinie (Q=0)", color=stil_siedelinie["farbe"], linewidth=float(stil_siedelinie["dicke"]), linestyle=stil_siedelinie["stil"], zorder=8)
            ax.plot(s_v, h_v, label="Taulinie (Q=1)", color=stil_taulinie["farbe"], linewidth=float(stil_taulinie["dicke"]), linestyle=stil_taulinie["stil"], zorder=8)
    
        elif diagram_type == "p-v-Diagramm":
            v_liq, p_vals = zip(*data_liq)
            v_vap, _ = zip(*data_vap)
            ax.plot(v_liq, p_vals, label="Siedelinie (Q=0)", color=stil_siedelinie["farbe"], linewidth=float(stil_siedelinie["dicke"]), linestyle=stil_siedelinie["stil"],zorder=8)
            ax.plot(v_vap, p_vals, label="Taulinie (Q=1)", color=stil_taulinie["farbe"], linewidth=float(stil_taulinie["dicke"]), linestyle=stil_taulinie["stil"], zorder=8)
    
        elif diagram_type == "p-T-Diagramm":
            ax.plot(x_vals, data_liq, label="Dampfdruckkurve", color=stil_siedelinie["farbe"],linewidth=float(stil_siedelinie["dicke"]), linestyle=stil_siedelinie["stil"], zorder=8)
    
        else:
            ax.plot(data_liq, x_vals, label="Siedelinie (Q=0)", color=stil_siedelinie["farbe"],linewidth=float(stil_siedelinie["dicke"]), linestyle=stil_siedelinie["stil"], zorder=8)
            ax.plot(data_vap, x_vals, label="Taulinie (Q=1)", color=stil_taulinie["farbe"], linewidth=float(stil_taulinie["dicke"]), linestyle=stil_taulinie["stil"], zorder=8)
    
        # Tripelpunkt
        try:
            T_t = T_trip
            if diagram_type == "T-s-Diagramm":
                s = convert_from_SI(CoolProp.PropsSI("S", "T", T_t, "Q", 0, fluid_name), "entropy", entropy_unit)
                if units is not None:
                    s = conv_list(s, "entropy", units["x"])   
                ax.scatter(s, T_t, label="Tripelpunkt", color=stil_tripel["farbe"], marker=stil_tripel["marker"], s=stil_tripel["größe"] * 5, zorder=9)
            elif diagram_type == "log(p)-h-Diagramm":
                h = CoolProp.PropsSI("H", "T", T_t, "Q", 0, fluid_name)
                p = CoolProp.PropsSI("P", "T", T_t, "Q", 0, fluid_name)
                if units is not None:
                    p = conv_list(p, "pressure", units["y"])
                    h = conv_list(h, "enthalpy", units["x"])
                ax.scatter(h, p, label="Tripelpunkt", color=stil_tripel["farbe"], marker=stil_tripel["marker"], s=stil_tripel["größe"] * 5, zorder=9)
            elif diagram_type == "h-s-Diagramm":
                s = CoolProp.PropsSI("S", "T", T_t, "Q", 0, fluid_name)
                h = CoolProp.PropsSI("H", "T", T_t, "Q", 0, fluid_name)
                if units is not None:
                    h = conv_list(h, "enthalpy", units["y"])
                    s = conv_list(s, "entropy", units["x"])
                ax.scatter(s, h,label="Tripelpunkt", color=stil_tripel["farbe"], marker=stil_tripel["marker"], s=stil_tripel["größe"] * 5, zorder=9)
            elif diagram_type == "p-T-Diagramm":
                p = CoolProp.PropsSI("P", "T", T_t, "Q", 0, fluid_name)
                if units is not None:
                    T_t = conv_list(T_t, "temperature", units["x"])
                    p = conv_list(p, "pressure", units["y"])
                ax.scatter(T_t, p, label="Tripelpunkt", color=stil_tripel["farbe"], marker=stil_tripel["marker"], s=stil_tripel["größe"] * 5, zorder=9)
            elif diagram_type in ["T-v-Diagramm", "p-v-Diagramm"]:
                
                rho = CoolProp.PropsSI("D", "T", T_t, "Q", 0, fluid_name)
                v = 1 / rho
                p = CoolProp.PropsSI("P", "T", T_t, "Q", 0, fluid_name)
                if diagram_type == "T-v-Diagramm":                   
                    y = T_t 
                    if units is not None: y = conv_list(y, "temperature", units["x"])
                else:
                    y=p
                    if units is not None: y = conv_list(y, "pressure", units["y"])
                if diagram_type == "T-v-Diagramm":   
                    x = v 
                    if units is not None:x = conv_list(x, "volume", units["y"])
                else: 
                    x= v
                    if units is not None: x = conv_list(x, "volume", units["y"])
                ax.scatter(x, y, label="Tripelpunkt", color=stil_tripel["farbe"], marker=stil_tripel["marker"], s=stil_tripel["größe"] * 5, zorder=9)
        except:
            pass
    
        # Kritischer Punkt
        try:
            T_c = T_crit
            if diagram_type == "T-s-Diagramm":
                s = CoolProp.PropsSI("S", "T", T_c, "Q", 0, fluid_name)
                if units is not None:
                    s = conv_list(s, "entropy", units["x"])  
                
                ax.scatter(s, T_c, label="Kritischer Punkt",color=stil_krit["farbe"], marker=stil_krit["marker"], s=stil_krit["größe"] * 5, zorder=9)#color=stil_krit["farbe"], marker=stil_krit["marker"], s=stil_krit["größe"]
            elif diagram_type == "log(p)-h-Diagramm":
                h = CoolProp.PropsSI("H", "T", T_c, "Q", 0, fluid_name)
                p = CoolProp.PropsSI("P", "T", T_c, "Q", 0, fluid_name)
                if units is not None:
                    p = conv_list(p, "pressure", units["y"])
                    h = conv_list(h, "enthalpy", units["x"])
                ax.scatter(h, p, label="Kritischer Punkt",color=stil_krit["farbe"], marker=stil_krit["marker"], s=stil_krit["größe"] * 5, zorder=9)
            elif diagram_type == "h-s-Diagramm":
                s = CoolProp.PropsSI("S", "T", T_c, "Q", 0, fluid_name)
                h = CoolProp.PropsSI("H", "T", T_c, "Q", 0, fluid_name)
                if units is not None:
                    h = conv_list(h, "enthalpy", units["y"])
                    s = conv_list(s, "entropy", units["x"])
                ax.scatter(s, h, label="Kritischer Punkt",color=stil_krit["farbe"], marker=stil_krit["marker"], s=stil_krit["größe"] * 5, zorder=9)
            elif diagram_type == "p-T-Diagramm":
                p = CoolProp.PropsSI("P", "T", T_c, "Q", 1, fluid_name)
                if units is not None:
                    T_c = conv_list(T_c, "temperature", units["x"])
                    p = conv_list(p, "pressure", units["y"])
                ax.scatter(T_c, p,label="Kritischer Punkt",color=stil_krit["farbe"], marker=stil_krit["marker"], s=stil_krit["größe"] * 5, zorder=9)
            elif diagram_type in ["T-v-Diagramm", "p-v-Diagramm"]:
                rho = CoolProp.PropsSI("D", "T", T_c, "Q", 0, fluid_name)
                v = 1 / rho
    
                p = CoolProp.PropsSI("P", "T", T_c, "Q", 0, fluid_name)

                if diagram_type == "T-v-Diagramm":                   
                    y = T_c 
                    if units is not None: y = conv_list(y, "temperature", units["y"])
                else:
                    y=p
                    if units is not None: y = conv_list(y, "pressure", units["y"])
                if diagram_type == "T-v-Diagramm":   
                    x = v 
                    if units is not None:x = conv_list(x, "volume", units["x"])
                else: 
                    x= v
                    if units is not None: x = conv_list(x, "volume", units["x"])
                ax.scatter(x, y, label="Kritischer Punkt",color=stil_krit["farbe"], marker=stil_krit["marker"], s=stil_krit["größe"] * 5, zorder=9)
        except:
            pass
    
    
        handles, labels = ax.get_legend_handles_labels()
        # if handles and legende_set.get() == True:
        #     ax.legend()
        if handles and legende_set.get():
            #print("Legende in create_figure")
            ax.legend()

    
    def generate_isolines_general(fluid_name, ax, x_range, y_range, isoline_type='isobar', num_lines=5, x_axis='S', y_axis='T'):

    
        def convert_axis_input(axis_name, value):
            if axis_name.upper() == 'V':
                return 'Dmass', 1.0 / value  # spezifisches Volumen → Dichte
            return axis_name, value
    
        def get_prop(prop, var1, val1, var2, val2):
            try:
                return CoolProp.PropsSI(prop, var1, val1, var2, val2, fluid_name)
            except:
                return None
            
        def get_volume(T, P):
            rho = get_prop("Dmass", "T", T, "P", P)
            if rho and rho > 0:
                return 1.0 / rho
            return None

        def resolve_value(axis, val):
            if axis.upper() == 'V':
                return 1.0 / val  # V → rho
            return val
       
        if isoline_type == 'isobar':
            num_lines =  int(stil_isobare["anzahl"])
            p_vals = np.logspace(np.log10(1000), np.log10(CoolProp.PropsSI("pcrit", fluid_name)), num_lines)
            for p in p_vals:
                x_list, y_list = [], []
                y_vals = np.linspace(y_range[0], y_range[1], 300)
                for y_val in y_vals:
                    try:
                        y_input_name, y_input_val = convert_axis_input(y_axis, y_val)
                        if x_axis.upper() == 'V':
                            # T über y_axis holen, z.B. T = y_val
                            if y_axis.upper() != 'T':
                                T = get_prop("T", y_input_name, y_input_val, "P", p)
                            else:
                                T = y_val
                            if T is None:
                                continue
                            x_val = get_volume(T, p)
                        else:
                            x_val = get_prop(x_axis, y_input_name, y_input_val, "P", p)
                        if x_val is None:
                            continue
                        x_list.append(x_val)
                        y_list.append(y_val)
        
                    except:
                        continue
                ax.plot(x_list, y_list, color=stil_isobare["farbe"], linewidth=float(stil_isobare["dicke"]), linestyle=stil_isobare["stil"],label="_nolegend_")
                mid = len(x_list) // 3
                ax.text(x_list[-mid], y_list[-mid], f'{p/1000:.1f} kPa', fontsize=9, color="black", rotation=45)
        
        elif isoline_type == 'isotherm':
            num_lines =  int(stil_isotherme["anzahl"])
            T_min = CoolProp.PropsSI("Ttriple", fluid_name)
            T_max = CoolProp.PropsSI("Tcrit", fluid_name)
            T_vals = np.linspace(T_min + 1, T_max - 1, num_lines)
            for T in T_vals:
                x_list, y_list = [], []
                p_vals = np.logspace(3, np.log10(CoolProp.PropsSI("pcrit", fluid_name)), 300)
                for p in p_vals:
                    try:
                        # x-Achse
                        if x_axis.upper() == 'V':
                            x_val = get_volume(T, p)
                        else:
                            x_val = get_prop(x_axis, "T", T, "P", p)
                        # y-Achse
                        if y_axis.upper() == 'V':
                            y_val = get_volume(T, p)
                        else:
                            y_val = get_prop(y_axis, "T", T, "P", p)
                        
                        if x_val is None or y_val is None or x_val <= 0 or y_val <= 0:
                            continue
                        x_list.append(x_val)
                        y_list.append(y_val)
                    except:
                        continue
                ax.plot(x_list, y_list, color=stil_isotherme["farbe"], linewidth=float(stil_isotherme["dicke"]), linestyle=stil_isotherme["stil"], label="_nolegend_")
                if selected_diagram.get() =="log(p)-h-Diagramm":
                    ax.text(x_list[-10], y_list[-10], f'{T:.1f} K', fontsize=9, color="black", rotation=45)
                elif selected_diagram.get() == "h-s-Diagramm":
                    ax.text(x_list[100], y_list[100], f'{T:.1f} K', fontsize=9, color="black")
                elif selected_diagram.get() == "p-v-Diagramm":
                    ax.text(x_list[100], y_list[100], f'{T:.1f} K', fontsize=9, color="black")

        
        elif isoline_type == 'isentrope':
            num_lines= int(stil_isentrope["anzahl"])
            T_min = CoolProp.PropsSI("Ttriple", fluid_name)
            T_max = CoolProp.PropsSI("Tcrit", fluid_name)
            T_vals = np.linspace(T_min + 1, T_max - 1, num_lines)
            #p_min = CoolProp.PropsSI("ptriple", fluid_name)
            #p_min = CoolProp.PropsSI("ptriple", selected_fluid.get())
            #print("p_min=", p_min)
            print("Tmin=", T_min, "Tmax=", T_max)
            s_vals = []
            for T in T_vals:
                try:
                    s_vals.append(CoolProp.PropsSI("S", "T", T, "Q", 0, fluid_name))
                    s_vals.append(CoolProp.PropsSI("S", "T", T, "Q", 1, fluid_name))
                except:
                    continue
            if not s_vals:
                return  # keine gültigen Entropiewerte
            s_vals = np.linspace(min(s_vals), max(s_vals), num_lines)
            for s in s_vals:
                x_list, y_list = [], []
                y_vals = np.logspace(np.log10(y_range[0]), np.log10(y_range[1]), 500)
                print("y_raneg0=", y_range)
                #print("y_vals=", y_vals)
                for y_val in y_vals:
                    try:
                        y_input_name, y_input_val = convert_axis_input(y_axis, y_val)
                        print("y_inpu_val=", y_input_val)
                        x_val = CoolProp.PropsSI(x_axis, y_input_name, y_input_val, "S", s, fluid_name)
                        x_list.append(x_val)
                        y_list.append(y_val)
                    except:
                        continue
                ax.plot(x_list, y_list, color=stil_isentrope["farbe"], linewidth=float(stil_isentrope["dicke"]), linestyle=stil_isentrope["stil"], label="_nolegend_")
                mid = len(x_list) // 10
                ax.text(x_list[mid], y_list[mid], f'{s:.1f} J/kg*K', fontsize=9, color="black", rotation=45)
    
        elif isoline_type == 'isochor':
            num_lines= int(stil_isochore["anzahl"])
            rho_vals = np.logspace(-1, 3, num_lines)
            for rho in rho_vals:
                x_list, y_list = [], []
                #
                if selected_diagram.get()=="T-s-Diagramm" or selected_diagram.get()=="h-s-Diagramm" or selected_diagram.get()=="p-T-Diagramm":
                    y_vals = np.linspace(y_range[0], y_range[1], 300)
                elif selected_diagram.get()=="log(p)-h-Diagramm":
                    y_vals = np.logspace(np.log10(minp), np.log10(y_range[1]), 500)
                
                for y_val in y_vals:
                    try:
                        y_input_name, y_input_val = convert_axis_input(y_axis, y_val)
                        x_val = CoolProp.PropsSI(x_axis, y_input_name, y_input_val, "Dmass", rho, fluid_name)
                        x_list.append(x_val)
                        y_list.append(y_val)
                    except:
                        continue
                ax.plot(x_list, y_list, color=stil_isochore["farbe"], linewidth=float(stil_isochore["dicke"]), linestyle=stil_isochore["stil"],  label="_nolegend_")
                if selected_diagram.get() == "p-T-Diagramm":
                    ax.text(x_list[13], y_list[13], f'{rho:.1f} m³/kg', fontsize=9, color="black", rotation=45)
                elif selected_diagram.get()== "log(p)-h-Diagramm" :
                    mid = len(x_list) // 3
                    ax.text(x_list[mid], y_list[mid], f'{rho:.1f} m³/kg', fontsize=9, color="black", rotation=45)
                elif selected_diagram.get()== "h-s-Diagramm":
                    mid = len(x_list) // 6
                    ax.text(x_list[-mid], y_list[-mid], f'{rho:.1f} m³/kg', fontsize=9, color="black", rotation=45)
                else:
                    ax.text(x_list[-10], y_list[-10], f'{rho:.1f} m³/kg', fontsize=9, color="black", rotation=45)   
                
    
        elif isoline_type == 'isenthalpe':
            num_lines= int(stil_isenthalpe["anzahl"])
            h_vals = np.linspace(100e3, CoolProp.PropsSI("Hcrit", fluid_name), num_lines)
            for h in h_vals:
                x_list, y_list = [], []
                y_vals = np.linspace(y_range[0], y_range[1], 300)
                for y_val in y_vals:
                    try:
                        y_input_name, y_input_val = convert_axis_input(y_axis, y_val)
                        x_val = CoolProp.PropsSI(x_axis, y_input_name, y_input_val, "H", h, fluid_name)
                        x_list.append(x_val)
                        y_list.append(y_val)
                    except:
                        continue
                ax.plot(x_list, y_list, color=stil_isenthalpe["farbe"], linewidth=float(stil_isenthalpe["dicke"]), linestyle=stil_isenthalpe["stil"], label="_nolegend_")
                ax.text(x_list[-10], y_list[-10], f'{h:.1f} J/kg', fontsize=9, color="black", rotation=45)
                
        elif isoline_type == 'isovapor':
            num_lines= int(stil_isovapore["anzahl"])
            q_vals = np.linspace(0.1, 0.9, num_lines)
            T_trip = CoolProp.PropsSI("Ttriple", fluid_name)
            T_crit = CoolProp.PropsSI("Tcrit", fluid_name)
            for q in q_vals:
                x_list, y_list = [], []
                for T in np.linspace(T_trip, T_crit, 300):
                    try:
                        x_val = CoolProp.PropsSI(x_axis, "T", T, "Q", q, fluid_name)
                        y_val = CoolProp.PropsSI(y_axis if y_axis != 'V' else 'Dmass', "T", T, "Q", q, fluid_name)
                        if y_axis == 'V': y_val = 1.0 / y_val
                        x_list.append(x_val)
                        y_list.append(y_val)
                    except:
                        continue
                ax.plot(x_list, y_list, color=stil_isovapore["farbe"], linewidth=float(stil_isovapore["dicke"]), linestyle=stil_isovapore["stil"], label="_nolegend_")
                ax.text(x_list[10], y_list[10], f'{q:.1f}', fontsize=9, color="black", rotation=45)
 
    
    def check_input():
        try:
            # Alle Eingaben als Strings behandeln
            if ("," in str(eingabe1_var.get()) or
                "," in str(eingabe2_var.get()) or
                "," in minx_entry.get() or
                "," in maxx_entry.get() or
                "," in miny_entry.get() or
                "," in maxy_entry.get()):
                tkinter.messagebox.showwarning("Warnung", "Bitte einen Punkt als Komma nehmen!")
                return False
        except Exception as e:
            print(f"Fehler in check_input: {e}")
            return False
        return True
    checkbox_vars_diagramm =[isobar_var, isotherm_var, isochor_var, isentropic_var, isenthalpic_var, isovapore_var]    
    
    
    def create_figure(selected):
        #reset_isoline_checkboxes()
        update_units()
        
            
        fig = plt.Figure(figsize=(6, 4), dpi=65)
        ax = fig.add_subplot(111)
        
        T_raw = get_column_values("temperatur")
        s_raw = get_column_values("entropy")
        p_raw = get_column_values("pressure")
        h_raw = get_column_values("enthalpy")
        v_raw = get_column_values("volume")
        #convertieren in SI
        T = [convert_to_SI(t, "temperature", temp_unit) for t in T_raw]
        s = [convert_to_SI(x, "entropy", entropy_unit) for x in s_raw]
        p = [convert_to_SI(p, "pressure", pressure_unit) for p in p_raw]
        h = [convert_to_SI(h, "enthalpy", enthalpy_unit) for h in h_raw]
        v = [convert_to_SI(v, "volume", volume_unit) for v in v_raw]
        
        # T = get_column_values("temperatur")
        # s = get_column_values("entropy")
       # p = get_column_values("pressure")
       # h = get_column_values("enthalpy")
       # v = get_column_values("volume")
        
        if check_input() == False:  # Falls check_input False zurückgibt, abbrechen
            return

        minx_raw = minx_var.get()# werte des Wertebereichs des Diagrammes
        maxx_raw = maxx_var.get()
        miny_raw = miny_var.get()
        maxy_raw = maxy_var.get()
        
        
        minx=0
        maxx=0
        miny=0
        maxy=0
        
      
        if selected == "T-s-Diagramm":
            ax.clear()
            
            minx = [convert_to_SI(minx_raw, "entropy",  entropy_unit)]
            maxx = [convert_to_SI(maxx_raw, "entropy", entropy_unit)]
            miny = [convert_to_SI(miny_raw, "temperature", temp_unit)]
            maxy = [convert_to_SI(maxy_raw, "temperature", temp_unit)]
          
            
            fig = plt.Figure(figsize=(6, 4), dpi=65)
            ax = fig.add_subplot(111)
            #plot_siedetaulinien(ax, selected_fluid)
            plot_saturation_lines_general(ax, selected_fluid, diagram_type="T-s-Diagramm")
            ax.scatter(s, T, label="Daten", color=stil_daten["farbe"], marker=stil_daten["marker"], s=stil_daten["größe"] * 5, zorder=10)  # Streudiagramm da mit Norm=log etc eintragen
            ax.set_title("T-s Diagramm")
            #ax.set_xlabel("Entropie [kJ/kg·K]")
            #ax.set_ylabel("Temperatur [°C]")
            ax.set_xlabel(axis_names["entropy"])  
            ax.set_ylabel(axis_names["temperatur"])
            ax.tick_params(axis='x', labelrotation=45)
            ax.tick_params(axis='y', labelrotation=45)

            if not T or not s:  # Prüft, ob eine der Listen leer ist, bei leerer Liste gibts fehler
                T = [270, 700]  # Beispielwerte für Temperatur
                s = [0, 9000]  # Beispielwerte für Entropie
            # Berechnung der minimalen und maximalen Werte, falls noch keine Werte angegeben sind
            
            if not minx_var.get() and not maxx_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden, max und min werte des Wertebereichs der Tabelle
                minx = 0
                maxx = 9000   
            else:
                minx = float(minx[0])
                maxx = float(maxx[0])    
            if not miny_var.get() and not maxy_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden
                miny = 270
                maxy = 700  
            else:
                miny= float(miny[0])
                maxy= float(maxy[0])

            if selected_row_values: #damit ausgewählter Punkt blau wird
                temperatur_raw = float(selected_row_values[0])
                entropy_raw = float(selected_row_values[6])
                temperatur =[convert_to_SI(temperatur_raw, "temperature", temp_unit)]
                entropy= [convert_to_SI(entropy_raw, "entropy",  entropy_unit)]
                ax.scatter(entropy, temperatur, label="ausgewählt", color=stil_datenaus["farbe"], marker=stil_datenaus["marker"], s=stil_datenaus["größe"] * 5, zorder=10)
                #plt.plot(entropy, temperatur, 'ro')  # ro = red circle

            try:
                isobar_check.config(state='normal')    # aktivieren
                isotherm_check.config(state='disabled')
                isochor_check.config(state='normal')
                isentropic_check.config(state='disabled')
                isenthalpic_check.config(state='disabled')
                isovapore_check.config(state='normal')
            except Exception as e:
                 print("Error while plotting points:", e)    

             # If Checkbox is activated plot Isolines
            try:
                x_range = (float(minx), float(maxx))
                y_range = (float(miny), float(maxy))
                #print("xrange ist:", x_range, "yrange ist:", y_range)
                if isobar_var.get() == True :
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isobar', num_lines=10, x_axis='S', y_axis='T')

                if isovapore_var.get()== True :
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isovapor', num_lines=10, x_axis='S', y_axis='T')
                if isochor_var.get()== True :
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isochor', num_lines=10, x_axis='S', y_axis='T')
                    
            except Exception as e:
                print("Error while plotting points:", e)   
            
        elif selected == "log(p)-h-Diagramm":
            minx = [convert_to_SI(minx_raw, "enthalpy",  enthalpy_unit)]
            maxx = [convert_to_SI(maxx_raw, "enthalpy",  enthalpy_unit)]
            miny = [convert_to_SI(miny_raw, "pressure", pressure_unit)]
            maxy = [convert_to_SI(maxy_raw, "pressure", pressure_unit)]
            
            fig = plt.Figure(figsize=(6, 4), dpi=65)
            ax = fig.add_subplot(111)
            #plot_siedetaulinien_ph(ax, selected_fluid)
            plot_saturation_lines_general(ax, selected_fluid, diagram_type="log(p)-h-Diagramm")
            ax.scatter(h, p, label="Daten", color=stil_daten["farbe"], marker=stil_daten["marker"], s=stil_daten["größe"] * 5, zorder=10)
            ax.set_title("log(p)-h Diagramm")
            ax.set_xlabel(axis_names["enthalpy"])  
            ax.set_ylabel(axis_names["pressure"])
            
            ax.set_yscale('log')

            ax.tick_params(axis='x', labelrotation=45)
            ax.tick_params(axis='y', labelrotation=45)
            
            if not h or not p:  # Prüft, ob eine der Listen leer ist, bei leerer Liste gibts fehler
                h = [0, 3000000]  # Beispielwerte
                p = [500, 50000000]  # Beispielwerte 
            # Berechnung der minimalen und maximalen Werte, falls noch keine Werte angegeben sind
            
            if not minx_var.get() and not maxx_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden, max und min werte des Wertebereichs der Tabelle
                minx = 0
                maxx = 3000000
            else:
                minx = float(minx[0])
                maxx = float(maxx[0])  
            if not miny_var.get() and not maxy_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden
                miny = 500
                maxy = 50000000
            else:
                miny = float(miny[0])
                maxy = float(maxy[0])
                
           
            if selected_row_values: #damit ausgewählter Punkt blau wird
                enthalpy_raw = float(selected_row_values[5])
                pressure_raw = float(selected_row_values[1])
                enthalpy =[convert_to_SI(enthalpy_raw, "enthalpy", enthalpy_unit)]
                pressure =[convert_to_SI(pressure_raw, "pressure", pressure_unit)]
                ax.scatter(enthalpy, pressure, label="ausgewählt", color=stil_datenaus["farbe"], marker=stil_datenaus["marker"], s=stil_datenaus["größe"] * 5, zorder=10)
                #plt.plot(entropy, temperatur, 'ro')  # ro = red circl
        
            try:
                isobar_check.config(state='disabled')    # aktivieren
                isotherm_check.config(state='normal')
                isochor_check.config(state='normal')
                isentropic_check.config(state='normal')
                isenthalpic_check.config(state='disabled')
                isovapore_check.config(state='normal')

            except:
                pass
            
            try:
                x_range = (float(minx), float(maxx))
                y_range = (float(miny), float(maxy))

                if isentropic_var.get()==True:

                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isentrope', num_lines=10, x_axis='H', y_axis='P')
                if isotherm_var.get()==True:

                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isotherm', num_lines=10, x_axis='H', y_axis='P')
                if isovapore_var.get()==True:

                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isovapor', num_lines=10, x_axis='H', y_axis='P')
                if isochor_var.get()==True:

                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isochor', num_lines=10, x_axis='H', y_axis='P')
            except:
                pass 

            
            
        elif selected == "h-s-Diagramm":
            miny = [convert_to_SI(miny_raw, "enthalpy",  enthalpy_unit)]
            maxy = [convert_to_SI(maxy_raw, "enthalpy",  enthalpy_unit)]
            minx = [convert_to_SI(minx_raw, "entropy", entropy_unit)]
            maxx = [convert_to_SI(maxx_raw, "entropy", entropy_unit)]
            
            fig = plt.Figure(figsize=(6, 4), dpi=65)
            ax = fig.add_subplot(111)
            plot_saturation_lines_general(ax, selected_fluid, diagram_type="h-s-Diagramm")
            #plot_siedetaulinien_hs(ax, selected_fluid)
            
            ax.scatter(s, h, label="Daten",color=stil_daten["farbe"], marker=stil_daten["marker"], s=stil_daten["größe"] * 5, zorder=10)
            ax.set_title("h-s Diagramm")
            ax.set_xlabel(axis_names["entropy"])  
            ax.set_ylabel(axis_names["enthalpy"])

            ax.tick_params(axis='x', labelrotation=45)
            ax.tick_params(axis='y', labelrotation=45)
            if not s or not h:  # Prüft, ob eine der Listen leer ist, bei leerer Liste gibts fehler
                h = [0, 3000000]  # Beispielwerte
                s = [0, 9200]  # Beispielwerte 
            # Berechnung der minimalen und maximalen Werte, falls noch keine Werte angegeben sind
            
            if not minx_var.get() and not maxx_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden, max und min werte des Wertebereichs der Tabelle
                minx = 0
                maxx = 9200
            else:
                minx = float(minx[0])
                maxx = float(maxx[0]) 
            if not miny_var.get() and not maxy_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden
                miny = 0
                maxy = 3000000
            else:
                miny = float(miny[0])
                maxy = float(maxy[0])
                
            
            if selected_row_values: #damit ausgewählter Punkt blau wird           
                enthalpy_raw = float(selected_row_values[5])
                entropy_raw = float(selected_row_values[6])
                enthalpy =[convert_to_SI(enthalpy_raw, "enthalpy",  enthalpy_unit)]
                entropy =[convert_to_SI(entropy_raw, "entropy",  entropy_unit)]
                ax.scatter(entropy, enthalpy,label="ausgewählt",color=stil_datenaus["farbe"], marker=stil_datenaus["marker"], s=stil_datenaus["größe"] * 5, zorder=10)
                #plt.plot(entropy, temperatur, 'ro')  # ro = red circlv

            try:
                isobar_check.config(state='normal')    # aktivieren
                isotherm_check.config(state='normal')
                isochor_check.config(state='normal')
                isentropic_check.config(state='disabled')
                isenthalpic_check.config(state='disabled')
                isovapore_check.config(state='normal')

            except:
                pass
            
            try:
                x_range = (float(minx), float(maxx))
                y_range = (float(miny), float(maxy))
                if isobar_var.get()==True:
                   # generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isobar', num_lines=10)
                   generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                       isoline_type='isobar', num_lines=10, x_axis='S', y_axis='H')
                if isotherm_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isotherm', num_lines=10) 
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isotherm', num_lines=10, x_axis='S', y_axis='H')
                if isovapore_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isovapor', num_lines=10)
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isovapor', num_lines=10, x_axis='S', y_axis='H')
                if isochor_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isochor', num_lines=10)
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isochor', num_lines=10, x_axis='S', y_axis='H')

            except:
                pass
            
        
            
        elif selected == "p-T-Diagramm":
            minx = [convert_to_SI(minx_raw, "temperature", temp_unit)]
            maxx = [convert_to_SI(maxx_raw, "temperature", temp_unit)]
            miny = [convert_to_SI(miny_raw, "pressure", pressure_unit)]
            maxy = [convert_to_SI(maxy_raw, "pressure", pressure_unit)]

            fig = plt.Figure(figsize=(6, 4), dpi=65)
            ax = fig.add_subplot(111)
            #plot_saturation_lines(ax, selected_fluid)
            plot_saturation_lines_general(ax, selected_fluid, diagram_type="p-T-Diagramm")
            ax.scatter(T, p, label="Daten", color=stil_daten["farbe"], marker=stil_daten["marker"], s=stil_daten["größe"] * 5, zorder=10)
            ax.set_title("p-T Diagramm")
            ax.set_xlabel(axis_names["temperatur"])  
            ax.set_ylabel(axis_names["pressure"])

            ax.tick_params(axis='x', labelrotation=45)
            ax.tick_params(axis='y', labelrotation=45)
            if not T or not p:  # Prüft, ob eine der Listen leer ist, bei leerer Liste gibts fehler
                T = [200, 650]  # Beispielwerte
                p = [0, 23000000]  # Beispielwerte 
            # Berechnung der minimalen und maximalen Werte, falls noch keine Werte angegeben sind
            
            if not minx_var.get() and not maxx_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden, max und min werte des Wertebereichs der Tabelle
                minx = 200
                maxx = 650
            else:
                minx = float(minx[0])
                maxx = float(maxx[0])  
            if not miny_var.get() and not maxy_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden
                miny = 0
                maxy = 23000000
            else:
                miny = float(miny[0])
                maxy = float(maxy[0])
                
           
            if selected_row_values: #damit ausgewählter Punkt blau wird           
                temperatur_raw = float(selected_row_values[0])
                pressure_raw = float(selected_row_values[1])
                temperatur =[convert_to_SI(temperatur_raw, "temperature", temp_unit)]
                pressure = [convert_to_SI(pressure_raw, "pressure",  pressure_unit)] 
                ax.scatter(temperatur, pressure, label="ausgewählt", color=stil_datenaus["farbe"], marker=stil_datenaus["marker"], s=stil_datenaus["größe"] * 5, zorder=10)
                #plt.plot(entropy, temperatur, 'ro')  # ro = red circl
            
            try:
                isobar_check.config(state='disabled')    # aktivieren
                isotherm_check.config(state='disabled')
                isochor_check.config(state='normal')
                isentropic_check.config(state='disabled')
                isenthalpic_check.config(state='disabled')
                isovapore_check.config(state='disabled')
                

            except:
                pass
            
            try:
                x_range = (float(minx), float(maxx))
                y_range = (float(miny), float(maxy))
                if isochor_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isochor', num_lines=10)
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isochor', num_lines=10, x_axis='T', y_axis='P')
            except:
                pass
            
        elif selected == "T-v-Diagramm":
            minx = [convert_to_SI(minx_raw, "volume", volume_unit)]
            maxx = [convert_to_SI(maxx_raw, "volume", volume_unit)]
            miny = [convert_to_SI(miny_raw, "temperature", temp_unit)]
            maxy = [convert_to_SI(maxy_raw, "temperature", temp_unit)]
            
            fig = plt.Figure(figsize=(6, 4), dpi=65)
            ax = fig.add_subplot(111)
            #plot_boiling_and_dew_lines(ax, selected_fluid)
            plot_saturation_lines_general(ax, selected_fluid, diagram_type="T-v-Diagramm")
            ax.scatter(v, T, label="Daten", color=stil_daten["farbe"], marker=stil_daten["marker"], s=stil_daten["größe"] * 5, zorder=10)
            ax.set_xscale('log')
            ax.set_title("T-v Diagramm")
            ax.set_xlabel(axis_names["volume"])  
            ax.set_ylabel(axis_names["temperatur"])

            ax.tick_params(axis='x', labelrotation=45)
            ax.tick_params(axis='y', labelrotation=45)
            if not T or not v:  # Prüft, ob eine der Listen leer ist, bei leerer Liste gibts fehler
                T = [200, 700]  # Beispielwerte
                v = [0.001, 1000 ]  # Beispielwerte 
            # Berechnung der minimalen und maximalen Werte, falls noch keine Werte angegeben sind
            
            if not minx_var.get() and not maxx_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden, max und min werte des Wertebereichs der Tabelle
                minx = 0.0001
                maxx = 1000
            else:
                minx = float(minx[0])
                maxx = float(maxx[0])  
            if not miny_var.get() and not maxy_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden
                miny = 200
                maxy = 700
            else:
                miny = float(miny[0])
                maxy = float(maxy[0])
                
            
            if selected_row_values: #damit ausgewählter Punkt blau wird
                volume_raw = float(selected_row_values[3])
                temperatur_raw = float(selected_row_values[0])
                volume = [convert_to_SI(volume_raw, "volume",  volume_unit)] 
                temperatur =[convert_to_SI(temperatur_raw, "temperature", temp_unit)]
                ax.scatter(volume, temperatur,label="ausgewählt", color=stil_datenaus["farbe"], marker=stil_datenaus["marker"], s=stil_datenaus["größe"] * 5, zorder=10)
                #plt.plot(entropy, temperatur, 'ro')  # ro = red circl
            
            
            try:
                isobar_check.config(state='normal')    # aktivieren
                isotherm_check.config(state='disabled')
                isochor_check.config(state='disabled')
                isentropic_check.config(state='disabled')
                isenthalpic_check.config(state='disabled')
                isovapore_check.config(state='disabled')
                
        
            except:
                pass
            
            try:
                x_range = (float(minx), float(maxx))
                y_range = (float(miny), float(maxy))
                if isobar_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isobar', num_lines=10) 
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isobar', num_lines=10, x_axis='V', y_axis='T')
                
            except:
                pass 
        
        elif selected == "p-v-Diagramm":
            minx = [convert_to_SI(minx_raw, "volume", volume_unit)]
            maxx = [convert_to_SI(maxx_raw, "volume", volume_unit)]
            miny = [convert_to_SI(miny_raw, "pressure", pressure_unit)]
            maxy = [convert_to_SI(maxy_raw, "pressure", pressure_unit)]
            
            fig = plt.Figure(figsize=(6, 4), dpi=65)
            ax = fig.add_subplot(111)
            #plot_boiling_and_dew_lines_pv(ax, selected_fluid)
            plot_saturation_lines_general(ax, selected_fluid, diagram_type="p-v-Diagramm")
            ax.scatter(v, p, label="Daten", color=stil_daten["farbe"], marker=stil_daten["marker"], s=stil_daten["größe"] * 5, zorder=10)
            ax.set_xscale('log')
            ax.set_title("p-v Diagramm")
            ax.set_xlabel(axis_names["volume"])  
            ax.set_ylabel(axis_names["pressure"])
            
            ax.tick_params(axis='x', labelrotation=45)
            ax.tick_params(axis='y', labelrotation=45)
            if not p or not v:  # Prüft, ob eine der Listen leer ist, bei leerer Liste gibts fehler
                p = [0, 23000000]  # Beispielwerte
                v = [0.001, 1000 ]  # Beispielwerte 
            # Berechnung der minimalen und maximalen Werte, falls noch keine Werte angegeben sind
            
            if not minx_var.get() and not maxx_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden, max und min werte des Wertebereichs der Tabelle
                minx = 0.0001
                maxx = 1000
            else:
                minx = float(minx[0])
                maxx = float(maxx[0]) 
            if not miny_var.get() and not maxy_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden
                miny = 0
                maxy = 23000000
            else:
                miny =float(miny[0])
                maxy = float(maxy[0])
                
            
            if selected_row_values: #damit ausgewählter Punkt blau wird
                volume_raw = float(selected_row_values[3])
                pressure_raw = float(selected_row_values[1])
                volume = [convert_to_SI(volume_raw, "volume",  volume_unit)]
                pressure = [convert_to_SI(pressure_raw, "pressure", pressure_unit)]
                ax.scatter(volume, pressure, label="ausgewählt", color=stil_datenaus["farbe"], marker=stil_datenaus["marker"], s=stil_datenaus["größe"] * 5, zorder=10)
                #plt.plot(entropy, temperatur, 'ro')  # ro = red circl
            
            
            try:
                isobar_check.config(state='disabled')    # aktivieren
                isotherm_check.config(state='normal')
                isochor_check.config(state='disabled')
                isentropic_check.config(state='disabled')
                isenthalpic_check.config(state='disabled')
                isovapore_check.config(state='disabled')
                
        
            except:
                pass
            
            try:
                x_range = (float(minx), float(maxx))
                y_range = (float(miny), float(maxy))
                
                if isotherm_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isovapore', num_lines=10)
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isotherm', num_lines=10, x_axis='V', y_axis='P')
                
            except:
                pass 

        # --- X-ACHSE ---
        if minx == maxx:
            minx -= 0.5
            maxx += 0.5
        if miny == maxy:
            miny -= 0.5
            maxy += 0.5
        
        ax.set_xlim(minx, maxx )
        ax.set_ylim(miny , maxy)
        
        if ax.get_xscale() == 'log':
            ax.set_xscale('log')
            
            ax.xaxis.set_major_locator(LogLocator(base=10.0, numticks=10))
            ax.xaxis.set_major_formatter(LogFormatter(base=10.0))
            ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs='auto', numticks=10))
            
            # ax.xaxis.set_major_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=10))
            # ax.xaxis.set_major_formatter(LogFormatter(base=10.0))
            # ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(1.1, 10, 1) * 0.1, numticks=10))
            xticks = ax.get_xticks()
         
        else:
            x_step = calculate_step_size(minx, maxx)
            xticks = np.arange(minx, maxx + x_step, x_step)
            ax.set_xticks(xticks)
            ax.xaxis.set_minor_locator(AutoMinorLocator())
         
        
        # --- Y-ACHSE ---
        if ax.get_yscale() == 'log':
            ax.set_yscale('log')
            ax.yaxis.set_major_locator(LogLocator(base=10.0, numticks=10))
            ax.yaxis.set_major_formatter(LogFormatter(base=10.0))
            ax.yaxis.set_minor_locator(LogLocator(base=10.0, subs='auto', numticks=10))
            yticks = ax.get_yticks()
        
        else:
            y_step = calculate_step_size(miny, maxy)
            yticks = np.arange(miny, maxy + y_step, y_step)
            ax.set_yticks(yticks)
            ax.yaxis.set_minor_locator(AutoMinorLocator())
        

        if selected == "T-s-Diagramm":
            xtick_labels = [round(convert_from_SI(val, "entropy", entropy_unit),1) for val in xticks]
            ytick_labels = [round(convert_from_SI(val, "temperature", temp_unit),1) for val in yticks]
        elif selected == "log(p)-h-Diagramm":
            xtick_labels = [round(convert_from_SI(val, "enthalpy", enthalpy_unit),1) for val in xticks]
            ytick_labels = [round(convert_from_SI(val, "pressure", pressure_unit),1) for val in yticks]
            print("yticks=", yticks)
        elif selected == "h-s-Diagramm":
            xtick_labels = [round(convert_from_SI(val, "entropy", entropy_unit),1) for val in xticks]
            ytick_labels = [round(convert_from_SI(val, "enthalpy", enthalpy_unit),1) for val in yticks]
        elif selected == "p-T-Diagramm":
            xtick_labels = [round(convert_from_SI(val, "temperature", temp_unit),1) for val in xticks]
            ytick_labels = [round(convert_from_SI(val, "pressure", pressure_unit),1) for val in yticks]
        elif selected == "T-v-Diagramm":
            xtick_labels = [round(convert_from_SI(val, "volume", volume_unit),1) for val in xticks]
            ytick_labels = [round(convert_from_SI(val, "temperature", temp_unit),1) for val in yticks]
        elif selected == "p-v-Diagramm":
            xtick_labels = [round(convert_from_SI(val, "volume", volume_unit),1) for val in xticks]
            ytick_labels = [round(convert_from_SI(val, "pressure", pressure_unit),1) for val in yticks]
        else :
            xtick_labels = xticks
            ytick_labels = yticks

        # if ax.get_xscale() != 'log':
        #     ax.set_xticklabels(xtick_labels, rotation=45)

        # if ax.get_yscale() != 'log':
        #     ax.set_yticklabels(ytick_labels, rotation=45)
        
        def custom_formatter(unit, label_func):
            def formatter(val, pos):
                converted = label_func(val, unit)
                if abs(converted) >= 10000 or abs(converted) < 0.01:
                    return f"{converted:.0e}"
                else:
                    return f"{converted:.4f}".rstrip("0").rstrip(".")
            return FuncFormatter(formatter)
        
        # X-Achse
        if ax.get_xscale() == 'log':
            if selected == "log(p)-h-Diagramm":
                ax.xaxis.set_major_formatter(custom_formatter(enthalpy_unit, lambda v, u: convert_from_SI(v, "enthalpy", u)))
            elif selected == "T-v-Diagramm":
                ax.xaxis.set_major_formatter(custom_formatter(volume_unit, lambda v, u: convert_from_SI(v, "volume", u)))
            elif selected == "p-v-Diagramm":
                ax.xaxis.set_major_formatter(custom_formatter(volume_unit, lambda v, u: convert_from_SI(v, "volume", u)))
            
        else:
            ax.set_xticklabels(xtick_labels, rotation=45)
        
        # Y-Achse
        if ax.get_yscale() == 'log':
            if selected == "log(p)-h-Diagramm":
                ax.yaxis.set_major_formatter(custom_formatter(pressure_unit, lambda v, u: convert_from_SI(v, "pressure", u)))
            elif selected == "T-v-Diagramm":
                ax.yaxis.set_major_formatter(custom_formatter(temp_unit, lambda v, u: convert_from_SI(v, "temperature", u)))
            elif selected == "p-v-Diagramm":
                ax.yaxis.set_major_formatter(custom_formatter(pressure_unit, lambda v, u: convert_from_SI(v, "pressure", u)))
   
            
        else:
            ax.set_yticklabels(ytick_labels, rotation=45)
            

        # Gitterlinien aktivieren und an die Ticks anpassen
        ax.grid(True, which='major', axis='both', linestyle='--', color='gray', linewidth=0.5)
        ax.grid(True, which='minor', axis='both', linestyle='--', color='lightgray', linewidth=0.5)
        handles, labels = ax.get_legend_handles_labels()
        print(legende_set.get())
        # if handles and legende_set.get() == True:
        #     print("Legende in create_figure")
        #     ax.legend() 
        if handles and legende_set.get():
            print("Legende in create_figure")
            ax.legend()
        margins = get_subplot_settings()
        fig.subplots_adjust(
            left=margins["left"],
            right=margins["right"],
            top=margins["top"],
            bottom=margins["bottom"]
        )

        # fig.subplots_adjust(left=load_subplot_settings[left_var], right=0.9, top=0.94, bottom=0.17)    #15% vom linken rand entfernt und 0.1 vom rechten entfernt

        return fig, ax  # Rückgabe der Figure und Axes
    
    class CursorAnnotation:
        def __init__(self, ax, diagram_type):
            self.ax = ax
            self.diagram_type = diagram_type  # z. B. "T-s-Diagramm"
            self.annotation = ax.annotate('', xy=(0, 0), xytext=(10, -10), textcoords='offset points', bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"), zorder=11)
            self.annotation.set_visible(False)
    
        def update(self, event):
            global x_SI, y_SI
            if event.inaxes == self.ax:
                x, y = event.xdata, event.ydata
                #print ("In Class x=", x, "y=", y)
                if x is not None and y is not None:
                    mouse_x_px = event.x
                    mouse_y_px = event.y
                    
                    canvas_width, canvas_height = event.canvas.get_width_height()
    
                    offset_x = 20
                    offset_y = 20
    
                    if mouse_x_px > canvas_width * 0.6:
                        offset_x = -110
                    if mouse_y_px < canvas_height * 0.35:
                        offset_y = 40
                    elif mouse_y_px > canvas_height * 0.8:
                        offset_y = -36
    
                    self.annotation.set_position((offset_x, offset_y))
                    self.annotation.xy = (x, y)
                    
                    selected=selected_diagram.get()
                    if selected == "T-s-Diagramm":
                        x_SI = round(convert_from_SI(x, "entropy", entropy_unit),4) 
                        y_SI = round(convert_from_SI(y, "temperature", temp_unit),4)
                    elif selected == "log(p)-h-Diagramm":
                        x_SI = round(convert_from_SI(x, "enthalpy", enthalpy_unit),4) 
                        y_SI = round(convert_from_SI(y, "pressure", pressure_unit),4) 
                    elif selected == "h-s-Diagramm":
                        x_SI = round(convert_from_SI(x, "entropy", entropy_unit),4)
                        y_SI = round(convert_from_SI(y, "enthalpy", enthalpy_unit),4) 
                    elif selected == "p-T-Diagramm":
                        x_SI = round(convert_from_SI(x, "temperature", temp_unit),4)
                        y_SI = round(convert_from_SI(y, "pressure", pressure_unit),4) 
                    elif selected == "T-v-Diagramm":
                        x_SI = round(convert_from_SI(x, "volume", volume_unit),4) 
                        y_SI = round(convert_from_SI(y, "temperature", temp_unit),4) 
                    elif selected == "p-v-Diagramm":
                        x_SI = round(convert_from_SI(x, "volume", volume_unit),4) 
                        y_SI = round(convert_from_SI(y, "pressure", pressure_unit),4)
                    else :
                        x_SI = x
                        y_SI = y
                    #print ("In Class x_SI=", x_SI, "y_SI=", y_SI)
    
                    # Umrechnung + Einheiten
                    # x_label, x_unit, x_val = self.get_axis_info(x, axis='x')
                    # y_label, y_unit, y_val = self.get_axis_info(y, axis='y')
                    x_label, x_unit, x_val = self.get_axis_info(x, axis='x', convert=True)
                    y_label, y_unit, y_val = self.get_axis_info(y, axis='y', convert=True)
    
                    self.annotation.set_text(f"{x_label} = {x_val:.3f} {x_unit}\n{y_label} = {y_val:.2f} {y_unit}")
                    self.annotation.set_visible(True)
                    event.canvas.draw()
                else:
                    self.annotation.set_visible(False)
                    event.canvas.draw()
            else:
                # Tooltip ausblenden, wenn Maus außerhalb des Diagramms
                self.annotation.set_visible(False)
                event.canvas.draw()

        def get_axis_info(self, value, axis='x', convert=True):
            mapping = {
                "T-s-Diagramm": {'x': ('s', 'entropy', entropy_unit), 'y': ('T', 'temperature', temp_unit)},
                "log(p)-h-Diagramm": {'x': ('h', 'enthalpy', enthalpy_unit), 'y': ('p', 'pressure', pressure_unit)},
                "h-s-Diagramm": {'x': ('s', 'entropy', entropy_unit), 'y': ('h', 'enthalpy', enthalpy_unit)},
                "p-T-Diagramm": {'x': ('T', 'temperature', temp_unit), 'y': ('p', 'pressure', pressure_unit)},
                "T-v-Diagramm": {'x': ('v', 'volume', volume_unit), 'y': ('T', 'temperature', temp_unit)},
                "p-v-Diagramm": {'x': ('v', 'volume', volume_unit), 'y': ('p', 'pressure', pressure_unit)},
            }
        
            label, typ, unit = mapping.get(self.diagram_type, {}).get(axis, (axis, None, ''))
        
            if typ is not None and convert:
                value_converted = convert_from_SI(value, typ, unit)
            else:
                value_converted = value
        
            return label, unit, value_converted

    
    def on_move(event):
        cursor_annotation.update(event)
       


    def show_diagram(*args):
        global current_ax, current_canvas, canvas_widget, fig, cursor_annotation
        update_units()
        # Vorherigen Plot löschen
        for widget in diagram_canvas_frame.winfo_children():
            widget.destroy()

        for widget in toolbar_frame.winfo_children():
            widget.destroy()

        # Größe des Frames holen (in Pixeln)
        diagram_canvas_frame.update_idletasks()
        frame_width = diagram_canvas_frame.winfo_width()
        frame_height = diagram_canvas_frame.winfo_height()

        #print(f"Frame size: {frame_width} x {frame_height}")  # Debugging-Ausgabe

        # Falls noch 1x0 bei Start, Fallback-Werte setzen
        if frame_width < 1 or frame_height < 1:
            frame_width, frame_height = 250, 250  # Defaultwerte

        # DPI für Matplotlib
        dpi = 100

        # Berechne die Größe der Matplotlib-Figur in Zoll
        fig_width_inch = frame_width / dpi
        fig_height_inch = frame_height / dpi

        #print(f"Figure size in inches: {fig_width_inch} x {fig_height_inch}")  # Debugging-Ausgabe

        # Holen der Auswahl, z.B. von einem Dropdown oder einer Auswahlbox
        selected = selected_diagram.get()  # Hier wird die Auswahl verwendet

        # Erstellen der Figure mit den ausgewählten Daten
        fig, ax = create_figure(selected)

        # Das Diagramm im Canvas rendern
        canvas = FigureCanvasTkAgg(fig, master=diagram_canvas_frame)
        canvas.draw()

        # Canvas im Frame anzeigen und Größe setzen
        canvas_widget = canvas.get_tk_widget()

        # Hier wird explizit die Canvas-Größe gesetzt
        canvas_widget.config(width=frame_width, height=frame_height)
        
        # Sicherstellen, dass der Canvas den gesamten Frame ausfüllt
        canvas_widget.pack(fill='both', expand=True)
        #canvas_widget.grid(row=0, column=0, padx=20, pady=1, sticky="e")
        #canvas_widget.place(x=0, y=0, width=frame_width-10, height=frame_height-10)
        units_dict = {
            "temperature": temp_unit,
            "pressure": pressure_unit,
            "volume": volume_unit,
            "entropy": entropy_unit,
            "enthalpy": enthalpy_unit
            }
        cursor_annotation = CursorAnnotation(fig.gca(), selected_diagram.get())
         # # Verbinde die Funktion mit dem Mausbewegungs-Event
        fig.canvas.mpl_connect('motion_notify_event', on_move)
        
        # Toolbar hinzufügen
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame, pack_toolbar=False)
        toolbar.update()
        toolbar.grid(row=0, column=0, sticky="W")
        
        if hasattr(canvas, "toolbar"): #damit in der Toolbar die Koordinaten nicht mehr angezeigt werden
            canvas.toolbar.set_message = lambda s: None
        
        cid = fig.canvas.mpl_connect("button_press_event", mouse_event)
        #cid = fig.canvas.mpl_connect("motion_notify_event", mouse_event1)
        
        current_ax = ax
        current_canvas = canvas
        
        
    entry_fields = [minx_entry, miny_entry, maxx_entry, maxy_entry]
    
    def on_select_legend():
        print("Legende testen", legende_var.get())
        global legende_set
        if legende_var.get():
            print("Legende aktivieren", legende_var.get())
            legende_set.set(True)
        else:
                legende_set.set(False)
        show_diagram()
    
    def new_diagram(event=None):
        for var in checkbox_vars_diagramm:  # Liste von BooleanVar(), z. B.
            var.set(False)
        for entry in entry_fields:  # Liste vorher definieren!
            entry.delete(0, tk.END)
            entry.insert(0, "0")
        show_diagram()
        
    legende_check = tk.Checkbutton(diagram_frame, text="Legende", variable=legende_var, onvalue=True, offvalue=False, command=on_select_legend)
    legende_check.grid(row=0, column=0, padx=(220,0), sticky = "W")
        
    # Event-Handler für Auswahländeru
    diagram_combobox.bind("<<ComboboxSelected>>", new_diagram)

    diagram_canvas_frame = ttk.Frame(diagram_frame,width=300, height=300)
    diagram_canvas_frame.grid(row=1, column=0, pady=5, columnspan=1, rowspan=7, sticky="W")
    diagram_canvas_frame.grid_propagate(False)  # Verhindert automatische Größenanpassung des Frames

    # Direkt beim Start Diagramm anzeigen
    show_diagram()
    


    def on_click(event):
         if event.button is MouseButton.LEFT:
             print('disconnecting callback')
             plt.disconnect(binding_id)


    binding_id = plt.connect('motion_notify_event', on_move)
    plt.connect('button_press_event', on_click)

    


    #Berechnungen-------------------------------------------------------------------
    
    # Berechnung to the Labels
    calc_temp=0
    calc_s=0
    calc_p=0
    calc_h=0
    calc_d=0
    

    def calcw():
        global mouse_event_triggered
        
        fluid_info(selected_fluid)#setzt Fluidinfo
        #for item in tree.get_children():#löscht tree
           #tree.delete(item)
        if not mouse_event_triggered:
            for item in tree.get_children():
                tree.delete(item)
    
        mouse_event_triggered = False  # zurücksetzen für nächsten Durchlauf
        
    
       
        if check_input() == False:  # Falls check_input False zurückgibt, abbrechen
            return
    
        try:
            variable1 = selected_variable1.get()
            variable2 = selected_variable2.get()
            
            step = float(schritte_num.get())
            


            if variable1 == "Temperatur T":
                start_value = convert_to_SI(float(wertemin_num.get()), "temperature", temp_unit)
                end_value = convert_to_SI(float(wertemax_num.get()), "temperature", temp_unit)
                if temp_unit == "Fahrenheit":
                    step = step * 5/9  # Umrechnung von °F-Schrittgröße zu K
                elif temp_unit == "Rankine":
                    step = step * 5/9  # Umrechnung von °R-Schrittgröße zu K
            elif variable1 == "Druck p":
                start_value = convert_to_SI(float(wertemin_num.get()),"pressure", pressure_unit)
                end_value = convert_to_SI(float(wertemax_num.get()), "pressure",pressure_unit)
                step = convert_to_SI(float(schritte_num.get()), "pressure",pressure_unit)
            elif variable1 == "Dichte rho":
                start_value = convert_to_SI(float(wertemin_num.get()), "density", density_unit)
                end_value = convert_to_SI(float(wertemax_num.get()), "density", density_unit)
                step = convert_to_SI(float(schritte_num.get()), "density", density_unit)
            elif variable1 == "Spezifische Enthalpie h":
                start_value = convert_to_SI(float(wertemin_num.get()), "enthalpy", enthalpy_unit)
                end_value = convert_to_SI(float(wertemax_num.get()),"enthalpy", enthalpy_unit)
                step = convert_to_SI(float(schritte_num.get()), "enthalpy", enthalpy_unit)
            elif variable1 == "Spezifische Entropie s":
                start_value = convert_to_SI(float(wertemin_num.get()), "entropy", entropy_unit)
                end_value = convert_to_SI(float(wertemax_num.get()),"entropy", entropy_unit)
                step = convert_to_SI(float(schritte_num.get()), "entropy", entropy_unit)
            elif variable1 == "Innere Energie u":
                start_value = convert_to_SI(float(wertemin_num.get()), "internal_energy", i_energy_unit)
                end_value = convert_to_SI(float(wertemax_num.get()), "internal_energy", i_energy_unit)
                step = convert_to_SI(float(schritte_num.get()), "internal_energy", i_energy_unit)
            elif variable1 == "Cp":
                start_value = convert_to_SI(float(wertemin_num.get()), "cp", cp_unit)
                end_value = convert_to_SI(float(wertemax_num.get()),"cp", cp_unit)
                step = convert_to_SI(float(schritte_num.get()), "cp", cp_unit)
            elif variable1 == "Cv":
                start_value = convert_to_SI(float(wertemin_num.get()),"cv", cv_unit)
                end_value = convert_to_SI(float(wertemax_num.get()),"cv", cv_unit)
                step = convert_to_SI(float(schritte_num.get()), "cv", cv_unit)
            elif variable1 == "Volumen v":
                start_value = convert_to_SI(float(wertemin_num.get()), "volume", volume_unit)
                end_value = convert_to_SI(float(wertemax_num.get()),"volume",volume_unit)
                step = convert_to_SI(float(schritte_num.get()), "volume",volume_unit)

            else:
                #inconst_value = float(eingabe1_var.get())
                start_value = float(wertemin_num.get())
                end_value = float(wertemax_num.get())
                step = float(schritte_num.get()) 
            
            if variable2 == "Temperatur T":
                const_value = convert_to_SI(float(eingabe2_var.get()), "temperature", temp_unit)
            elif variable2 == "Druck p":
                const_value = convert_to_SI(float(eingabe2_var.get()), "pressure", pressure_unit)
            elif variable2 == "Dichte rho":
                const_value = convert_to_SI(float(eingabe2_var.get()), "density", density_unit)
            elif variable2 == "Spezifische Enthalpie h":
                const_value = convert_to_SI(float(eingabe2_var.get()),"enthalpy", enthalpy_unit)
            elif variable2 == "Spezifische Entropie s":
                const_value = convert_to_SI(float(eingabe2_var.get()),"entropy", entropy_unit)
            elif variable2 == "Innere Energie u":
                const_value = convert_to_SI(float(eingabe2_var.get()),"internal_energy", i_energy_unit)
            elif variable2 == "Cp":
                const_value = convert_to_SI(float(eingabe2_var.get()),"cp", cp_unit)
            elif variable2 == "Cv":
                const_value = convert_to_SI(float(eingabe2_var.get()),"cv", cv_unit)
            elif variable2 == "Volumen v":
                const_value = convert_to_SI(float(eingabe2_var.get()),"volume",volume_unit)
            else:
                const_value = float(eingabe2_var.get())
                
            
             
            
            current_value = start_value  
            print (eingabe1_var)
            if variable1 == variable2:
                tkinter.messagebox.showwarning("Warnung", "Bitte zwei unterschiedliche Variablen zur Berechnung wählen!")
                return

            elif (variable1, variable2) in [("Spezifische Enthalpie h", "Temperatur T"), ("Temperatur T", "Spezifische Enthalpie h"), 
                                            ("Spezifische Entropie s", "Dampfqualität x"), ("Dampfqualität x", "Spezifische Entropie s"),
                                            ("Innere Energie u", "Temperatur T"),("Temperatur T","Innere Energie u" ),
                                            ("Innere Energie u", "Spezifische Enthalpie h"),("Spezifische Enthalpie h","Innere Energie u" ),
                                            ("Innere Energie u", "Spezifische Entropie s"),("Spezifische Entropie s","Innere Energie u" ),
                                            ("Innere Energie u", "Dampfqualität x"),("Dampfqualität x","Innere Energie u" ),
                                            ("Volumen v", "Dichte rho"), ("Dichte rho", "Volumen v"),
                                            ("Spezifische Enthalpie h", "Dampfqualität x"), ("Dampfqualität x", "Spezifische Enthalpie h")]:
                tkinter.messagebox.showwarning("Warnung", "Dieses Paar von Eingabevariablen ist nicht möglich! Bitte eine andere Kombination wählen.")
                return
            elif step <= 0:
                tkinter.messagebox.showwarning("Warnung", "Die Schrittweite muss größer als 0 sein!")
                return
            elif start_value > end_value:
                tkinter.messagebox.showwarning("Warnung", "Der Startwert ist größer als der Endwert!")
                return
            else:
                input1_code = get_input_code(variable1)
                input2_code = get_input_code(variable2)
                
            if not check_limitsw(variable1, variable2, start_value, const_value, end_value, maxtemp, mfloatemp, maxp, minp):
                return    
                
            if variable1 == "Volumen v":    # v umrechnen dass damit auch als eingabe gerechnet werden kann
                #helpdensity = 1/eingabe1_var.get()
                input1_code = "D"
                #inconst_value = helpdensity
                start_value = 1/start_value
                end_value = 1/end_value
                const_value = 1/const_value
            elif variable2 == "Volumen v":
                #helpdensity = 1/eingabe2_var.get()
                input2_code = "D"
                #const_value = helpdensity
                const_value = 1/const_value
                
                
                
                
            while current_value <= end_value:
                print(current_value, end_value)
                try:
                    calc_temp = CoolProp.PropsSI("T", input1_code, current_value, input2_code, const_value, selected_fluid.get())
                    calc_p = CoolProp.PropsSI("P", input1_code, current_value, input2_code, const_value, selected_fluid.get())                                    
                    calc_d = CoolProp.PropsSI("D", input1_code, current_value, input2_code, const_value, selected_fluid.get())
                    calc_h = CoolProp.PropsSI("H", input1_code, current_value, input2_code, const_value, selected_fluid.get())
                    calc_s = CoolProp.PropsSI("S", input1_code, current_value, input2_code, const_value, selected_fluid.get())
                    calc_x = CoolProp.PropsSI("Q", input1_code, current_value, input2_code, const_value, selected_fluid.get())*100
                    calc_u = CoolProp.PropsSI("U", input1_code, current_value, input2_code, const_value, selected_fluid.get())
                    calc_vis = CoolProp.PropsSI("V", input1_code, current_value, input2_code, const_value, selected_fluid.get())
                    calc_cp = CoolProp.PropsSI("CPMASS", input1_code, current_value, input2_code, const_value, selected_fluid.get())
                    calc_cv = CoolProp.PropsSI("CVMASS", input1_code, current_value, input2_code, const_value, selected_fluid.get())
                    calc_v = 1/ (CoolProp.PropsSI("D", input1_code, current_value, input2_code, const_value, selected_fluid.get()))
                    calc_state = CoolProp.PropsSI("PHASE", input1_code, current_value, input2_code, const_value, selected_fluid.get())
                    print (calc_p)
                    calc_temp = convert_from_SI(calc_temp, "temperature", temp_unit)
                    calc_p = convert_from_SI(calc_p, "pressure", pressure_unit)#Temperatur in gewählte Einheit zurück umwandeln
                    calc_d = convert_from_SI(calc_d, "density", density_unit)
                    calc_h = convert_from_SI(calc_h, "enthalpy", enthalpy_unit)
                    calc_s = convert_from_SI(calc_s, "entropy", entropy_unit)
                    calc_u = convert_from_SI(calc_u, "internal_energy", i_energy_unit)
                    calc_cp = convert_from_SI(calc_cp, "cp", cp_unit)
                    calc_cv = convert_from_SI(calc_cv, "cv", cv_unit)
                    calc_v = convert_from_SI(calc_v, "volume", volume_unit)
                    print(calc_state)
                    
                    calc_state = state(calc_state) # um Aggregatszustand zu ändern
                    
                    if calc_x == -100:
                        calc_x = 0
                        
                    data = [round(calc_temp, 3), round(calc_p, 3), round(calc_d, 3), round(calc_v, 3),round(calc_u, 3),
                            round(calc_h, 3), round(calc_s, 3), round(calc_vis, 3), calc_state, round(calc_x, 1), round(calc_cp, 3), round(calc_cv, 3)]
                    
                    tree.insert("", "end", values=data)
                    
                except:
                    tkinter.messagebox.showwarning("Warnung", f"Berechnung fehlgeschlagen für {current_value}!")
                
                current_value += step
        except ValueError:
            tkinter.messagebox.showwarning("Warnung", "Bitte gültige Zahlenwerte eingeben!")

    
    
    def calc():
        global mouse_event_triggered
        
        fluid_info(selected_fluid)#setzt Fluidinfo
        #for item in tree.get_children():#löscht tree
           #tree.delete(item)
        if not mouse_event_triggered:
            for item in tree.get_children():
                tree.delete(item)
                
    
        #mouse_event_triggered = False  # zurücksetzen für nächsten Durchlauf
    
    
        
        if check_input() == False:  # Falls check_input False zurückgibt, abbrechen
            return
        variable1 = selected_variable1.get()
        variable2 = selected_variable2.get()
        
        try:

            if variable1 == "Temperatur T":
                inconst_value = convert_to_SI(float(eingabe1_var.get()), "temperature", temp_unit)
            elif variable1 == "Druck p":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "pressure", pressure_unit)
            elif variable1 == "Dichte rho":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "density", density_unit)
            elif variable1 == "Spezifische Enthalpie h":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "enthalpy",  enthalpy_unit)
            elif variable1 == "Spezifische Entropie s":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "entropy",  entropy_unit)
            elif variable1 == "Innere Energie u":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "internal_energy", i_energy_unit)
            elif variable1 == "Cp":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "cp", cp_unit)
            elif variable1 == "Cv":
                inconst_value =convert_to_SI(float(eingabe1_var.get()),"cv", cv_unit)
            elif variable1 == "Volumen v":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "volume", volume_unit)
            else:
                inconst_value = float(eingabe1_var.get())
                
            
            if variable2 == "Temperatur T":
                const_value = convert_to_SI(float(eingabe2_var.get()), "temperature", temp_unit)
            elif variable2 == "Druck p":
                const_value = convert_to_SI(float(eingabe2_var.get()), "pressure",pressure_unit)
            elif variable2 == "Dichte rho":
                const_value = convert_to_SI(float(eingabe2_var.get()), "density",density_unit)
            elif variable2 == "Spezifische Enthalpie h":
                const_value = convert_to_SI(float(eingabe2_var.get()), "enthalpy",enthalpy_unit)
            elif variable2 == "Spezifische Entropie s":
                const_value = convert_to_SI(float(eingabe2_var.get()),"entropy",entropy_unit)
            elif variable2 == "Innere Energie u":
                const_value = convert_to_SI(float(eingabe2_var.get()),"internal_energy", i_energy_unit)
            elif variable2 == "Cp":
                const_value = convert_to_SI(float(eingabe2_var.get()),"cp", cp_unit)
            elif variable2 == "Cv":
                const_value = convert_to_SI(float(eingabe2_var.get()),"cv", cv_unit)
            elif variable2 == "Volumen v":
                const_value = convert_to_SI(float(eingabe2_var.get()),"volume", volume_unit)
            else:
                const_value = float(eingabe2_var.get())

                
           
            
            if variable1 == variable2:
                tkinter.messagebox.showwarning("Warnung", "Bitte zwei unterschiedliche Variablen zur Berechnung wählen!")
                return          
            

                
            elif (variable1, variable2) in [("Spezifische Enthalpie h", "Temperatur T"), ("Temperatur T", "Spezifische Enthalpie h"), 
                                            ("Spezifische Entropie s", "Dampfqualität x"), ("Dampfqualität x", "Spezifische Entropie s"),
                                            ("Innere Energie u", "Temperatur T"),("Temperatur T","Innere Energie u" ),
                                            ("Innere Energie u", "Spezifische Enthalpie h"),("Spezifische Enthalpie h","Innere Energie u" ),
                                            ("Innere Energie u", "Spezifische Entropie s"),("Spezifische Entropie s","Innere Energie u" ),
                                            ("Innere Energie u", "Dampfqualität x"),("Dampfqualität x","Innere Energie u" ),
                                            ("Volumen v", "Dichte rho"), ("Dichte rho", "Volumen v")]:
                tkinter.messagebox.showwarning("Warnung", "Dieses Paar von Eingabevariablen ist nicht möglich! Bitte eine andere Kombination wählen.")
                return
            else:
                input1_code = get_input_code(variable1)
                input2_code = get_input_code(variable2)
                
            if not check_limits(variable1, variable2, const_value, inconst_value, maxtemp, mfloatemp, maxp, minp):
                return    
                
            if variable1 == "Volumen v":    # v umrechnen dass damit auch als eingabe gerechnet werden kann
                #helpdensity = 1/eingabe1_var.get()
                input1_code = "D"
                #inconst_value = helpdensity
                inconst_value = 1/inconst_value
            elif variable2 == "Volumen v":
                #helpdensity = 1/eingabe2_var.get()
                input2_code = "D"
                #const_value = helpdensity
                const_value = 1/const_value

            try:
                print(input1_code, inconst_value, input2_code, const_value)
                calc_temp = CoolProp.PropsSI("T", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_p = CoolProp.PropsSI("P", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())                                    
                calc_d = CoolProp.PropsSI("D", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_h = CoolProp.PropsSI("H", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_s = CoolProp.PropsSI("S", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_x = CoolProp.PropsSI("Q", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())*100
                calc_u = CoolProp.PropsSI("U", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_vis = CoolProp.PropsSI("V", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_cp = CoolProp.PropsSI("CPMASS", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_cv = CoolProp.PropsSI("CVMASS", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_v = 1/ (CoolProp.PropsSI("D", input1_code, inconst_value, input2_code, const_value, selected_fluid.get()))
                calc_state = CoolProp.PropsSI("PHASE", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                
                
                
                calc_temp = convert_from_SI(calc_temp, "temperature", temp_unit)
                calc_p = convert_from_SI(calc_p, "pressure", pressure_unit)#Temperatur in gewählte Einheit zurück umwandeln
                calc_d = convert_from_SI(calc_d, "density", density_unit)
                calc_h = convert_from_SI(calc_h, "enthalpy", enthalpy_unit)
                calc_s = convert_from_SI(calc_s, "entropy", entropy_unit)
                calc_u = convert_from_SI(calc_u, "internal_energy", i_energy_unit)
                calc_cp = convert_from_SI(calc_cp, "cp", cp_unit)
                calc_cv = convert_from_SI(calc_cv, "cv", cv_unit)
                calc_v = convert_from_SI(calc_v, "volume", volume_unit)
                
                calc_state = state(calc_state)
                
                if calc_x == -100:
                    calc_x = 0  
                    
                data = [round(calc_temp, 3), round(calc_p, 3), round(calc_d, 3), round(calc_v, 3),round(calc_u, 3),
                        round(calc_h, 3), round(calc_s, 3), round(calc_vis, 3), calc_state, round(calc_x, 1), round(calc_cp, 3), round(calc_cv, 3)]
                
                tree.insert("", "end", values=data)
                
                mouse_event_triggered = False
            # except:
            #     tkinter.messagebox.showwarning("Warnung", "Berechnung fehlgeschlagen!")
            #     print("Berchnung fehlgeschlagen")
            except Exception as e:
                tkinter.messagebox.showwarning("Warnung", f"Berechnung fehlgeschlagen:\n{e}")
                print("Berechnung fehlgeschlagen:", e)
                    
        except ValueError:
            tkinter.messagebox.showwarning("Warnung", "Bitte gültige Zahlenwerte eingeben!")
    
    def get_input_code(variable_name):
        mapping = {
            "Temperatur T": "T",
            "Druck p": "P",
            "Dichte rho": "D",
            "Spezifische Enthalpie h": "H",
            "Spezifische Entropie s": "S",
            "Dampfqualität x": "Q",
            "Innere Energie u": "U",
            "Viskosität eta": "V",
            "Cp": "CPMASS",
            "Cv": "CVMASS",
            "Volume v": "D"
        }
        return mapping.get(variable_name, "")

    
    def state(calc_state):
        state_mapping = {
            0.0: "flüssig",
            3.0: "flüssig",
            2.0: "gasförmig",
            5.0: "gasförmig",
            1.0: "überkritisch",
            4.0: "krit. Punkt",
            6.0: "Nassdampfgebiet"
        }
        return state_mapping.get(calc_state, "unbekannt")

    def check_limits(variable1, variable2, const_value, inconst_value, maxtemp, mfloatemp, maxp, minp):
        # Temperaturprüfungen
        if variable1 == "Temperatur T":
            print(inconst_value, maxtemp, mfloatemp)
            if inconst_value > maxtemp or inconst_value < mfloatemp:
                tkinter.messagebox.showwarning("Warnung", "Temperaturwert 1 liegt außerhalb der Fluidgrenzen!")
                return False
    
        if variable2 == "Temperatur T":
            if const_value > maxtemp or const_value < mfloatemp:
                tkinter.messagebox.showwarning("Warnung", "Temperaturwert 2 liegt außerhalb der Fluidgrenzen!")
                return False
    
        # Druckprüfungen
        if variable1 == "Druck p":
            if inconst_value > maxp or inconst_value < minp:
                tkinter.messagebox.showwarning("Warnung", "Druckwert 1 liegt außerhalb der Fluidgrenzen!")
                return False
    
        if variable2 == "Druck p":
            if const_value > maxp or const_value < minp:
                tkinter.messagebox.showwarning("Warnung", "Druckwert 2 liegt außerhalb der Fluidgrenzen!")
                return False
    
        return True

    def check_limitsw(variable1, variable2, start_value, const_value, end_value, maxtemp, mfloatemp, maxp, minp):
        # Temperaturprüfungen
        if variable1 == "Temperatur T":
            if end_value > maxtemp or start_value < mfloatemp:
                tkinter.messagebox.showwarning("Warnung", "Start- oder Endwert liegen außerhalb der Fluidgrenzen!")
                return False
    
        if variable2 == "Temperatur T":
            if const_value > maxtemp or const_value < mfloatemp:
                tkinter.messagebox.showwarning("Warnung", "Temperaturwert liegt außerhalb der Fluidgrenzen!")
                return False
    
        # Druckprüfungen
        if variable1 == "Druck p":
            if end_value > maxp or start_value < minp:
                tkinter.messagebox.showwarning("Warnung", "Start- oder Endwert liegen außerhalb der Fluidgrenzen!")
                return False
    
        if variable2 == "Druck p":
            if const_value > maxp or const_value < minp:
                tkinter.messagebox.showwarning("Warnung", "Druckwert 2 liegt außerhalb der Fluidgrenzen!")
                print (end_value, const_value, maxp, minp)
                return False
    
        return True


    # Use of Return Key
    def return_calc(event):
        calc()

    #diagram(selected_diagram.get())
    
    def rechnen():
        if checkbox_var.get() == 1:
            calcw()
            create_figure(selected_fluid.get())
            show_diagram()
        else:
            calc()
            create_figure(selected_fluid.get())
            show_diagram()
    

    def export_treeview_to_csv():
        rows = tree.get_children()
        if not rows:
            tk.messagebox.showinfo("Info", "Keine Daten zum Exportieren.")
            return
    
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV-Dateien", "*.csv")],
            title="CSV-Datei speichern"
        )
        if not file_path:
            return  # Abgebrochen
    
        # CSV in einen StringIO-Puffer schreiben
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')  # Oder ',' für US-Format
    
        # Spaltenüberschriften schreiben
        headers = [tree.heading(col)["text"] for col in tree["columns"]]
        writer.writerow(headers)
    
        # Alle Datenzeilen schreiben
        for row_id in tree.get_children():
            row_data = tree.item(row_id)["values"]
            writer.writerow(row_data)
    
        # Inhalt in Datei speichern
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            file.write(output.getvalue())
    
        # In Zwischenablage kopieren
        window.clipboard_clear()
        window.clipboard_append(output.getvalue())
        window.update()  # Wichtig für Windows
    
        tk.messagebox.showinfo("Erfolg", f"CSV wurde erfolgreich gespeichert und kopiert:\n{file_path}")

        
    
    # Create Calc Button
    calc_btn = ttk.Button(main_frame, text="▶️ Berechnen", command=rechnen, width=17)
    calc_btn.grid(row=10, column=3, sticky="Nw", columnspan=1, pady=10, padx=(25,0))
    main_frame.bind("<Return>", return_calc)

    csv_button = ttk.Button(main_frame, text="💾 CSV exportieren", command=export_treeview_to_csv, width=17)
    csv_button.grid(row=10, column=3, pady=10, sticky="w", padx=(150,0))  # Anpassen an dein Layout
    
    diagram_btn = ttk.Button(diagram_frame, text="↺ Aktualisieren", command=show_diagram, width=25)
    diagram_btn.grid(row=8, column=1, pady=10, padx=10, sticky="w")
    
    
    
    
    def update_labels():
        if checkbox_var.get() == 1:  # Checkbox ist angehakt
            checkbox.config(text="4. Bitte geben Sie einen Wertebereich für Variable 1 ein:")
            wertemin_label.config(fg="black")
            wertemax_label.config(fg="black")
            schritte_label.config(fg="black")
            wertemin_entry.config(foreground="black")
            wertemax_entry.config(foreground="black")
            schritte_entry.config(foreground="black")
            input1unit_label.config(foreground="light grey")
            eingabe1_entry.config(foreground="light grey")
        else:  # Checkbox nicht angehakt
            checkbox.config(text="Wertebereich")
            wertemin_label.config(foreground="light gray")
            wertemax_label.config(fg="light gray")
            schritte_label.config(fg="light gray")
            wertemin_entry.config(foreground="light gray")
            wertemax_entry.config(foreground="light gray")
            schritte_entry.config(foreground="light gray")
            input1unit_label.config(foreground="black")
            eingabe1_entry.config(foreground="black")
    
    #create checkbox
    checkbox_var = tk.IntVar(value=0)
    checkbox = tk.Checkbutton(main_frame, text="Wertebereich", font=("Arial", 12, "bold"), variable=checkbox_var, command=update_labels)
    checkbox.grid(row=8, column=2, columnspan=2, padx=20, pady=5, sticky="w")
    
    all_entry_fields = [eingabe1_entry, eingabe2_entry, wertemin_entry, wertemax_entry, schritte_entry, minx_entry, miny_entry, maxx_entry, maxy_entry]
    checkbox_vars = [checkbox_var, isobar_var, isotherm_var, isochor_var, isentropic_var, isenthalpic_var, isovapore_var, legende_var, legende_set]
    
    
    def reset_app():
        global cache_reinstoffe
        # ░0░ Treeview-Daten speichern + in History einfügen
        #save_current_data(tree, cache_reinstoffe)
        load_history_from_file() 
        cache_reinstoffe.clear()
        for item in tree.get_children():
            row = tree.item(item)["values"]
            append_to_history(history_reinstoffe, row)
            append_to_cache(cache_reinstoffe, row)
            #save_current_data(tree, cache_reinstoffe)
        
           
        # ░1░ Diagramm + Toolbar löschen
        for widget in diagram_canvas_frame.winfo_children():
            widget.destroy()

        # ░2░ Eingabefelder leeren (alle tkinter.Entry Felder)
        for entry in all_entry_fields:  # Liste vorher definieren!
            entry.delete(0, tk.END)
            entry.insert(0, "0")
        
        default_units = {
            "Temperatur T": "Kelvin",
            "Druck p": "Pa",
            "Dichte rho": "kg/m³",
            "Volumen v": "m³/kg",
            "Innere Energie u": "J/kg",
            "Spezifische Enthalpie h": "J/kg",
            "Spezifische Entropie s": "J/kg*K",
            "Viskosität eta": "Pa*s",
            "Cp": "J/kg*K",
            "Cv": "J/kg*K"
        }
        for label, var in selected_vars.items():
            default = default_units.get(label)
            if default:
                var.set(default)
            
        # ░3░ Comboboxen auf Standard zurücksetzen
        fluid_combobox.set("Water")
        input1_combobox.set("Temperatur T")
        input2_combobox.set("Druck p")
        diagram_combobox.set("T-s-Diagramm")    # z. B.

    
        # ░4░ Treeview leeren
        for item in tree.get_children():
            tree.delete(item)
    
        # ░5░ Checkboxen zurücksetzen
        for var in checkbox_vars:  # Liste von BooleanVar(), z. B.
            var.set(False)
        
        # ░8░ Fluid-Informationen zurücksetzen
        pure_info_label["text"] = "- Reines Fluid:"
        molarmass_info_label["text"] = "- Molare Masse: "
        gasconstant_info_label["text"] = "- Spez. Gaskonstante: "
        ctp_pressure_label["text"] = "- Druck: "
        ctp_temp_label["text"] = "- Temperatur: "
        ctp_den_label["text"] = "- Dichte: "
        tp_pressure_label["text"] = "- Druck: "
        tp_temp_label["text"] = "- Temperatur: "
        maxp_label["text"] = "- Max. Druck: "
        maxtemp_label["text"] = "- Max. Temperatur: "
        minp_label["text"] = "- Min. Druck: "
        mfloatemp_label["text"] = "- Min. Temperatur: "

    
        # ░6░ Globale Plot-Objekte zurücksetzen
        current_ax = None
        current_canvas = None
        fig = None
        cursor_annotation = None
        update_labels()
        show_diagram()
        selected_row_values = None
        highlight_point = False
        print("Anwendung wurde vollständig zurückgesetzt.")
        
        
    def reset_app_delayed():
        # Neues kleines Fenster ohne Rand
        loading_window = tk.Toplevel(window)
        loading_window.title("Bitte warten...")
        loading_window.geometry("300x140")
        loading_window.resizable(False, False)
        loading_window.overrideredirect(True)  # Kein Rand, keine Titelleiste
        loading_window.configure(bg="white")  # Hintergrundfarbe

    
        # Fenster zentrieren
        x = window.winfo_x() + (window.winfo_width() // 2) - 125
        y = window.winfo_y() + (window.winfo_height() // 2) - 60
        loading_window.geometry(f"+{x}+{y}")
        
        # Info-Label
        label = tk.Label(loading_window, text="Zurücksetzen läuft...", font=("Arial", 12))
        label.pack(pady=(15, 5))
        label.configure(bg="white")  # Hintergrundfarbe

    
        # Lade-Animation (Text-Kreis)
        spinner_label = tk.Label(loading_window, font=("Consolas", 25))
        spinner_label.pack()
        spinner_label.configure(bg="white")  # Hintergrundfarbe

        # Animation: sich drehendes Zeichen
        spinner_frames = itertools.cycle(["◐", "◓", "◑", "◒"])
    
        def animate():
            spinner_label.config(text=next(spinner_frames))
            loading_window.after(100, animate)
    
        animate()  # Start Animation
    
        # Nach 5 Sekunden: Fenster schließen + Reset
        window.after(1000, lambda: [loading_window.destroy(), reset_app()])   
    # def reset_app_delayed():
    #     # GUI erst nach 1 Sekunde zurücksetzen
    #     tk.messagebox.showinfo("Information", "Anwendung wird vollständig zurückgesetzt.")
    #     window.after(5000, reset_app)
       
    reset_btn = ttk.Button(main_frame, text="🏠 Zurück zum Start", command=reset_app_delayed, width=25)
    reset_btn.grid(row=0, column=3, pady=10, padx=80, sticky="w")
    
    def delete_row():
        selected_item = tree.selection()
        if selected_item:
            tree.delete(selected_item)
        else:
            print("Keine Zeile ausgewählt")

    delete_button = ttk.Button(main_frame, text="🗑️Müll", command=delete_row, width=9, )
    delete_button.grid(row=9, column=3, pady=10, sticky="w", padx=(200,0))
    
    def reload_reinstoffe():
        load_history_from_file()
        update_cache_treeview(tree, cache_reinstoffe)
        
    
    
    cache_btn = ttk.Button(main_frame, text="Sitzung wiederherstellen", command=reload_reinstoffe, width=25)
    cache_btn.grid(row=0, column=2, pady=10, padx=20, sticky="w")
    #update_cache_treeview(tree, cache_reinstoffe)
    #reload_reinstoffe()
    
#Seite Reinstoffe
#-----------------------------------------------------------------------------------------------------
#Seite Stoffgemische

def show_stoffgemische():
    for widget in main_frame.winfo_children():
        widget.destroy()
    heading_label = tk.Label(main_frame, text="Stoffgemische", font=("Arial", 20, "bold"),  width=40)
    heading_label.grid(row=0, column=0,  padx=20, pady=7, sticky="w", columnspan=3)
    heading_label.configure(background="darkseagreen2")

#Seite Stoffgemische
#-----------------------------------------------------------------------------------------------------
#Seite Kreislaeufe
def sort_treeview_by_column(tree, col_index, reverse=False):#bei Klicken auf "von" in Tabelle, werden alle Einträge aufsteigend sortiert
    items = [(tree.set(k, "von"), k) for k in tree.get_children('')]

    try:
        # In float konvertieren, um numerisch zu sortieren
        items.sort(key=lambda t: float(t[0]), reverse=reverse)
    except ValueError:
        # Falls das Konvertieren nicht klappt, dann alphanumerisch
        items.sort(key=lambda t: t[0], reverse=reverse)

    for index, (val, k) in enumerate(items):
        tree.move(k, '', index)


def show_kreisprozesse(): 
    
    # Einheitenspeicherung für spätere Nutzung
    global tree, temp_unit, pressure_unit, density_unit, volume_unit,i_energy_unit, enthalpy_unit, entropy_unit, viscosity_unit, cp_unit, cv_unit, tree2
    for widget in main_frame.winfo_children():
        widget.destroy()
    
    def on_row_select(event):
        global selected_row_values
    
        # Alte Markierung entfernen
        for row in tree.get_children():
            tree.item(row, tags=())
    
        # Aktuell ausgewählte Zeile markieren
        selected_item = tree.focus()
        tree.item(selected_item, tags=("highlight",))
        tree.tag_configure("highlight", background="red", foreground="white")
    
        # Daten der ausgewählten Zeile speichern
        selected_row_values = tree.item(selected_item, "values")
        print("Ausgewählte Zeile:", selected_row_values)  # Optional: Debug-Ausgabe
    
    
    # Tabelle erstellen-------------------------------------------------------------------------------------
  

    tree_frame = tk.Frame(main_frame, width=1000, height=180)
    tree_frame.grid(row=11, column=0, columnspan=4, sticky="nsew", padx=40, pady=10)
    tree_frame.grid_propagate(False)
    
    tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
    tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
    
    
    tree2 = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
    tree2["columns"] = ["state_change", "von", "zu", "temperatur", "pressure", "density", "volume", "internal energy", "enthalpy", "entropy", "viscosity", "state","vapor_quality","cp", "cv" ]
    tree2.column("#0", width=0)          #damit 0. Spalte nicht sichtbar ist
    tree2.bind('<Motion>', 'break')      #damit Spaltenbreite unveränderbar ist für User
    
    
    for col in tree2["columns"]:
        tree2.column(col, width=122, anchor="center")
    tree2.column("von", width=50, anchor="center")
    tree2.column("zu", width=50, anchor="center")
    
    for col in tree2["columns"]:#damit sortiert wird
        tree2.heading(col, text=col, command=lambda _col=col: sort_treeview_by_column(tree2, _col))

    tree_scroll_y.config(command = tree2.yview)
    tree_scroll_x.config(command = tree2.xview)
    
    tree2.grid(row=0, column=0, sticky="nsew")
    tree_scroll_y.grid(row=0, column=1, sticky="ns")
    tree_scroll_x.grid(row=1, column=0, sticky="ew")
    
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)
    
    tree2.bind("<<TreeviewSelect>>", on_row_select)
    
    #-------------

    
    #Updates Einheiten überall---------------------------------------------------------------------------
    
    def update_units(*args):        #args damit die Einheiten jederzeit verändert werden, wenn sie geändert werden
       window.update_idletasks()  # Stellt sicher, dass Tkinter die Variablen aktualisiert hat
   
       global temp_unit, pressure_unit, density_unit, volume_unit,i_energy_unit, enthalpy_unit, entropy_unit, viscosity_unit, cp_unit, cv_unit, axis_names
       
       temp_unit = selected_vars["Temperatur T"].get()
       pressure_unit = selected_vars["Druck p"].get()
       density_unit = selected_vars["Dichte rho"].get()
       volume_unit = selected_vars["Volumen v"].get()       #0.0010029231088 für 298K und 100000Pa
       i_energy_unit = selected_vars ["Innere Energie u"].get()
       enthalpy_unit = selected_vars["Spezifische Enthalpie h"].get()
       entropy_unit = selected_vars["Spezifische Entropie s"].get()
       viscosity_unit = selected_vars["Viskosität eta"].get()
       cp_unit = selected_vars["Cp"].get()
       cv_unit = selected_vars["Cv"].get()
       
       selected_input1 = selected_variable1.get()       #Label 1 ändern
       if selected_input1 == "Dichte rho":
           input1unit_label["text"] = density_unit
       elif selected_input1 == "Druck p":
           input1unit_label["text"] = pressure_unit
       elif selected_input1 == "Temperatur T":
           input1unit_label["text"] = temp_unit
       elif selected_input1 == "Spezifische Enthalpie h":
           input1unit_label["text"] = enthalpy_unit
       elif selected_input1 == "Spezifische Entropie s":
           input1unit_label["text"] = entropy_unit
       elif selected_input1 == "Dampfqualität x":
           input1unit_label["text"] = "kg/kg"
       elif selected_input1 == "Volumen v":
           input1unit_label["text"] = volume_unit
       elif selected_input1 == "Innere Energie u":
           input1unit_label["text"] = i_energy_unit
       # elif selected_input1 == "Viskosität eta":
       #     input1unit_label["text"] = viscosity_unit
       # elif selected_input1 == "Cp":
       #     input1unit_label["text"] = cp_unit
       # elif selected_input1 == "Cv":
       #     input1unit_label["text"] = cv_unit
           
       selected_input2 = selected_variable2.get()       #Label 2 ändern
       if selected_input2 == "Dichte rho":
           input2unit_label["text"] = density_unit
       elif selected_input2 == "Druck p":
           input2unit_label["text"] = pressure_unit
       elif selected_input2 == "Temperatur T":
           input2unit_label["text"] = temp_unit
       elif selected_input2 == "Spezifische Enthalpie h":
           input2unit_label["text"] = enthalpy_unit
       elif selected_input2 == "Spezifische Entropie s":
           input2unit_label["text"] = entropy_unit
       elif selected_input2 == "Dampfqualität x":
           input2unit_label["text"] = "kg/kg"
       elif selected_input2 == "Volumen v":
           input2unit_label["text"] = volume_unit
       elif selected_input2 == "Innere Energie u":
           input2unit_label["text"] = i_energy_unit
       # elif selected_input2 == "Viskosität eta":
       #     input2unit_label["text"] = viscosity_unit
       # elif selected_input2 == "Cp":
       #     input2unit_label["text"] = cp_unit
       # elif selected_input2 == "Cv":
       #     input2unit_label["text"] = cv_unit
       
       columns = {
            "state_change": f"Zustandsänderung",
            "von": f"von ",
            "zu": f"zu",
            "temperatur": f"Temperatur [{temp_unit}]",
            "pressure": f"Druck [{pressure_unit}]",
            "density": f"Dichte [{density_unit}]",
            "volume":f"Volumen [{volume_unit}]", 
            "internal energy":f"Innere Energie [{i_energy_unit}]",
            "enthalpy": f"Enthalpie [{enthalpy_unit}]",
            "entropy": f"Entropie [{entropy_unit}]",
            "vapor_quality": f"Dampfqualität [%]",
            "viscosity": f"Viskosität [{viscosity_unit}]", 
            "cp": f"Cp [{cp_unit}]", 
            "cv": f"Cv [{cv_unit}]", 
            "state": f"Aggregatszustand"
       }
       
       for col, heading in columns.items():
            tree2.heading(col, text=heading)
       
       axis_names = {
            "temperatur": f"Temperatur [{temp_unit}]",
            "pressure": f"Druck [{pressure_unit}]",
            "density": f"Dichte [{density_unit}]",
            "volume":f"Volumen [{volume_unit}]", 
            "enthalpy": f"Enthalpie [{enthalpy_unit}]",
            "entropy": f"Entropie [{entropy_unit}]"}

       
       return axis_names
        
       
       
       
       
    row_index = 3
    
    
    heading_label = tk.Label(main_frame, text="Kreisprozesse", font=("Arial", 20, "bold"), width=40)
    heading_label.grid(row=0, column=0,  padx=20, pady=7, sticky="w", columnspan=3)
    heading_label.configure(background="rosybrown2")
    
    stoffauswahl_label = tk.Label(main_frame, text="1. Bitte wählen Sie den gewünschten Stoff aus:", font=("Arial", 12, "bold"))
    stoffauswahl_label.grid(row=1, column=0,  padx=20, pady=5, sticky="w")
    
    selected_fluid = tk.StringVar()         #Dropdownmenü Fluidauswahl
    selected_fluid.set("Water") 
    cp_fluids = CoolProp.FluidsList()
    fluid_combobox = ttk.Combobox(main_frame, width=38, textvariable=selected_fluid, values=cp_fluids, state="readonly")
    fluid_combobox.grid(row=1, column=1, padx=2, pady=5, sticky="w") 
    fluid_combobox.set("Water")
    
    einheiten_label = tk.Label(main_frame, text="2. Bitte wählen Sie die gewünschten Einheiten aus:", font=("Arial", 12, "bold"))
    einheiten_label.grid(row=2, column=0, columnspan=1, padx=20, pady=5, sticky="w")
    
    einheiten = {
        "Temperatur T": ["Kelvin", "Celsius", "Fahrenheit", "Rankine"],
        "Druck p": ["Pa", "bar", "atm"],
        "Dichte rho": ["kg/m³", "g/m³", "kg/l", "g/l"],
        "Volumen v": ["m³/kg", "m³/g", "l/kg", "l/g"],
        "Innere Energie u": ["J/kg", "J/g"],
        "Spezifische Enthalpie h": ["J/kg", "J/g"],
        "Spezifische Entropie s": ["J/kg*K", "J/g*K"],
        "Viskosität eta": ["Pa*s"],
        "Cp": ["J/kg*K", "J/g*K"],
        "Cv": ["J/kg*K", "J/g*K"]

        
    }
    
    einheiten_list =["Temperatur T", "Druck p", "Dichte rho", "Volumen v", "Innere Energie u", "Spezifische Enthalpie h", "Spezifische Entropie s","Dampfqualität x"]
    
   
    einheiten_frame = ttk.LabelFrame(main_frame, text="Einheiten")
    einheiten_frame.grid(row=3, column=0, columnspan=1, padx=20, pady=5, sticky="w")


    #Einheiten in Frames einsetzen
    for label, options in einheiten.items():
        size_label = ttk.Label(einheiten_frame, text=label + ":", font=("Arial", 10))
        size_label.grid(row=row_index, column=0, padx=10, pady=5, sticky="w")
    
        selected_var = tk.StringVar(value=options[0])
        selected_vars[label] = selected_var
    
        dropdown = ttk.Combobox(einheiten_frame, textvariable=selected_var, values=options, state="readonly", width=20)
        dropdown.grid(row=row_index, column=1, padx=10, pady=5, sticky="w")
    
        selected_var.trace_add("write", update_units)
        row_index += 1

    temp_unit = selected_vars["Temperatur T"].get()
    pressure_unit = selected_vars["Druck p"].get()
    density_unit = selected_vars["Dichte rho"].get()
    volume_unit = selected_vars["Volumen v"].get()
    i_energy_unit = selected_vars ["Innere Energie u"].get()
    enthalpy_unit = selected_vars["Spezifische Enthalpie h"].get()
    entropy_unit = selected_vars["Spezifische Entropie s"].get()
    viscosity_unit = selected_vars["Viskosität eta"].get()
    cp_unit = selected_vars["Cp"].get()
    cv_unit = selected_vars["Cv"].get()

    
    # Werteeingabe
    eingabe_label = tk.Label(main_frame, text="3. Bitte wählen Sie zwei Input-Variablen aus und tragen Sie die Werte ein:", font=("Arial", 12, "bold") )
    eingabe_label.grid(row=8, column=0, columnspan=2, padx=20, pady=5, sticky="w")
    
    eingabe_label = tk.Label(main_frame, text="Input-Variable 1", font=("Arial", 10))
    eingabe_label.grid(row=9, column=0, padx=20, pady=5, sticky="w")
    
    eingabe_label = tk.Label(main_frame, text="Input-Variable 2", font=("Arial", 10))
    eingabe_label.grid(row=10, column=0, padx=20, pady=5, sticky="w")
    
    

    input1unit_label = ttk.Label(main_frame, text=temp_unit)
    input1unit_label.grid(row=9, column=1, padx=70, sticky="W")
    
    input2unit_label = ttk.Label(main_frame, text=temp_unit)
    input2unit_label.grid(row=10, column=1, padx=70,sticky="W")
    
    eingabe1_var = tk.StringVar()
    eingabe1_entry = ttk.Entry(main_frame, textvariable=eingabe1_var, width=10)
    eingabe1_entry.grid(row=9, column=1, padx=1, pady=5, sticky="w")
    
    eingabe2_var = tk.StringVar()
    eingabe2_entry = ttk.Entry(main_frame, textvariable=eingabe2_var, width=10)
    eingabe2_entry.grid(row=10, column=1, padx=1, pady=5, sticky="w")
    
    def on_select_inpu1(event):
        update_units()
        
    def on_select_inpu2(event):
        update_units()
    
    
    
    selected_variable1 = tk.StringVar(value="Temperatur T") #welche Größe ausgewählt
    input1_combobox = ttk.Combobox(main_frame, width=22, textvariable=selected_variable1, values=list(einheiten_list), state="readonly")
    input1_combobox.grid(row=9, column=0, padx=150, sticky="W")
    input1_combobox.bind_all("<<ComboboxSelected>>", on_select_inpu1)
    #input1_combobox.bind("<<ComboboxSelected>>", on_select_inpu1, add="+") 
    
    selected_variable2 = tk.StringVar(value="Druck p")
    input2_combobox = ttk.Combobox(main_frame, width=22, textvariable=selected_variable2, values=list(einheiten_list), state="readonly")
    input2_combobox.grid(row=10, column=0, padx=150,sticky="W")
    input2_combobox.bind("<<ComboboxSelected>>", on_select_inpu2)
     
    update_units()  #damit die Einheiten jederzeit verändert werden, wenn sie geändert werden
    
    #----------- Wertebereich ---------------------------------
    # Checkbox hinzufügen
    
    zustaende_liste=["isobar", "isotherm", "isochor", "isentrop"]
    von_liste = [1,2,3,4,5,6,7,8,9,10]
    zu_liste = [1,2,3,4,5,6,7,8,9,10]          
    #Schrittweite
    zustandsänderung_label = tk.Label(main_frame, text="Zustandsänderung:", font=("Arial", 10))
    zustandsänderung_label.grid(row=9, column=2, padx=20, pady=5, sticky="w")
    
    zustand_var = tk.StringVar(value="isobar")
    zustand_Combobox = ttk.Combobox(main_frame, textvariable=zustand_var, values=list(zustaende_liste), width=15, state="readonly")
    zustand_Combobox.grid(row=9, column=2, padx=170, pady=5, sticky="w")
    
   
    von_label = tk.Label(main_frame, text="Von Punkt:", font=("Arial", 10))
    von_label.grid(row=10, column=2, pady=5, padx=20,sticky="w")   
    
    von_var= tk.StringVar(value=1)
    von_Combobox = ttk.Spinbox(main_frame, textvariable=von_var, from_=1, to=10, width=4, state="readonly")
    von_Combobox.grid(row=10, column=2, padx=(100,0), pady=5, sticky="w")
    
    zu_label = tk.Label(main_frame, text="zu Punkt:", font=("Arial", 10))
    zu_label.grid(row=10, column=2, pady=5, padx=(165,0),sticky="w")  
    
    zu_var= tk.StringVar(value=2)
    zu_Combobox = ttk.Spinbox(main_frame, textvariable=zu_var, from_=1, to=10, width=4, state="readonly")
    zu_Combobox.configure(background="white")
    zu_Combobox.grid(row=10, column=2, padx=(235,0), pady=5, sticky="w")
    
    
    
    
    #Fluidinformationen---------------------------------
    
    #alle labels erstellen ohne einfügen von Werten
    infos_frame = ttk.LabelFrame(main_frame, text="Fluidinformationen", relief="flat")
    infos_frame.grid(row=2, column=1, columnspan=1,rowspan=6, padx=2, pady=5, sticky="ew")
    infos_frame.configure(style="Custom.TLabelframe")
    
    
    pure_info_label = ttk.Label(infos_frame, text="- Reines Fluid:",font=("Arial", 10))
    pure_info_label.grid(row=0, column=0, columnspan=1, padx=5, sticky="W")
    
    molarmass_info_label = ttk.Label(infos_frame, text= "- Molare Masse: ", font=("Arial", 10))       #molare Masse
    molarmass_info_label.grid(row=2, column=0, padx=5,columnspan=2, sticky="W") 
    
    gasconstant_info_label = ttk.Label(infos_frame, text = "- Spez. Gaskonstante: ", font=("Arial", 10))     #Gaskonstante
    gasconstant_info_label.grid(row=3, column=0, columnspan=2, padx=5,sticky="W")


    # Critical Point Label
    ctp_label = ttk.Label(infos_frame, text="Kritischer Punkt:", font=("Arial", 10, "underline"))
    ctp_label.grid(row=5, column=0,padx=5, pady=10, sticky="W")
    
    ctp_pressure_label = ttk.Label(infos_frame,text= "- Druck: ", font=("Arial", 10))
    ctp_pressure_label.grid(row=6, column=0, columnspan=1, padx=5,sticky="W")
    
    ctp_temp_label = ttk.Label(infos_frame,text = "- Temperatur: ",font=("Arial", 10))
    ctp_temp_label.grid(row=7, column=0,padx=5, sticky="W")
    
    ctp_den_label = ttk.Label(infos_frame, text = "- Dichte: " , font=("Arial", 10))
    ctp_den_label.grid(row=8, column=0,padx=5, sticky="W")

    # Triple Point Label
    tp_label = ttk.Label(infos_frame, text="Tripelpunkt:", font=("Arial", 10, "underline"))
    tp_label.grid(row=9, column=0,padx=5, pady=5, sticky="W")
    
    tp_pressure_label = ttk.Label(infos_frame, text= "- Druck: " , font=("Arial", 10))
    tp_pressure_label.grid(row=10, column=0,padx=5, sticky="W")
    
    tp_temp_label = ttk.Label(infos_frame, text= "- Temperatur: " , font=("Arial", 10))
    tp_temp_label.grid(row=11, column=0,padx=5, sticky="W")

    # Fluidlimits Label
    limit_label = ttk.Label(infos_frame, text="Fluidgrenzen:", font=("Arial", 10, "underline"))
    limit_label.grid(row=12, column=0, padx=5,pady=5, sticky="W")
    
    maxtemp_label = ttk.Label(infos_frame, text="- Max. Druck: ", font=("Arial", 10))
    maxtemp_label.grid(row=16, column=0,padx=5, sticky="W")
    
    mfloatemp_label = ttk.Label(infos_frame, text = "- Max. Temperatur: " ,font=("Arial", 10))
    mfloatemp_label.grid(row=14, column=0,padx=5, sticky="W")
    
    maxp_label = ttk.Label(infos_frame, text= "- Min. Druck: ", font=("Arial", 10))
    maxp_label.grid(row=15, column=0,padx=5, sticky="W")
    
    minp_label = ttk.Label(infos_frame,text="- Min. Temperatur: ", font=("Arial", 10))
    minp_label.grid(row=13, column=0, padx=5,sticky="W")

    maxp=float()
    maxtemp=float()
    minp=float()
    mfloatemp=float()
    
    
    
    def fluid_info(selected_fluid):
        pure_info = CoolProp.get_fluid_param_string(selected_fluid.get(), "pure")
        print(pure_info)
        if pure_info == "true":
            pure_info_label["text"] = "- Reines Fluid: Ja"
        elif pure_info == "false":
            pure_info_label["text"] = "- Reines Fluid: Nein"

        # Molar Mass
        molarmass_info = CoolProp.PropsSI("M", selected_fluid.get())
        molarmass_info_label["text"] = "- Molare Masse: " + str(round(molarmass_info * 1000, 3)) + " g/mol"    #mol masse auf 3 Stellen nach Komma
        gascostant = CoolProp.PropsSI("gas_constant", selected_fluid.get())
        gasconstant_info_label["text"] = "- Spez. Gaskonstante: " + str(round(gascostant / molarmass_info, 1)) + " J/kg*K"    #Gaskonstante auf eine Nachkommastelle genau

        # Critical Point
        ctp_pressure = CoolProp.PropsSI("pcrit", selected_fluid.get())
        ctp_pressure_label["text"] = "- Druck: " + str(round(ctp_pressure,3)) + " Pa"
        ctp_temp = CoolProp.PropsSI("Tcrit", selected_fluid.get())
        ctp_temp_label["text"] = "- Temperatur: " + str(round(ctp_temp,3)) + " Kelvin"
        ctp_den = CoolProp.PropsSI("rhocrit", selected_fluid.get())
        ctp_den_label["text"] = "- Dichte: " + str(round(ctp_den, 3)) + " kg/m³"

        # Triple Point
        tp_pressure = CoolProp.PropsSI("ptriple", selected_fluid.get())
        tp_pressure_label["text"] = "- Druck: " + str(round(tp_pressure, 3)) + " Pa"
        tp_temp = CoolProp.PropsSI("Ttriple", selected_fluid.get())
        tp_temp_label["text"] = "- Temperatur: " + str(round(tp_temp,3)) + " Kelvin"

        # Fluidlimits
       
        maxp = CoolProp.PropsSI("pmax", selected_fluid.get())
        maxp_label["text"] = "- Max. Druck: " + str(round(maxp,3)) + " Pa"
        maxtemp = CoolProp.PropsSI("Tmax", selected_fluid.get())
        maxtemp_label["text"] = "- Max. Temperatur: " + str(round(maxtemp,3)) + " Kelvin"
        minp = CoolProp.PropsSI("pmin", selected_fluid.get())
        minp_label["text"] = "- Min. Druck: " + str(round(minp, 3)) + " Pa"
        mfloatemp = CoolProp.PropsSI("Tmin", selected_fluid.get())
        mfloatemp_label["text"] = "- Min. Temperatur: " + str(round(mfloatemp, 3)) + " Kelvin"
    
    maxtemp = CoolProp.PropsSI("Tmax", selected_fluid.get())
    mfloatemp = CoolProp.PropsSI("Tmin", selected_fluid.get())
    maxp = CoolProp.PropsSI("pmax", selected_fluid.get())
    minp = CoolProp.PropsSI("pmin", selected_fluid.get())


    # Diagramm erstellen-----------------------------------------------------------------------------------
    
    # Diagram Frame
    diagram_frame = ttk.LabelFrame(main_frame, text="Diagramm")
    diagram_frame.grid(row=1, column=2, rowspan=7, columnspan=2, padx=20, pady=1, sticky="nw")
    
    # Isolinien Frame
    iso_frame = ttk.LabelFrame(diagram_frame, text="Isolinien Ein-/Ausblenden")
    iso_frame.grid(row=7, column=1, columnspan=1, padx=10, sticky="W")
    # Set initial state for checkboxes
    
    wertebereich_label = ttk.Label(diagram_frame, text="Wertebereich Diagramm:", font=("Arial", 12, "underline"))
    wertebereich_label.grid(row=0, column=1, columnspan=1, padx=10, sticky="W")
    
    x_ax_label = ttk.Label(diagram_frame, text="1. x-Achse:", font=("Arial", 10))
    x_ax_label.grid(row=1, column=1, columnspan=1, padx=10, sticky="W")
    
    minx_label = ttk.Label(diagram_frame, text="min:", font=("Arial", 10))
    minx_label.grid(row=2, column=1, columnspan=1, padx=10, sticky="W")
    
    minx_var = tk.DoubleVar(value=0)
    minx_entry = ttk.Entry(diagram_frame, textvariable=minx_var, width=10)
    minx_entry.grid(row=2, column=1, columnspan=1, padx=80, sticky="W")
    
    maxx_label = ttk.Label(diagram_frame, text="max:", font=("Arial", 10))
    maxx_label.grid(row=3, column=1, columnspan=1, padx=10, sticky="W")
    
    maxx_var = tk.DoubleVar(value=0)
    maxx_entry = ttk.Entry(diagram_frame, textvariable=maxx_var, width=10)
    maxx_entry.grid(row=3, column=1, columnspan=1, padx=80, sticky="W")
    
    y_ax_label = ttk.Label(diagram_frame, text="2. y-Achse:", font=("Arial", 10))
    y_ax_label.grid(row=4, column=1, columnspan=1, padx=10, sticky="W")
    
    miny_label = ttk.Label(diagram_frame, text="min:", font=("Arial", 10))
    miny_label.grid(row=5, column=1, columnspan=1, padx=10, sticky="W")
    
    miny_var = tk.DoubleVar(value=0)
    miny_entry = ttk.Entry(diagram_frame, textvariable=miny_var, width=10)
    miny_entry.grid(row=5, column=1, columnspan=1, padx=80, sticky="W")
    
    maxy_label = ttk.Label(diagram_frame, text="max:", font=("Arial", 10))
    maxy_label.grid(row=6, column=1, columnspan=1, padx=10, sticky="W")
    
    maxy_var = tk.DoubleVar(value=0)
    maxy_entry = ttk.Entry(diagram_frame, textvariable=maxy_var, width=10)
    maxy_entry.grid(row=6, column=1, columnspan=1, padx=80, sticky="W")
    
    

    # Labels im Diagramm-Frame
    
    diagrams = ["T-s-Diagramm", "log(p)-h-Diagramm", "h-s-Diagramm", "p-T-Diagramm", "T-v-Diagramm", "p-v-Diagramm"]
    diagram_get = []

    # Diagramm Combobox (Auswahl Diagramm)
    selected_diagram = tk.StringVar()
    diagram_combobox = ttk.Combobox(diagram_frame, width=30, textvariable=selected_diagram, values=diagrams, state="readonly")
    diagram_combobox.grid(row=0, column=0, padx=15, sticky="NW")
    diagram_combobox.set("T-s-Diagramm")
   
    def on_select_check():
        create_figure(selected_fluid.get())
        print("")
    
    
    
    isobar_check = tk.Checkbutton(iso_frame, text="Isobare", variable=isobar_var, onvalue=True, offvalue=False, command=on_select_check, selectcolor=stil_isobare["farbe"])
    isobar_check.grid(row=0, column=0, sticky = "W")
    isotherm_check = tk.Checkbutton(iso_frame, text="Isotherme", variable=isotherm_var, onvalue=True, offvalue=False,  command=on_select_check, selectcolor=stil_isotherme["farbe"])
    isotherm_check.grid(row=1, column=0, sticky = "W")
    isochor_check = tk.Checkbutton(iso_frame, text="Isochore", variable=isochor_var, onvalue=True, offvalue=False,  command=on_select_check, selectcolor=stil_isochore["farbe"])
    isochor_check.grid(row=2, column=0, sticky = "W")
    isentropic_check = tk.Checkbutton(iso_frame, text="Isentrope", variable=isentropic_var, onvalue=True, offvalue=False,  command=on_select_check, selectcolor=stil_isentrope["farbe"])
    isentropic_check.grid(row=3, column=0, sticky = "W")
    isenthalpic_check = tk.Checkbutton(iso_frame, text="Isenthalpe", variable=isenthalpic_var, onvalue=True, offvalue=False,  command=on_select_check, selectcolor=stil_isenthalpe["farbe"])
    isenthalpic_check.grid(row=4, column=0, sticky = "W")
    isovapore_check = tk.Checkbutton(iso_frame, text="Isovapore", variable=isovapore_var, onvalue=True, offvalue=False, command=on_select_check, selectcolor=stil_isovapore["farbe"])
    isovapore_check.grid(row=5, column=0, sticky = "W")
    
    
    def mouse_event(event):
        global x_SI, y_SI
        # Sicherstellen, dass Toolbar-Mode abgefragt werden kann
        toolbar = event.canvas.toolbar if hasattr(event.canvas, 'toolbar') else None

        # Abbrechen, wenn gerade gezoomt oder gepannt wird
        if toolbar and toolbar.mode != "":
            return  # Kein eigener Klick, weil Toolbar aktiv ist
        
        x = round(event.xdata, 3)
        y = round(event.ydata, 3)
        eingabe1_var.set(y_SI)
        eingabe2_var.set(x_SI)
       
        
        current_ax.plot(x, y, 'ro')  # ro = red circle
        current_canvas.draw()
        if selected_diagram.get() =="T-s-Diagramm":
            input1_combobox.set("Temperatur T")
            input1unit_label["text"] = temp_unit     
            input2_combobox.set("Spezifische Entropie s")
            input2unit_label["text"] = entropy_unit
            #tree.insert("", "end", values=(x,y))
            calc()
                           
        elif selected_diagram.get() == "log(p)-h-Diagramm":
            input1_combobox.set("Druck p")
            input1unit_label["text"] = pressure_unit
            input2_combobox.set("Spezifische Enthalpie h")
            input2unit_label["text"] = enthalpy_unit
            calc()
            
            
        elif selected_diagram.get() == "h-s-Diagramm":
            input1_combobox.set("Spezifische Enthalpie h")
            input1unit_label["text"] = enthalpy_unit       
            input2_combobox.set("Spezifische Entropie s")
            input2unit_label["text"] = entropy_unit
            calc()

                 
        elif selected_diagram.get() == "p-T-Diagramm":
            input1_combobox.set("Druck p")
            input1unit_label["text"] = pressure_unit     
            input2_combobox.set("Temperatur T")
            input2unit_label["text"] = temp_unit
            calc()
            
            
            
        elif selected_diagram.get() == "T-v-Diagramm":
            input1_combobox.set("Temperatur T")
            input1unit_label["text"] = temp_unit      
            input2_combobox.set("Volumen v")
            input2unit_label["text"] = volume_unit
            calc()
            
        elif selected_diagram.get() == "p-v-Diagramm":
            input1_combobox.set("Druck p")
            input1unit_label["text"] = pressure_unit      
            input2_combobox.set("Volumen v")
            input2unit_label["text"] = volume_unit
            calc()
        
    # diagram(selected_diagram.get())
    toolbar_frame = ttk.LabelFrame(diagram_frame,  relief="flat")
    toolbar_frame.grid(row=8, column=0, sticky="NW")  
    
    
    def get_column_values(columns):
        # Liste der Werte für die angegebene Spalte erstellen
        column_values = []
        
        # Alle Zeilen durchlaufen
        for item_id in tree2.get_children():
            # Die Werte der Zeile abrufen
            item = tree2.item(item_id)
            values = item['values']
            
            # Den Index der gewünschten Spalte finden
            if columns == "temperatur":
                column_values.append(float(values[3]))  
            elif columns == "pressure":
                column_values.append(float(values[4]))  
            elif columns == "volume":
                column_values.append(float(values[6])) 
            elif columns == "enthalpy":
                column_values.append(float(values[8])) 
            elif columns == "entropy":
                column_values.append(float(values[9]))  

        
        return column_values
    

    def calculate_step_size(min_value, max_value):
        range_value = max_value - min_value
        # Bestimme eine geeignete Schrittweite
        if range_value <= 10:
            step_size = 2
        elif range_value <= 100:
            #print("range value kleiner 100")
            step_size = 20
        elif range_value <= 200:
            #print("range value kleiner 100")
            step_size = 40
        elif range_value <= 500:
            #print("range value kleiner 500")
            step_size = 100
        elif range_value <= 1000:
            #print("range value kleiner 1000")
            step_size = 200
        elif range_value <= 1500:
            #print("range value kleiner 1500")
            step_size = 300
        elif range_value <= 3000:
            #print("range value kleiner 3000")
            step_size = 500
        elif range_value <= 5000:
            #print("range value kleiner 5000")
            step_size = 500
        elif range_value <= 10000:
            #print("range value kleiner 10000")
            step_size = 1000
        elif range_value <= 15000:
            #print("range value kleiner 15000")
            step_size = 1500
        elif range_value <= 100000:
            #print("range value kleiner 100000")
            step_size = 10000
        elif range_value <= 1000000:
            #print("range value kleiner 1000000")
            step_size = 100000
        elif range_value <= 2000000:
           # print("range value kleiner 2000000")
            step_size = 200000
        elif range_value <= 5000000:
           # print("range value kleiner 5000000")
            step_size = 500000
        else:
            #print("range value größer 5000000")
            step_size = 2000000 
        # Wenn der Bereich zu groß ist, justiere die Schrittweite
        if range_value / step_size > 20:
            step_size = (range_value // 20)
        # Der Schrittwert muss eine runde Zahl sein (z. B. 10, 50, 100, ...), nicht 33, 37, ...
        step_size = np.round(step_size, -int(np.floor(np.log10(step_size))))  # Runde auf die nächste 10er Potenz
        return step_size

    
    def plot_saturation_lines_general(ax, fluid, diagram_type="T-s-Diagramm", units=None):
        fluid_name = selected_fluid.get() if callable(getattr(fluid, "get", None)) else selected_fluid.get()
        
    
        T_trip = CoolProp.PropsSI("Ttriple", fluid_name)
        T_crit = CoolProp.PropsSI("Tcrit", fluid_name)
        T_range = np.linspace(T_trip , T_crit , 300)
        
        print("T_trip=", T_trip, "T_crit=", T_crit)
        
        data_liq = []
        data_vap = []
        x_vals = []
        h_l, h_v = [], []
        s_l, s_v = [], []
        
        for T in T_range:
            try:
                if diagram_type == "T-s-Diagramm":
                    s_liq = CoolProp.PropsSI("S", "T", T, "Q", 0, fluid_name)
                    s_vap = CoolProp.PropsSI("S", "T", T, "Q", 1, fluid_name)
                    data_liq.append(s_liq)
                    data_vap.append(s_vap)
                    x_vals.append(T)
    
                elif diagram_type == "log(p)-h-Diagramm":
                    h_liq = CoolProp.PropsSI("H", "T", T, "Q", 0, fluid_name)
                    h_vap = CoolProp.PropsSI("H", "T", T, "Q", 1, fluid_name)
                    p = CoolProp.PropsSI("P", "T", T, "Q", 0, fluid_name)
                    data_liq.append(h_liq)
                    data_vap.append(h_vap)
                    x_vals.append(p)
    
                elif diagram_type == "h-s-Diagramm":
                   
                    h_liq = CoolProp.PropsSI("H", "T", T, "Q", 0, fluid_name)
                    h_vap = CoolProp.PropsSI("H", "T", T, "Q", 1, fluid_name)
                    s_liq = CoolProp.PropsSI("S", "T", T, "Q", 0, fluid_name)
                    s_vap = CoolProp.PropsSI("S", "T", T, "Q", 1, fluid_name)
                    h_l.append(h_liq)
                    h_v.append(h_vap)
                    s_l.append(s_liq)
                    s_v.append(s_vap)
                 
                    
                elif diagram_type == "p-T-Diagramm":
                    p = CoolProp.PropsSI("P", "T", T, "Q", 0, fluid_name)
                    data_liq.append(p)
                    x_vals.append(T)
    
                elif diagram_type == "T-v-Diagramm":
                    rho_liq = CoolProp.PropsSI("D", "T", T, "Q", 0, fluid_name)
                    rho_vap = CoolProp.PropsSI("D", "T", T, "Q", 1, fluid_name)
                    v_liq = 1 / rho_liq
                    v_vap = 1 / rho_vap
                    data_liq.append(v_liq)
                    data_vap.append(v_vap)
                    x_vals.append(T)
    
                elif diagram_type == "p-v-Diagramm":
                    p = CoolProp.PropsSI("P", "T", T, "Q", 0, fluid_name)
                    rho_liq = CoolProp.PropsSI("D", "T", T, "Q", 0, fluid_name)
                    rho_vap = CoolProp.PropsSI("D", "T", T, "Q", 1, fluid_name)
                    v_liq = 1 / rho_liq
                    v_vap = 1 / rho_vap
                    data_liq.append((v_liq, p))
                    data_vap.append((v_vap, p))
    
            except:
                continue

        if units is not None:
            def conv_list(values, qtype, unit):
                return [convert_from_SI(val, qtype, unit) for val in values]
    
            if diagram_type == "T-s-Diagramm":
                x_vals = conv_list(x_vals, "temperature", units["y"])
                data_liq = conv_list(data_liq, "entropy", units["x"])
                data_vap = conv_list(data_vap, "entropy", units["x"])
    
            elif diagram_type == "log(p)-h-Diagramm":
                x_vals = conv_list(x_vals, "pressure", units["y"])
                data_liq = conv_list(data_liq, "enthalpy", units["x"])
                data_vap = conv_list(data_vap, "enthalpy", units["x"])
    
            elif diagram_type == "h-s-Diagramm":
                h_l = conv_list(h_l, "enthalpy", units["y"])
                h_v = conv_list(h_v, "enthalpy", units["y"])
                s_l = conv_list(s_l, "entropy", units["x"])
                s_v = conv_list(s_v, "entropy", units["x"])
    
            elif diagram_type == "p-T-Diagramm":
                x_vals = conv_list(x_vals, "temperature", units["x"])
                data_liq = conv_list(data_liq, "pressure", units["y"])
    
            elif diagram_type == "T-v-Diagramm":
                x_vals = conv_list(x_vals, "temperature", units["x"])
                data_liq = conv_list(data_liq, "volume", units["y"])
                data_vap = conv_list(data_vap, "volume", units["y"])
    
            elif diagram_type == "p-v-Diagramm":
                data_liq = [(convert_from_SI(v, "volume", units["x"]), convert_from_SI(p, "pressure", units["y"])) for v, p in data_liq]
                data_vap = [(convert_from_SI(v, "volume", units["x"]), convert_from_SI(p, "pressure", units["y"])) for v, p in data_vap]


        # Plotten je nach Diagrammtyp
        if diagram_type == "h-s-Diagramm":
            ax.plot(s_l, h_l, label="Siedelinie (Q=0)", color=stil_siedelinie["farbe"], linewidth=float(stil_siedelinie["dicke"]), linestyle=stil_siedelinie["stil"], zorder=8)
            ax.plot(s_v, h_v, label="Taulinie (Q=1)", color=stil_taulinie["farbe"], linewidth=float(stil_taulinie["dicke"]), linestyle=stil_taulinie["stil"], zorder=8)
    
        elif diagram_type == "p-v-Diagramm":
            v_liq, p_vals = zip(*data_liq)
            v_vap, _ = zip(*data_vap)
            ax.plot(v_liq, p_vals, label="Siedelinie (Q=0)", color=stil_siedelinie["farbe"], linewidth=float(stil_siedelinie["dicke"]), linestyle=stil_siedelinie["stil"],zorder=8)
            ax.plot(v_vap, p_vals, label="Taulinie (Q=1)", color=stil_taulinie["farbe"], linewidth=float(stil_taulinie["dicke"]), linestyle=stil_taulinie["stil"], zorder=8)
    
        elif diagram_type == "p-T-Diagramm":
            ax.plot(x_vals, data_liq, label="Dampfdruckkurve", color=stil_siedelinie["farbe"],linewidth=float(stil_siedelinie["dicke"]), linestyle=stil_siedelinie["stil"], zorder=8)
    
        else:
            ax.plot(data_liq, x_vals, label="Siedelinie (Q=0)", color=stil_siedelinie["farbe"],linewidth=float(stil_siedelinie["dicke"]), linestyle=stil_siedelinie["stil"], zorder=8)
            ax.plot(data_vap, x_vals, label="Taulinie (Q=1)", color=stil_taulinie["farbe"], linewidth=float(stil_taulinie["dicke"]), linestyle=stil_taulinie["stil"], zorder=8)
    
        # Tripelpunkt
        try:
            T_t = T_trip
            if diagram_type == "T-s-Diagramm":
                s = convert_from_SI(CoolProp.PropsSI("S", "T", T_t, "Q", 0, fluid_name), "entropy", entropy_unit)
                if units is not None:
                    s = conv_list(s, "entropy", units["x"])   
                ax.scatter(s, T_t, label="Tripelpunkt", color=stil_tripel["farbe"], marker=stil_tripel["marker"], s=stil_tripel["größe"] * 5, zorder=9)
            elif diagram_type == "log(p)-h-Diagramm":
                h = CoolProp.PropsSI("H", "T", T_t, "Q", 0, fluid_name)
                p = CoolProp.PropsSI("P", "T", T_t, "Q", 0, fluid_name)
                if units is not None:
                    p = conv_list(p, "pressure", units["y"])
                    h = conv_list(h, "enthalpy", units["x"])
                ax.scatter(h, p, label="Tripelpunkt", color=stil_tripel["farbe"], marker=stil_tripel["marker"], s=stil_tripel["größe"] * 5, zorder=9)
            elif diagram_type == "h-s-Diagramm":
                s = CoolProp.PropsSI("S", "T", T_t, "Q", 0, fluid_name)
                h = CoolProp.PropsSI("H", "T", T_t, "Q", 0, fluid_name)
                if units is not None:
                    h = conv_list(h, "enthalpy", units["y"])
                    s = conv_list(s, "entropy", units["x"])
                ax.scatter(s, h,label="Tripelpunkt", color=stil_tripel["farbe"], marker=stil_tripel["marker"], s=stil_tripel["größe"] * 5, zorder=9)
            elif diagram_type == "p-T-Diagramm":
                p = CoolProp.PropsSI("P", "T", T_t, "Q", 0, fluid_name)
                if units is not None:
                    T_t = conv_list(T_t, "temperature", units["x"])
                    p = conv_list(p, "pressure", units["y"])
                ax.scatter(T_t, p, label="Tripelpunkt", color=stil_tripel["farbe"], marker=stil_tripel["marker"], s=stil_tripel["größe"] * 5, zorder=9)
            elif diagram_type in ["T-v-Diagramm", "p-v-Diagramm"]:
                
                rho = CoolProp.PropsSI("D", "T", T_t, "Q", 0, fluid_name)
                v = 1 / rho
                p = CoolProp.PropsSI("P", "T", T_t, "Q", 0, fluid_name)
                if diagram_type == "T-v-Diagramm":                   
                    y = T_t 
                    if units is not None: y = conv_list(y, "temperature", units["x"])
                else:
                    y=p
                    if units is not None: y = conv_list(y, "pressure", units["y"])
                if diagram_type == "T-v-Diagramm":   
                    x = v 
                    if units is not None:x = conv_list(x, "volume", units["y"])
                else: 
                    x= v
                    if units is not None: x = conv_list(x, "volume", units["y"])
                ax.scatter(x, y, label="Tripelpunkt", color=stil_tripel["farbe"], marker=stil_tripel["marker"], s=stil_tripel["größe"] * 5, zorder=9)
        except:
            pass
    
        # Kritischer Punkt
        try:
            T_c = T_crit
            if diagram_type == "T-s-Diagramm":
                s = CoolProp.PropsSI("S", "T", T_c, "Q", 0, fluid_name)
                if units is not None:
                    s = conv_list(s, "entropy", units["x"])  
                
                ax.scatter(s, T_c, label="Kritischer Punkt",color=stil_krit["farbe"], marker=stil_krit["marker"], s=stil_krit["größe"] * 5, zorder=9)#color=stil_krit["farbe"], marker=stil_krit["marker"], s=stil_krit["größe"]
            elif diagram_type == "log(p)-h-Diagramm":
                h = CoolProp.PropsSI("H", "T", T_c, "Q", 0, fluid_name)
                p = CoolProp.PropsSI("P", "T", T_c, "Q", 0, fluid_name)
                if units is not None:
                    p = conv_list(p, "pressure", units["y"])
                    h = conv_list(h, "enthalpy", units["x"])
                ax.scatter(h, p, label="Kritischer Punkt",color=stil_krit["farbe"], marker=stil_krit["marker"], s=stil_krit["größe"] * 5, zorder=9)
            elif diagram_type == "h-s-Diagramm":
                s = CoolProp.PropsSI("S", "T", T_c, "Q", 0, fluid_name)
                h = CoolProp.PropsSI("H", "T", T_c, "Q", 0, fluid_name)
                if units is not None:
                    h = conv_list(h, "enthalpy", units["y"])
                    s = conv_list(s, "entropy", units["x"])
                ax.scatter(s, h, label="Kritischer Punkt",color=stil_krit["farbe"], marker=stil_krit["marker"], s=stil_krit["größe"] * 5, zorder=9)
            elif diagram_type == "p-T-Diagramm":
                p = CoolProp.PropsSI("P", "T", T_c, "Q", 1, fluid_name)
                if units is not None:
                    T_c = conv_list(T_c, "temperature", units["x"])
                    p = conv_list(p, "pressure", units["y"])
                ax.scatter(T_c, p,label="Kritischer Punkt",color=stil_krit["farbe"], marker=stil_krit["marker"], s=stil_krit["größe"] * 5, zorder=9)
            elif diagram_type in ["T-v-Diagramm", "p-v-Diagramm"]:
                rho = CoolProp.PropsSI("D", "T", T_c, "Q", 0, fluid_name)
                v = 1 / rho
    
                p = CoolProp.PropsSI("P", "T", T_c, "Q", 0, fluid_name)

                if diagram_type == "T-v-Diagramm":                   
                    y = T_c 
                    if units is not None: y = conv_list(y, "temperature", units["y"])
                else:
                    y=p
                    if units is not None: y = conv_list(y, "pressure", units["y"])
                if diagram_type == "T-v-Diagramm":   
                    x = v 
                    if units is not None:x = conv_list(x, "volume", units["x"])
                else: 
                    x= v
                    if units is not None: x = conv_list(x, "volume", units["x"])
                ax.scatter(x, y, label="Kritischer Punkt",color=stil_krit["farbe"], marker=stil_krit["marker"], s=stil_krit["größe"] * 5, zorder=9)
        except:
            pass
    
    
        handles, labels = ax.get_legend_handles_labels()
        # if handles and legende_set.get() == True:
        #     ax.legend()
        if handles and legende_set.get():
            #print("Legende in create_figure")
            ax.legend()
    
    
  
    def generate_isolines_general(fluid_name,ax,x_range,y_range,isoline_type,num_lines=5,x_axis='S',y_axis='T',fixpoint1=None,fixpoint2=None):

        
        # Achsen-Übersetzung
        axis_map = {
            'T': 'T',
            'P': 'P',
            'S': 'S',
            'H': 'H',
            'V': 'Dmass'  # wird später in 1/rho umgerechnet
        }
        
        for item_id in tree2.get_children():
            values = tree2.item(item_id)["values"]
            

        y_name = axis_map.get(y_axis.upper())
        x_name = axis_map.get(x_axis.upper())  
        
        print("Der übergebene IsolineTyp ist: ", isoline_type)
        
        def convert_axis_input(axis_name, value):
            if axis_name.upper() == 'V':
                return 'Dmass', 1.0 / value
            return axis_name, value


        def get_prop(prop, var1, val1, var2, val2):
                try:
                    return CoolProp.PropsSI(str(prop), str(var1), float(val1), str(var2), float(val2), str(fluid_name))
                except:
                    return None
       
    
        def get_volume(T, P):
            rho = get_prop("Dmass", "T", T, "P", P)
            if rho and rho > 0:
                return 1.0 / rho
            return None
        
        if isoline_type == 'isobar':
            if fixpoint1 and fixpoint2:
                X1, Y1 = fixpoint1
                X2, Y2 = fixpoint2
        
                X1 = float(X1) #Volumen1
                X2 = float(X2) #Volumen2
                Y1 = float(Y1) #Druck1
                Y2 = float(Y2) #Druck2
                
                P_const = Y1  # Y1=Y2 da isobar
        
                # Unterstützte Fälle
                if x_axis.upper() == "V" and y_axis.upper() == "P":

                    v_vals = np.linspace(X1, X2, 300)
                    p_vals = []
        
                    for v in v_vals:
                        rho = 1.0 / v  # Dichte
                        p = get_prop("P", "P", P_const, "Dmass", rho)
                        print("P=", p)
                        if p and np.isfinite(p):
                            p_vals.append(p)
                        else:
                            p_vals.append(np.nan)
        
                    ax.plot(v_vals, p_vals, linestyle="-", linewidth=1.5, color="black")
                    
        
                elif x_axis.upper() == "S" and y_axis.upper() == "T":
                    s_vals = np.linspace(X1, X2, 300)  # Entropie von Punkt 1 zu Punkt 2
                    t_vals = []  # Temperatur
                    p = get_prop("P", y_name, float(Y1), x_name, float(X1))
                    for s in s_vals:
                        T = get_prop("T", "P", p, "S", s)
                        #print("s=", s, "T=",T)
                        if T and np.isfinite(T):
                            t_vals.append(T)
                            #print("test")
                        else:
                            t_vals.append(np.nan)
                    #print("Gültige Punkte:", sum([1 for t in t_vals if not np.isnan(t)]))

                    ax.plot(s_vals, t_vals,  linestyle="-", linewidth=1.5, color="black", zorder=8)
                    return

            else:
            # Standardmodus ohne fixierte Punkte
                num_lines= int(stil_isobare["anzahl"])
                p_vals = np.logspace(np.log10(1000), np.log10(CoolProp.PropsSI("pcrit", fluid_name)), num_lines)
                for p in p_vals:
                    x_list, y_list = [], []
                    y_vals = np.linspace(y_range[0], y_range[1], 300)
                    for y in y_vals:
                        #y_input_name, y_input_val = convert_axis_input(y_name, y_val)
                        if x_axis.upper() == 'V':
                            T = y if y_name == 'T' else get_prop("T", y_name, y, "P", p)
                            x_val = get_volume(T, p) if T else None
                        else:
                            x_val = get_prop(x_name, y_name, y, "P", p)
                        if x_val:
                            x_list.append(x_val)
                            y_list.append(y)
                    ax.plot(x_list, y_list, color=stil_isobare["farbe"], linewidth=float(stil_isobare["dicke"]), linestyle=stil_isobare["stil"], zorder=8)
                    mid = len(x_list) // 3
                    ax.text(x_list[-mid], y_list[-mid], f'{p/1000:.1f} kPa', fontsize=9, color="black", rotation=45)
       

        elif isoline_type == 'isotherm':
            if fixpoint1 and fixpoint2:
                X1, Y1 = fixpoint1
                X2, Y2 = fixpoint2
                X1 =float(X1)
                Y1 =float(Y1)
                X2 =float(X2)
                Y2 =float(Y2)
                if x_axis.upper() == "S" and y_axis.upper() == "T":
                    p1 = get_prop("P", y_name, Y1, x_name, X1)
                    p2 = get_prop("P", y_name, Y2, x_name, X2)
                    p_vals = np.linspace(p1, p2, 300)
                    x_list, y_list = [], []
        
                    for p in p_vals:
                        x_val = get_prop(x_name, y_name, Y1, "P", p) if x_axis.upper() != 'V' else get_volume(X1, p)
                        y_val = get_prop(y_name, y_name, Y1, "P", p) if y_axis.upper() != 'V' else get_volume(Y1, p)
                        if x_val and y_val:
                            x_list.append(x_val)
                            y_list.append(y_val)
        
                    ax.plot(x_list, y_list, linestyle="-", linewidth=1.5, color="black", zorder=8)
        
                elif x_axis.upper() == "V" and y_axis.upper() == "P":
                    v_vals = np.linspace(X1, X2, 300)
                    p_vals = []
                    rho=1/X1
                    T = get_prop("T", "P", Y1, "Dmass",rho)
        
                    for v in v_vals:
                        rho = 1.0 / v  # Dichte
                        p = get_prop("P", "T", T, "Dmass", rho)
        
                        if p and np.isfinite(p):
                            p_vals.append(p)
                        else:
                            p_vals.append(np.nan)
        
                    ax.plot(v_vals, p_vals, linestyle="-", linewidth=1.5, color="black", zorder=8)
                    
                    return
            
            
            
            
            else:
                num_lines= int(stil_isotherme["anzahl"])
                T_vals = np.linspace(CoolProp.PropsSI("Ttriple", fluid_name) + 1, CoolProp.PropsSI("Tcrit", fluid_name) - 1, num_lines)
                for T in T_vals:
                    x_list, y_list = [], []
                    p_vals = np.logspace(3, np.log10(CoolProp.PropsSI("pcrit", fluid_name)), 300)
                    for p in p_vals:
                        x_val = get_prop(x_axis, "T", T, "P", p) if x_axis.upper() != 'V' else get_volume(T, p)
                        y_val = get_prop(y_axis, "T", T, "P", p) if y_axis.upper() != 'V' else get_volume(T, p)
                        if x_val and y_val and x_val > 0 and y_val > 0:
                            x_list.append(x_val)
                            y_list.append(y_val)
                    ax.plot(x_list, y_list, color=stil_isotherme["farbe"], linewidth=float(stil_isotherme["dicke"]), linestyle=stil_isotherme["stil"], zorder=8)
                    if selected_diagram.get() =="log(p)-h-Diagramm":
                        ax.text(x_list[-10], y_list[-10], f'{T:.1f} K', fontsize=9, color="black", rotation=45)
                    elif selected_diagram.get() == "h-s-Diagramm":
                        ax.text(x_list[100], y_list[100], f'{T:.1f} K', fontsize=9, color="black")
                    elif selected_diagram.get() == "p-v-Diagramm":
                        ax.text(x_list[100], y_list[100], f'{T:.1f} K', fontsize=9, color="black")
        

        elif isoline_type == 'isentrope' or isoline_type == "isentrop":
            if fixpoint1 and fixpoint2:
                X1, Y1 = fixpoint1
                X2, Y2 = fixpoint2
                X1 = float(X1)
                X2 = float(X2)
                Y1 = float(Y1)
                Y2 = float(Y2)
                print("Y1=", Y1, "Y2=", Y2)
                y_vals = np.linspace(float(Y1), float(Y2), 300)
                rho1= 1/X1

                s = get_prop("S", y_name, Y1, "Dmass", rho1)
                
                x_list, y_list = [], []
                for y in y_vals:
                    if x_name=="S":
                        x_val=X1
                        x_list.append(x_val)
                        y_list.append(y)
                    else :   
                        x_help = get_prop("Dmass", y_name, y, "S", s)
                        if x_help is not None and x_help != 0:
                            x_val =1/x_help
                            x_list.append(x_val)
                            y_list.append(y)
    
                    #y_list.append(y)
                ax.plot(x_list, y_list, linestyle="-", linewidth=1.5, color="black", zorder=8)
                return


            else:
                num_lines= int(stil_isochore["anzahl"])
                T_vals = np.linspace(CoolProp.PropsSI("Ttriple", fluid_name) + 1, CoolProp.PropsSI("Tcrit", fluid_name) - 1, 100)
                s_vals = []
                for T in T_vals:
                    try:
                        s_vals.append(CoolProp.PropsSI("S", "T", T, "Q", 0, fluid_name))
                        s_vals.append(CoolProp.PropsSI("S", "T", T, "Q", 1, fluid_name))
                    except:
                        continue
                if not s_vals:
                    return
                s_vals = np.linspace(min(s_vals), max(s_vals), num_lines)
                for s in s_vals:
                    x_list, y_list = [], []
                    y_vals = np.logspace(np.log10(y_range[0]), np.log10(y_range[1]), 500)
                    for y_val in y_vals:
                        y_input_name, y_input_val = convert_axis_input(y_axis, y_val)
                        x_val = get_prop(x_axis, y_input_name, y_input_val, "S", s)
                        if x_val:
                            x_list.append(x_val)
                            y_list.append(y_val)
                    ax.plot(x_list, y_list, color=stil_isentrope["farbe"], linewidth=float(stil_isentrope["dicke"]), linestyle=stil_isentrope["stil"], zorder=8)
                    mid = len(x_list) // 10
                    ax.text(x_list[mid], y_list[mid], f'{s:.1f} J/kg*K', fontsize=9, color="black", rotation=45)
    
        # Isochor (konstante Dichte)
        elif isoline_type == 'isochor':
            if fixpoint1 and fixpoint2:
                X1, Y1 = fixpoint1
                X2, Y2 = fixpoint2

                rho = get_prop("Dmass", y_name, Y1, x_name, X1) #rechnen Dichte aus an Punkt 1
                if not rho:
                    return
                y_vals = np.linspace(float(Y1), float(Y2), 300)
                x_list, y_list = [], []
                for y in y_vals:
                    x_val = get_prop(x_name, y_name, y, "Dmass", rho)
                    if x_val:
                        x_list.append(x_val)
                        y_list.append(y)
                ax.plot(x_list, y_list, linestyle="-", linewidth=1.5, color="black", zorder=8)
                return
            else: 
                num_lines= int(stil_isochore["anzahl"])
                rho_vals = np.logspace(-1, 3, num_lines)
                for rho in rho_vals:
                    x_list, y_list = [], []

                    if selected_diagram.get()=="T-s-Diagramm" or selected_diagram.get()=="h-s-Diagramm" or selected_diagram.get()=="p-T-Diagramm":
                        y_vals = np.linspace(y_range[0], y_range[1], 300)
                    elif selected_diagram.get()=="log(p)-h-Diagramm":
                        y_vals = np.logspace(np.log10(minp), np.log10(y_range[1]), 500)
                    for y_val in y_vals:
                        y_input_name, y_input_val = convert_axis_input(y_axis, y_val)
                        x_val = get_prop(x_axis, y_input_name, y_input_val, "Dmass", rho)
                        if x_val:
                            x_list.append(x_val)
                            y_list.append(y_val)
                    ax.plot(x_list, y_list, color=stil_isochore["farbe"], linewidth=float(stil_isochore["dicke"]), linestyle=stil_isochore["stil"], zorder=8)
  
                    if selected_diagram.get() == "p-T-Diagramm":
                        ax.text(x_list[13], y_list[13], f'{rho:.1f} m³/kg', fontsize=9, color="black", rotation=45)
                    elif selected_diagram.get()== "log(p)-h-Diagramm" :
                        mid = len(x_list) // 3
                        ax.text(x_list[mid], y_list[mid], f'{rho:.1f} m³/kg', fontsize=9, color="black", rotation=45)
                    elif selected_diagram.get()== "h-s-Diagramm":
                        mid = len(x_list) // 6
                        ax.text(x_list[-mid], y_list[-mid], f'{rho:.1f} m³/kg', fontsize=9, color="black", rotation=45)
                    else:
                        ax.text(x_list[-10], y_list[-10], f'{rho:.1f} m³/kg', fontsize=9, color="black", rotation=45)    
                    
        # Isenthalpe
        elif isoline_type == 'isenthalpe':
            num_lines= int(stil_isenthalpe["anzahl"])
            h_vals = np.linspace(100e3, CoolProp.PropsSI("Hcrit", fluid_name), num_lines)
            for h in h_vals:
                x_list, y_list = [], []
                y_vals = np.linspace(y_range[0], y_range[1], 300)
                for y_val in y_vals:
                    y_input_name, y_input_val = convert_axis_input(y_axis, y_val)
                    x_val = get_prop(x_axis, y_input_name, y_input_val, "H", h)
                    if x_val:
                        x_list.append(x_val)
                        y_list.append(y_val)
                ax.plot(x_list, y_list, color=stil_isenthalpe["farbe"], linewidth=float(stil_isenthalpe["dicke"]), linestyle=stil_isenthalpe["stil"], zorder=8)
                ax.text(x_list[-10], y_list[-10], f'{h:.1f} J/kg', fontsize=9, color="black", rotation=45)
                
        # Isovapor (konstanter Dampfgehalt)
        elif isoline_type == 'isovapor':
            num_lines= int(stil_isovapore["anzahl"])
            q_vals = np.linspace(0.1, 0.9, num_lines)
            T_trip = CoolProp.PropsSI("Ttriple", fluid_name)
            T_crit = CoolProp.PropsSI("Tcrit", fluid_name)
            for q in q_vals:
                x_list, y_list = [], []
                for T in np.linspace(T_trip, T_crit, 300):
                    x_val = get_prop(x_axis, "T", T, "Q", q)
                    y_val = get_prop(y_axis if y_axis != 'V' else 'Dmass', "T", T, "Q", q)
                    if y_axis == 'V' and y_val: y_val = 1.0 / y_val
                    if x_val and y_val:
                        x_list.append(x_val)
                        y_list.append(y_val)
                ax.plot(x_list, y_list,  color=stil_isovapore["farbe"], linewidth=float(stil_isovapore["dicke"]), linestyle=stil_isovapore["stil"], zorder=8)
                ax.text(x_list[10], y_list[10], f'{q:.1f}', fontsize=9, color="black", rotation=45)
    
    def check_input():
        try:
            # Alle Eingaben als Strings behandeln
            if ("," in str(eingabe1_var.get()) or
                "," in str(eingabe2_var.get()) or
                "," in minx_entry.get() or
                "," in maxx_entry.get() or
                "," in miny_entry.get() or
                "," in maxy_entry.get()):
                tkinter.messagebox.showwarning("Warnung", "Bitte einen Punkt als Komma nehmen!")
                return False
        except Exception as e:
            print(f"Fehler in check_input: {e}")
            return False
        return True
    checkbox_vars_diagramm =[isobar_var, isotherm_var, isochor_var, isentropic_var, isenthalpic_var, isovapore_var] 
    
   

    def draw_isoline_connections_from_tree(fluid_name, tree, ax, x_axis, y_axis):
        tree_column_map = {
            'T': 3,
            'P': 4,
            'D': 5,
            'V': 6,
            'H': 8,
            'S': 9,
        }
    
        selected_item = tree2.focus()  # Aktuell ausgewählte Zeile
        if not selected_item:
            print("Keine Zeile ausgewählt.")
            return
        
        values = tree2.item(selected_item)["values"]
        try:
            isoline_type = str(values[0]).lower()
            from_id = str(values[1])
            to_id = str(values[2])
    
            from_x_val_raw = values[tree_column_map.get(x_axis.upper())]
            from_y_val_raw = values[tree_column_map.get(y_axis.upper())]
            from_x_val = convert_to_SI(from_x_val_raw, x_axis.lower(), globals().get(f"{x_axis.lower()}_unit"))
            from_y_val = convert_to_SI(from_y_val_raw, y_axis.lower(), globals().get(f"{y_axis.lower()}_unit"))
    
            # Zielpunkt (to_id) im Tree finden
            to_item = next(
                (i for i in tree2.get_children() if str(tree2.item(i)["values"][1]) == to_id), None
            )
            if not to_item:
                print("Zielpunkt nicht gefunden.")
                return
    
            to_values = tree2.item(to_item)["values"]
            to_x_val_raw = to_values[tree_column_map.get(x_axis.upper())]
            to_y_val_raw = to_values[tree_column_map.get(y_axis.upper())]
            to_x_val = convert_to_SI(to_x_val_raw, x_axis.lower(), globals().get(f"{x_axis.lower()}_unit"))
            to_y_val = convert_to_SI(to_y_val_raw, y_axis.lower(), globals().get(f"{y_axis.lower()}_unit"))
    
            fixpoint1 = (from_x_val, from_y_val)
            fixpoint2 = (to_x_val, to_y_val)
    
            # Zeichnen
            generate_isolines_general(fluid_name=fluid_name, ax=ax, x_range=None, y_range=None,
                                      isoline_type=isoline_type, num_lines=1,
                                      x_axis=x_axis, y_axis=y_axis,
                                      fixpoint1=fixpoint1, fixpoint2=fixpoint2)
            # Isolinie merken
            persisted_isolines.append({
                "fluid_name": fluid_name,
                "isoline_type": isoline_type,
                "x_axis": x_axis,
                "y_axis": y_axis,
                "fixpoint1": fixpoint1,
                "fixpoint2": fixpoint2
            })
    
            print("Isolinie gezeichnet:", isoline_type, from_id, "->", to_id)
    
        except Exception as e:
            print(f"Fehler beim Zeichnen der ausgewählten Isolinien-Verbindung: {e}")

    def on_draw_selected_isoline_button_click():
        # Sicherstellen, dass current_ax und current_canvas existieren
        if current_ax is None or current_canvas is None:
            print("Es wurde noch kein Diagramm erstellt.")
            return
    
        ax = current_ax
        fig = current_canvas.figure
    
        # Dynamisch bestimmen, welche Achsen benutzt werden sollen
        selected = selected_diagram.get()
        if selected == "T-s-Diagramm":
            x_axis = 'S'
            y_axis = 'T'
        elif selected == "p-v-Diagramm":
            x_axis = 'V'
            y_axis = 'P'
        else:
            print(f"Diagrammtyp '{selected}' nicht unterstützt für Isolinien.")
            return
    
        draw_isoline_connections_from_tree(
            fluid_name=selected_fluid.get(),
            tree=tree2,
            ax=ax,
            x_axis=x_axis,
            y_axis=y_axis
        )
    
        current_canvas.draw()


    def redraw_persisted_isolines(ax):
        for isoline in persisted_isolines:
            try:
                generate_isolines_general(
                    fluid_name=isoline["fluid_name"],
                    ax=ax,
                    x_range=None,
                    y_range=None,
                    isoline_type=isoline["isoline_type"],
                    num_lines=1,
                    x_axis=isoline["x_axis"],
                    y_axis=isoline["y_axis"],
                    fixpoint1=isoline["fixpoint1"],
                    fixpoint2=isoline["fixpoint2"]
                )
            except Exception as e:
                print(f"Fehler beim erneuten Zeichnen einer Isolinie: {e}")
            

    def create_figure(selected, highlight_point=False):
        #reset_isoline_checkboxes()
        update_units()
        
            
        fig = plt.Figure(figsize=(6, 4), dpi=65)
        ax = fig.add_subplot(111)
        
        T_raw = get_column_values("temperatur")
        s_raw = get_column_values("entropy")
        p_raw = get_column_values("pressure")
        h_raw = get_column_values("enthalpy")
        v_raw = get_column_values("volume")
        #convertieren in SI
        T = [convert_to_SI(t, "temperature", temp_unit) for t in T_raw]
        s = [convert_to_SI(x, "entropy", entropy_unit) for x in s_raw]
        p = [convert_to_SI(p, "pressure", pressure_unit) for p in p_raw]
        h = [convert_to_SI(h, "enthalpy", enthalpy_unit) for h in h_raw]
        v = [convert_to_SI(v, "volume", volume_unit) for v in v_raw]
        
        # T = get_column_values("temperatur")
        # s = get_column_values("entropy")
       # p = get_column_values("pressure")
       # h = get_column_values("enthalpy")
       # v = get_column_values("volume")
        
        if check_input() == False:  # Falls check_input False zurückgibt, abbrechen
            return

        minx_raw = minx_var.get()# werte des Wertebereichs des Diagrammes
        maxx_raw = maxx_var.get()
        miny_raw = miny_var.get()
        maxy_raw = maxy_var.get()
        
        minx=0
        maxx=0
        miny=0
        maxy=0
        
      
        if selected == "T-s-Diagramm":
            ax.clear()
            
            minx = [convert_to_SI(minx_raw, "entropy",  entropy_unit)]
            maxx = [convert_to_SI(maxx_raw, "entropy", entropy_unit)]
            miny = [convert_to_SI(miny_raw, "temperature", temp_unit)]
            maxy = [convert_to_SI(maxy_raw, "temperature", temp_unit)]

            fig = plt.Figure(figsize=(6, 4), dpi=65)
            ax = fig.add_subplot(111)
            #plot_siedetaulinien(ax, selected_fluid)
            plot_saturation_lines_general(ax, selected_fluid, diagram_type="T-s-Diagramm")
            ax.scatter(s, T, label="Daten", color=stil_daten["farbe"], marker=stil_daten["marker"], s=stil_daten["größe"] * 5, zorder=10)
            # Alle Punkte mit Labels versehen
            for i, (ent, temp) in enumerate(zip(s, T)): #punkte beschriften
                try:
                    label = tree2.item(tree2.get_children()[i])["values"][1]  # z.B. erste Spalte = Zustandsname
                    ax.annotate(label, (ent, temp), textcoords="offset points", xytext=(0, 5), ha='left', fontsize=9)
                except IndexError:
                    pass  # falls Treeview weniger Einträge hat als s/T oder umgekehrt

            ax.set_title("T-s Diagramm")
            ax.set_xlabel(axis_names["entropy"])  
            ax.set_ylabel(axis_names["temperatur"])
            ax.tick_params(axis='x', labelrotation=45)
            ax.tick_params(axis='y', labelrotation=45)

            if not T or not s:  # Prüft, ob eine der Listen leer ist, bei leerer Liste gibts fehler
                T = [270, 700]  # Beispielwerte für Temperatur
                s = [0, 9000]  # Beispielwerte für Entropie
            # Berechnung der minimalen und maximalen Werte, falls noch keine Werte angegeben sind

            if not minx_var.get() and not maxx_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden, max und min werte des Wertebereichs der Tabelle
                minx = 0
                maxx = 9000 
            else:
                minx = float(minx[0])
                maxx = float(maxx[0])
            if not miny_var.get() and not maxy_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden
                miny = 270
                maxy = 700
            else:
                miny = float(miny[0])
                maxy = float(maxy[0])
            
            
            #draw_isoline_connections_from_tree( fluid_name=selected_fluid.get(), tree=tree,  ax=ax, x_axis='S',y_axis='T')
            if persisted_isolines:
                redraw_persisted_isolines(ax)

            if highlight_point and selected_row_values:
                temperatur_raw = float(selected_row_values[3])
                entropy_raw = float(selected_row_values[9])
                temperatur = [convert_to_SI(temperatur_raw, "temperature", temp_unit)]
                entropy = [convert_to_SI(entropy_raw, "entropy",  entropy_unit)]
                ax.scatter(entropy, temperatur, label="ausgewählt", color=stil_datenaus["farbe"], marker=stil_datenaus["marker"], s=stil_datenaus["größe"] * 5, zorder=10)

            
            # if selected_row_values: #damit ausgewählter Punkt blau wird
            #     temperatur_raw = float(selected_row_values[3])
            #     entropy_raw = float(selected_row_values[9])
            #     temperatur =[convert_to_SI(temperatur_raw, "temperature", temp_unit)]
            #     entropy= [convert_to_SI(entropy_raw, "entropy",  entropy_unit)]
            #     ax.scatter(entropy, temperatur, label="ausgewählt", c='cyan', marker='o', s=10, zorder=10)
            #     #plt.plot(entropy, temperatur, 'ro')  # ro = red circle

            try:
                isobar_check.config(state='normal')    # aktivieren
                isotherm_check.config(state='disabled')
                isochor_check.config(state='normal')
                isentropic_check.config(state='disabled')
                isenthalpic_check.config(state='disabled')
                isovapore_check.config(state='normal')
            except Exception as e:
                 print("Error while plotting points:", e)    

             # If Checkbox is activated plot Isolines
            try:
                x_range = (float(minx), float(maxx))
                y_range = (float(miny), float(maxy))
                if isobar_var.get() == True :
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isobar', num_lines=10, x_axis='S', y_axis='T', fixpoint1=None, fixpoint2=None)

                if isovapore_var.get()== True :
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isovapor', num_lines=10, x_axis='S', y_axis='T', fixpoint1=None,fixpoint2=None)
                if isochor_var.get()== True :
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isochor', num_lines=10, x_axis='S', y_axis='T', fixpoint1=None,fixpoint2=None)
                    
            except Exception as e:
                print("Error while plotting points:", e)   
            
        elif selected == "log(p)-h-Diagramm":
            minx = [convert_to_SI(minx_raw, "enthalpy",  enthalpy_unit)]
            maxx = [convert_to_SI(maxx_raw, "enthalpy",  enthalpy_unit)]
            miny = [convert_to_SI(miny_raw, "pressure", pressure_unit)]
            maxy = [convert_to_SI(maxy_raw, "pressure", pressure_unit)]
            
            fig = plt.Figure(figsize=(6, 4), dpi=65)
            ax = fig.add_subplot(111)
            #plot_siedetaulinien_ph(ax, selected_fluid)
            plot_saturation_lines_general(ax, selected_fluid, diagram_type="log(p)-h-Diagramm")
            ax.scatter(h, p, label="Daten", color=stil_daten["farbe"], marker=stil_daten["marker"], s=stil_daten["größe"] * 5, zorder=10)
            for i, (ent, temp) in enumerate(zip(h, p)):
                try:
                    label = tree2.item(tree2.get_children()[i])["values"][1]  # z.B. erste Spalte = Zustandsname
                    ax.annotate(label, (ent, temp), textcoords="offset points", xytext=(0, 5), ha='left', fontsize=9)
                except IndexError:
                    pass  # falls Treeview weniger Einträge hat
            ax.set_title("log(p)-h Diagramm")
            ax.set_xlabel(axis_names["enthalpy"])  
            ax.set_ylabel(axis_names["pressure"])
            
            ax.set_yscale('log')

            ax.tick_params(axis='x', labelrotation=45)
            ax.tick_params(axis='y', labelrotation=45)
            
            if not h or not p:  # Prüft, ob eine der Listen leer ist, bei leerer Liste gibts fehler
                h = [0, 3000000]  # Beispielwerte
                p = [500, 50000000]  # Beispielwerte 
            # Berechnung der minimalen und maximalen Werte, falls noch keine Werte angegeben sind
            
            if not minx_var.get() and not maxx_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden, max und min werte des Wertebereichs der Tabelle
                minx = 0
                maxx = 3000000
            else:
                minx = float(minx[0])
                maxx = float(maxx[0]) 
            if not miny_var.get() and not maxy_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden
                miny = 500
                maxy = 50000000
            else:
                miny = float(miny[0])
                maxy = float(maxy[0])
                
           
            
            if selected_row_values: #damit ausgewählter Punkt blau wird
                enthalpy_raw = float(selected_row_values[8])
                pressure_raw = float(selected_row_values[4])
                enthalpy =[convert_to_SI(enthalpy_raw, "enthalpy", enthalpy_unit)]
                pressure =[convert_to_SI(pressure_raw, "pressure", pressure_unit)]
                ax.scatter(enthalpy, pressure, label="ausgewählt", color=stil_datenaus["farbe"], marker=stil_datenaus["marker"], s=stil_datenaus["größe"] * 5, zorder=10)
                #plt.plot(entropy, temperatur, 'ro')  # ro = red circl
        
            try:
                isobar_check.config(state='disabled')    # aktivieren
                isotherm_check.config(state='normal')
                isochor_check.config(state='normal')
                isentropic_check.config(state='normal')
                isenthalpic_check.config(state='disabled')
                isovapore_check.config(state='normal')

            except:
                pass
            
            try:
                x_range = (float(minx), float(maxx))
                y_range = (float(miny), float(maxy))

                if isentropic_var.get()==True:
                    # generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isentrope', num_lines=10)
                    # generate_isolines_ph(selected_fluid, ax, x_range, y_range, isoline_type='isentrope', num_lines=10)
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isentrope', num_lines=10, x_axis='H', y_axis='P')
                if isotherm_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isotherm', num_lines=10)
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isotherm', num_lines=10, x_axis='H', y_axis='P')
                if isovapore_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isovapor', num_lines=10)
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isovapor', num_lines=10, x_axis='H', y_axis='P')
                if isochor_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isochor', num_lines=10)
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isochor', num_lines=10, x_axis='H', y_axis='P')
            except:
                pass 

            
            
        elif selected == "h-s-Diagramm":
            miny = [convert_to_SI(miny_raw, "enthalpy",  enthalpy_unit)]
            maxy = [convert_to_SI(maxy_raw, "enthalpy",  enthalpy_unit)]
            minx = [convert_to_SI(minx_raw, "entropy", entropy_unit)]
            maxx = [convert_to_SI(maxx_raw, "entropy", entropy_unit)]
            
            fig = plt.Figure(figsize=(6, 4), dpi=65)
            ax = fig.add_subplot(111)
            plot_saturation_lines_general(ax, selected_fluid, diagram_type="h-s-Diagramm")
            #plot_siedetaulinien_hs(ax, selected_fluid)
            
            ax.scatter(s, h, label="Daten", color=stil_daten["farbe"], marker=stil_daten["marker"], s=stil_daten["größe"] * 5, zorder=10)
            for i, (ent, temp) in enumerate(zip(s, h)):
                try:
                    label = tree2.item(tree2.get_children()[i])["values"][1]  # z.B. erste Spalte = Zustandsname
                    ax.annotate(label, (ent, temp), textcoords="offset points", xytext=(0, 5), ha='left', fontsize=9)
                except IndexError:
                    pass  # falls Treeview weniger Einträge hat
            ax.set_title("h-s Diagramm")
            ax.set_xlabel(axis_names["entropy"])  
            ax.set_ylabel(axis_names["enthalpy"])

            ax.tick_params(axis='x', labelrotation=45)
            ax.tick_params(axis='y', labelrotation=45)
            if not s or not h:  # Prüft, ob eine der Listen leer ist, bei leerer Liste gibts fehler
                h = [0, 3000000]  # Beispielwerte
                s = [0, 9200]  # Beispielwerte 
            # Berechnung der minimalen und maximalen Werte, falls noch keine Werte angegeben sind
            
            if not minx_var.get() and not maxx_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden, max und min werte des Wertebereichs der Tabelle
                minx = 0
                maxx = 9200
            else:
                minx = float(minx[0])
                maxx = float(maxx[0])  
            if not miny_var.get() and not maxy_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden
                miny = 0
                maxy = 3000000
            else:
                miny = float(miny[0])
                maxy = float(maxy[0])
                
           
            
            if selected_row_values: #damit ausgewählter Punkt blau wird           
                enthalpy_raw = float(selected_row_values[8])
                entropy_raw = float(selected_row_values[9])
                enthalpy =[convert_to_SI(enthalpy_raw, "enthalpy",  enthalpy_unit)]
                entropy =[convert_to_SI(entropy_raw, "entropy",  entropy_unit)]
                ax.scatter(entropy, enthalpy,label="ausgewählt", color=stil_datenaus["farbe"], marker=stil_datenaus["marker"], s=stil_datenaus["größe"] * 5, zorder=10)
                #plt.plot(entropy, temperatur, 'ro')  # ro = red circlv

            try:
                isobar_check.config(state='normal')    # aktivieren
                isotherm_check.config(state='normal')
                isochor_check.config(state='normal')
                isentropic_check.config(state='disabled')
                isenthalpic_check.config(state='disabled')
                isovapore_check.config(state='normal')

            except:
                pass
            
            try:
                x_range = (float(minx), float(maxx))
                y_range = (float(miny), float(maxy))
                if isobar_var.get()==True:
                   # generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isobar', num_lines=10)
                   generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                       isoline_type='isobar', num_lines=10, x_axis='S', y_axis='H')
                if isotherm_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isotherm', num_lines=10) 
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isotherm', num_lines=10, x_axis='S', y_axis='H')
                if isovapore_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isovapor', num_lines=10)
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isovapor', num_lines=10, x_axis='S', y_axis='H')
                if isochor_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isochor', num_lines=10)
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isochor', num_lines=10, x_axis='S', y_axis='H')

            except:
                pass
            
        
            
        elif selected == "p-T-Diagramm":
            minx = [convert_to_SI(minx_raw, "temperature", temp_unit)]
            maxx = [convert_to_SI(maxx_raw, "temperature", temp_unit)]
            miny = [convert_to_SI(miny_raw, "pressure", pressure_unit)]
            maxy = [convert_to_SI(maxy_raw, "pressure", pressure_unit)]

            fig = plt.Figure(figsize=(6, 4), dpi=65)
            ax = fig.add_subplot(111)
            #plot_saturation_lines(ax, selected_fluid)
            plot_saturation_lines_general(ax, selected_fluid, diagram_type="p-T-Diagramm")
            ax.scatter(T, p, label="Daten",color=stil_daten["farbe"], marker=stil_daten["marker"], s=stil_daten["größe"] * 5, zorder=10)
            for i, (ent, temp) in enumerate(zip(T, p)):
                try:
                    label = tree2.item(tree2.get_children()[i])["values"][1]  # gibt punkten eine Nummer im Diagramm
                    ax.annotate(label, (ent, temp), textcoords="offset points", xytext=(0, 5), ha='left', fontsize=9)
                except IndexError:
                    pass  # falls Treeview weniger Einträge hat
            ax.set_title("p-T Diagramm")
            ax.set_xlabel(axis_names["temperatur"])  
            ax.set_ylabel(axis_names["pressure"])

            ax.tick_params(axis='x', labelrotation=45)
            ax.tick_params(axis='y', labelrotation=45)
            if not T or not p:  # Prüft, ob eine der Listen leer ist, bei leerer Liste gibts fehler
                T = [200, 650]  # Beispielwerte
                p = [0, 23000000]  # Beispielwerte 
            # Berechnung der minimalen und maximalen Werte, falls noch keine Werte angegeben sind
            
            if not minx_var.get() and not maxx_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden, max und min werte des Wertebereichs der Tabelle
                minx = 200
                maxx = 650
            else:
                minx = float(minx[0])
                maxx = float(maxx[0]) 
            if not miny_var.get() and not maxy_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden
                miny = 0
                maxy = 23000000
            else:
                miny = float(miny[0])
                maxy = float(maxy[0])
                
           
            
            if selected_row_values: #damit ausgewählter Punkt blau wird           
                temperatur_raw = float(selected_row_values[3])
                pressure_raw = float(selected_row_values[4])
                temperatur =[convert_to_SI(temperatur_raw, "temperature", temp_unit)]
                pressure = [convert_to_SI(pressure_raw, "pressure",  pressure_unit)] 
                ax.scatter(temperatur, pressure, label="ausgewählt",color=stil_datenaus["farbe"], marker=stil_datenaus["marker"], s=stil_datenaus["größe"] * 5, zorder=10)
                #plt.plot(entropy, temperatur, 'ro')  # ro = red circl
            
            try:
                isobar_check.config(state='disabled')    # aktivieren
                isotherm_check.config(state='disabled')
                isochor_check.config(state='normal')
                isentropic_check.config(state='disabled')
                isenthalpic_check.config(state='disabled')
                isovapore_check.config(state='disabled')
                

            except:
                pass
            
            try:
                x_range = (float(minx), float(maxx))
                y_range = (float(miny), float(maxy))
                if isochor_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isochor', num_lines=10)
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isochor', num_lines=10, x_axis='T', y_axis='P')
            except:
                pass
            
        elif selected == "T-v-Diagramm":
            minx = [convert_to_SI(minx_raw, "volume", volume_unit)]
            maxx = [convert_to_SI(maxx_raw, "volume", volume_unit)]
            miny = [convert_to_SI(miny_raw, "temperature", temp_unit)]
            maxy = [convert_to_SI(maxy_raw, "temperature", temp_unit)]
            
            fig = plt.Figure(figsize=(6, 4), dpi=65)
            ax = fig.add_subplot(111)
            #plot_boiling_and_dew_lines(ax, selected_fluid)
            plot_saturation_lines_general(ax, selected_fluid, diagram_type="T-v-Diagramm")
            ax.scatter(v, T, label="Daten", color=stil_daten["farbe"], marker=stil_daten["marker"], s=stil_daten["größe"] * 5, zorder=10)
            for i, (ent, temp) in enumerate(zip(v, T)):
                try:
                    label = tree2.item(tree2.get_children()[i])["values"][1]  # z.B. erste Spalte = Zustandsname
                    ax.annotate(label, (ent, temp), textcoords="offset points", xytext=(0, 5), ha='left', fontsize=9)
                except IndexError:
                    pass  # falls Treeview weniger Einträge hat
            ax.set_xscale('log')
            ax.set_title("T-v Diagramm")
            ax.set_xlabel(axis_names["volume"])  
            ax.set_ylabel(axis_names["temperatur"])

            ax.tick_params(axis='x', labelrotation=45)
            ax.tick_params(axis='y', labelrotation=45)
            if not T or not v:  # Prüft, ob eine der Listen leer ist, bei leerer Liste gibts fehler
                T = [200, 700]  # Beispielwerte
                v = [0.001, 1000 ]  # Beispielwerte 
            # Berechnung der minimalen und maximalen Werte, falls noch keine Werte angegeben sind
            
            if not minx_var.get() and not maxx_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden, max und min werte des Wertebereichs der Tabelle
                minx = 0.0001
                maxx = 1000
            else:
                minx = float(minx[0])
                maxx = float(maxx[0]) 
            if not miny_var.get() and not maxy_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden
                miny = 200
                maxy = 700
            else:
                miny = float(miny[0])
                maxy = float(maxy[0])
              
            
            
            if selected_row_values: #damit ausgewählter Punkt blau wird
                volume_raw = float(selected_row_values[6])
                temperatur_raw = float(selected_row_values[3])
                volume = [convert_to_SI(volume_raw, "volume",  volume_unit)] 
                temperatur =[convert_to_SI(temperatur_raw, "temperature", temp_unit)]
                ax.scatter(volume, temperatur,label="ausgewählt", color=stil_datenaus["farbe"], marker=stil_datenaus["marker"], s=stil_datenaus["größe"] * 5, zorder=10)
                #plt.plot(entropy, temperatur, 'ro')  # ro = red circl
            
            
            try:
                isobar_check.config(state='normal')    # aktivieren
                isotherm_check.config(state='disabled')
                isochor_check.config(state='disabled')
                isentropic_check.config(state='disabled')
                isenthalpic_check.config(state='disabled')
                isovapore_check.config(state='disabled')
                
        
            except:
                pass
            
            try:
                x_range = (float(minx), float(maxx))
                y_range = (float(miny), float(maxy))
                if isobar_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isobar', num_lines=10) 
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isobar', num_lines=10, x_axis='V', y_axis='T')
                
            except:
                pass 
        
        elif selected == "p-v-Diagramm":
            minx = [convert_to_SI(minx_raw, "volume", volume_unit)]
            maxx = [convert_to_SI(maxx_raw, "volume", volume_unit)]
            miny = [convert_to_SI(miny_raw, "pressure", pressure_unit)]
            maxy = [convert_to_SI(maxy_raw, "pressure", pressure_unit)]
            
            fig = plt.Figure(figsize=(6, 4), dpi=65)
            ax = fig.add_subplot(111)
            #plot_boiling_and_dew_lines_pv(ax, selected_fluid)
            plot_saturation_lines_general(ax, selected_fluid, diagram_type="p-v-Diagramm")
            ax.scatter(v, p, label="Daten", color=stil_daten["farbe"], marker=stil_daten["marker"], s=stil_daten["größe"] * 5, zorder=10)
            for i, (ent, temp) in enumerate(zip(v, p)):
                try:
                    label = tree2.item(tree2.get_children()[i])["values"][1]  # z.B. erste Spalte = Zustandsname
                    ax.annotate(label, (ent, temp), textcoords="offset points", xytext=(0, 5), ha='left', fontsize=9)
                except IndexError:
                    pass  # falls Treeview weniger Einträge hat
            ax.set_xscale('log')
            ax.set_title("p-v Diagramm")
            ax.set_xlabel(axis_names["volume"])  
            ax.set_ylabel(axis_names["pressure"])
            
            ax.tick_params(axis='x', labelrotation=45)
            ax.tick_params(axis='y', labelrotation=45)
            if not p or not v:  # Prüft, ob eine der Listen leer ist, bei leerer Liste gibts fehler
                p = [0, 23000000]  # Beispielwerte
                v = [0.001, 1000 ]  # Beispielwerte 
            # Berechnung der minimalen und maximalen Werte, falls noch keine Werte angegeben sind
            
            if not minx_var.get() and not maxx_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden, max und min werte des Wertebereichs der Tabelle
                minx = 0.0001
                maxx = 1000
            else:
                minx = float(minx[0])
                maxx = float(maxx[0])
            if not miny_var.get() and not maxy_var.get():  # Falls keine benutzerdefinierten Werte gesetzt wurden
                miny = 0
                maxy = 23000000
            else:
                miny = float(miny[0])
                maxy = float(maxy[0])
                
            #draw_isoline_connections_from_tree(fluid_name=selected_fluid.get(), tree=tree,  ax=ax, x_axis='V',y_axis='P')
            if persisted_isolines:
                redraw_persisted_isolines(ax)
            
            
            
            if highlight_point and selected_row_values:
                volume_raw = float(selected_row_values[6])
                pressure_raw = float(selected_row_values[4])
                volume = [convert_to_SI(volume_raw, "volume",  volume_unit)]
                pressure = [convert_to_SI(pressure_raw, "pressure", pressure_unit)]
                ax.scatter(volume, pressure, label="ausgewählt", color=stil_datenaus["farbe"], marker=stil_datenaus["marker"], s=stil_datenaus["größe"] * 5, zorder=10)
                #plt.plot(entropy, temperatur, 'ro')  # ro = red circl
            
            
            try:
                isobar_check.config(state='disabled')    # aktivieren
                isotherm_check.config(state='normal')
                isochor_check.config(state='disabled')
                isentropic_check.config(state='disabled')
                isenthalpic_check.config(state='disabled')
                isovapore_check.config(state='disabled')
                
        
            except:
                pass
            
            try:
                x_range = (float(minx), float(maxx))
                y_range = (float(miny), float(maxy))
                
                if isotherm_var.get()==True:
                    #generate_isolines(selected_fluid, ax, x_range, y_range, isoline_type='isovapore', num_lines=10)
                    generate_isolines_general(fluid_name=selected_fluid.get(), ax=ax, x_range=(minx, maxx), y_range=(miny, maxy),
                        isoline_type='isotherm', num_lines=10, x_axis='V', y_axis='P')
                
            except:
                pass 
            
            
        
        # Wertebereich der Achsen setzen mit 10 Pixel Puffer
        # ACHSENSKALEN: Limits setzen

        if minx == maxx:
            minx -= 0.5
            maxx += 0.5
        if miny == maxy:
            miny -= 0.5
            maxy += 0.5
        
        #print("minx=", minx, ", maxx= ", maxx,"miny=", miny, ", maxy=", maxy)
        ax.set_xlim(minx, maxx)
        ax.set_ylim(miny , maxy)
        
        # --- X-ACHSE ---
        if ax.get_xscale() == 'log':
            ax.set_xscale('log')
            ax.xaxis.set_major_locator(LogLocator(base=10.0, numticks=10))
            ax.xaxis.set_major_formatter(LogFormatter(base=10.0))
            ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs='auto', numticks=10))
            xticks = ax.get_xticks()
            # ax.set_xlim(minx, maxx)
            # ax.set_ylim(miny , maxy)
        else:
            x_step = calculate_step_size(minx, maxx)
            xticks = np.arange(minx, maxx + x_step, x_step)
            ax.set_xticks(xticks)
            ax.xaxis.set_minor_locator(AutoMinorLocator())
            # ax.set_xlim(minx, maxx )
            # ax.set_ylim(miny , maxy)
        
        # --- Y-ACHSE ---
        if ax.get_yscale() == 'log':
            ax.set_yscale('log')
            ax.yaxis.set_major_locator(LogLocator(base=10.0, numticks=10))
            ax.yaxis.set_major_formatter(LogFormatter(base=10.0))
            ax.yaxis.set_minor_locator(LogLocator(base=10.0, subs='auto', numticks=10))
            yticks = ax.get_yticks()
            # ax.set_xlim(minx , maxx)
            # ax.set_ylim(miny , maxy)
        else:
            y_step = calculate_step_size(miny, maxy)
            yticks = np.arange(miny, maxy + y_step, y_step)
            ax.set_yticks(yticks)
            ax.yaxis.set_minor_locator(AutoMinorLocator())
            # ax.set_xlim(minx, maxx)
            # ax.set_ylim(miny , maxy)

        if selected == "T-s-Diagramm":
            xtick_labels = [round(convert_from_SI(val, "entropy", entropy_unit),1) for val in xticks]
            ytick_labels = [round(convert_from_SI(val, "temperature", temp_unit),1) for val in yticks]
        elif selected == "log(p)-h-Diagramm":
            xtick_labels = [round(convert_from_SI(val, "enthalpy", enthalpy_unit),1) for val in xticks]
            ytick_labels = [round(convert_from_SI(val, "pressure", pressure_unit),1) for val in yticks]
        elif selected == "h-s-Diagramm":
            xtick_labels = [round(convert_from_SI(val, "entropy", entropy_unit),1) for val in xticks]
            ytick_labels = [round(convert_from_SI(val, "enthalpy", enthalpy_unit),1) for val in yticks]
        elif selected == "p-T-Diagramm":
            xtick_labels = [round(convert_from_SI(val, "temperature", temp_unit),1) for val in xticks]
            ytick_labels = [round(convert_from_SI(val, "pressure", pressure_unit),1) for val in yticks]
        elif selected == "T-v-Diagramm":
            xtick_labels = [round(convert_from_SI(val, "volume", volume_unit),1) for val in xticks]
            ytick_labels = [round(convert_from_SI(val, "temperature", temp_unit),1) for val in yticks]
        elif selected == "p-v-Diagramm":
            xtick_labels = [round(convert_from_SI(val, "volume", volume_unit),1) for val in xticks]
            ytick_labels = [round(convert_from_SI(val, "pressure", pressure_unit),1) for val in yticks]
        else :
            xtick_labels = xticks
            ytick_labels = yticks

        def custom_formatter(unit, label_func):
            def formatter(val, pos):
                converted = label_func(val, unit)
                if abs(converted) >= 10000 or abs(converted) < 0.01:
                    return f"{converted:.0e}"
                else:
                    return f"{converted:.4f}".rstrip("0").rstrip(".")
            return FuncFormatter(formatter)
        
        # X-Achse
        if ax.get_xscale() == 'log':
            if selected == "log(p)-h-Diagramm":
                ax.xaxis.set_major_formatter(custom_formatter(enthalpy_unit, lambda v, u: convert_from_SI(v, "enthalpy", u)))
            elif selected == "T-v-Diagramm":
                ax.xaxis.set_major_formatter(custom_formatter(volume_unit, lambda v, u: convert_from_SI(v, "volume", u)))
            elif selected == "p-v-Diagramm":
                ax.xaxis.set_major_formatter(custom_formatter(volume_unit, lambda v, u: convert_from_SI(v, "volume", u)))
            
        else:
            ax.set_xticklabels(xtick_labels, rotation=45)
        
        # Y-Achse
        if ax.get_yscale() == 'log':
            if selected == "log(p)-h-Diagramm":
                ax.yaxis.set_major_formatter(custom_formatter(pressure_unit, lambda v, u: convert_from_SI(v, "pressure", u)))
            elif selected == "T-v-Diagramm":
                ax.yaxis.set_major_formatter(custom_formatter(temp_unit, lambda v, u: convert_from_SI(v, "temperature", u)))
            elif selected == "p-v-Diagramm":
                ax.yaxis.set_major_formatter(custom_formatter(pressure_unit, lambda v, u: convert_from_SI(v, "pressure", u)))
   
            
        else:
            ax.set_yticklabels(ytick_labels, rotation=45)
        
        # Gitterlinien aktivieren und an die Ticks anpassen
        ax.grid(True, which='major', axis='both', linestyle='--', color='gray', linewidth=0.5)
        ax.grid(True, which='minor', axis='both', linestyle='--', color='lightgray', linewidth=0.5)
        handles, labels = ax.get_legend_handles_labels()
        if handles and legende_set.get():
            print("Legende in create_figure")
            ax.legend()
        #fig.subplots_adjust(left=0.17, right=0.9, top=0.94, bottom=0.17)    #15% vom linken rand entfernt und 0.1 vom rechten entfernt
        margins = get_subplot_settings()
        fig.subplots_adjust(
            left=margins["left"],
            right=margins["right"],
            top=margins["top"],
            bottom=margins["bottom"])
        
        return fig, ax  # Rückgabe der Figure und Axes
    

    
    
    class CursorAnnotation:
        def __init__(self, ax, diagram_type):
            self.ax = ax
            self.diagram_type = diagram_type  # z. B. "T-s-Diagramm"
            self.annotation = ax.annotate('', xy=(0, 0), xytext=(10, -10),
                                          textcoords='offset points',
                                          bbox=dict(boxstyle="round", fc="w"),
                                          arrowprops=dict(arrowstyle="->"), zorder=11)
            self.annotation.set_visible(False)
    
        def update(self, event):
            global x_SI, y_SI
            if event.inaxes == self.ax:
                x, y = event.xdata, event.ydata
                if x is not None and y is not None:
                    mouse_x_px = event.x
                    mouse_y_px = event.y
                    canvas_width, canvas_height = event.canvas.get_width_height()
    
                    offset_x = 20
                    offset_y = 20
    
                    if mouse_x_px > canvas_width * 0.6:
                        offset_x = -110
                    if mouse_y_px < canvas_height * 0.35:
                        offset_y = 40
                    elif mouse_y_px > canvas_height * 0.8:
                        offset_y = -36
    
                    self.annotation.set_position((offset_x, offset_y))
                    self.annotation.xy = (x, y)
                    
                    selected=selected_diagram.get()
                    if selected == "T-s-Diagramm":
                        x_SI = round(convert_from_SI(x, "entropy", entropy_unit),4) 
                        y_SI = round(convert_from_SI(y, "temperature", temp_unit),4)
                    elif selected == "log(p)-h-Diagramm":
                        x_SI = round(convert_from_SI(x, "enthalpy", enthalpy_unit),4) 
                        y_SI = round(convert_from_SI(y, "pressure", pressure_unit),4) 
                    elif selected == "h-s-Diagramm":
                        x_SI = round(convert_from_SI(x, "entropy", entropy_unit),4)
                        y_SI = round(convert_from_SI(y, "enthalpy", enthalpy_unit),4) 
                    elif selected == "p-T-Diagramm":
                        x_SI = round(convert_from_SI(x, "temperature", temp_unit),4)
                        y_SI = round(convert_from_SI(y, "pressure", pressure_unit),4) 
                    elif selected == "T-v-Diagramm":
                        x_SI = round(convert_from_SI(x, "volume", volume_unit),4) 
                        y_SI = round(convert_from_SI(y, "temperature", temp_unit),4) 
                    elif selected == "p-v-Diagramm":
                        x_SI = round(convert_from_SI(x, "volume", volume_unit),4) 
                        y_SI = round(convert_from_SI(y, "pressure", pressure_unit),4)
                    else :
                        x_SI = x
                        y_SI = y
    
                    # Umrechnung + Einheiten
                    x_label, x_unit, x_val = self.get_axis_info(x, axis='x')
                    y_label, y_unit, y_val = self.get_axis_info(y, axis='y')
    
                    self.annotation.set_text(f"{x_label} = {x_val:.3f} {x_unit}\n{y_label} = {y_val:.2f} {y_unit}")
                    self.annotation.set_visible(True)
                    event.canvas.draw()
                else:
                    self.annotation.set_visible(False)
                    event.canvas.draw()
            else:
                # Tooltip ausblenden, wenn Maus außerhalb des Diagramms
                self.annotation.set_visible(False)
                event.canvas.draw()
    
        def get_axis_info(self, value, axis='x'):
            # Mapping für Diagrammtyp → Achsenbezeichnungen, SI-Typen und Einheiten
            mapping = {
                "T-s-Diagramm": {'x': ('s', 'entropy', entropy_unit), 'y': ('T', 'temperature', temp_unit)},
                "log(p)-h-Diagramm": {'x': ('h', 'enthalpy', enthalpy_unit), 'y': ('p', 'pressure', pressure_unit)},
                "h-s-Diagramm": {'x': ('s', 'entropy', entropy_unit), 'y': ('h', 'enthalpy', enthalpy_unit)},
                "p-T-Diagramm": {'x': ('T', 'temperature', temp_unit), 'y': ('p', 'pressure', pressure_unit)},
                "T-v-Diagramm": {'x': ('v', 'volume', volume_unit), 'y': ('T', 'temperature', temp_unit)},
                "p-v-Diagramm": {'x': ('v', 'volume', volume_unit), 'y': ('p', 'pressure', pressure_unit)},
            }
    
            # Fallback für alles andere
            label, typ, unit = mapping.get(self.diagram_type, {}).get(axis, (axis, None, ''))
    
            if typ is not None:
                value_converted = convert_from_SI(value, typ, unit)
            else:
                value_converted = value
    
            return label, unit, value_converted

    
    def on_move(event):
        cursor_annotation.update(event)
       


    def show_diagram(*args):
        global current_ax, current_canvas, canvas_widget, fig, cursor_annotation, persisted_isolines
        update_units()
        # Vorherigen Plot löschen
        for widget in diagram_canvas_frame.winfo_children():
            widget.destroy()

        for widget in toolbar_frame.winfo_children():
            widget.destroy()

        # Größe des Frames holen (in Pixeln)
        diagram_canvas_frame.update_idletasks()
        frame_width = diagram_canvas_frame.winfo_width()
        frame_height = diagram_canvas_frame.winfo_height()

        #print(f"Frame size: {frame_width} x {frame_height}")  # Debugging-Ausgabe

        # Falls noch 1x0 bei Start, Fallback-Werte setzen
        if frame_width < 1 or frame_height < 1:
            frame_width, frame_height = 250, 250  # Defaultwerte

        # DPI für Matplotlib
        dpi = 100

        # Berechne die Größe der Matplotlib-Figur in Zoll
        fig_width_inch = frame_width / dpi
        fig_height_inch = frame_height / dpi

        #print(f"Figure size in inches: {fig_width_inch} x {fig_height_inch}")  # Debugging-Ausgabe

        # Holen der Auswahl, z.B. von einem Dropdown oder einer Auswahlbox
        selected = selected_diagram.get()  # Hier wird die Auswahl verwendet

        # Erstellen der Figure mit den ausgewählten Daten
        #fig, ax = create_figure(selected)
        fig, ax = create_figure(selected, highlight_point=True)


        # Das Diagramm im Canvas rendern
        canvas = FigureCanvasTkAgg(fig, master=diagram_canvas_frame)
        canvas.draw()

        # Canvas im Frame anzeigen und Größe setzen
        canvas_widget = canvas.get_tk_widget()

        # Hier wird explizit die Canvas-Größe gesetzt
        canvas_widget.config(width=frame_width, height=frame_height)
        
        # Sicherstellen, dass der Canvas den gesamten Frame ausfüllt
        canvas_widget.pack(fill='both', expand=True)

        units_dict = {
            "temperature": temp_unit,
            "pressure": pressure_unit,
            "volume": volume_unit,
            "entropy": entropy_unit,
            "enthalpy": enthalpy_unit
            }
        cursor_annotation = CursorAnnotation(fig.gca(), selected_diagram.get())
         # # Verbinde die Funktion mit dem Mausbewegungs-Event
        fig.canvas.mpl_connect('motion_notify_event', on_move)
        
        # Toolbar hinzufügen
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame, pack_toolbar=False)
        toolbar.update()
        toolbar.grid(row=0, column=0, sticky="W")
        
        if hasattr(canvas, "toolbar"): #damit in der Toolbar die Koordinaten nicht mehr angezeigt werden
            canvas.toolbar.set_message = lambda s: None
        
        cid = fig.canvas.mpl_connect("button_press_event", mouse_event)
        #cid = fig.canvas.mpl_connect("motion_notify_event", mouse_event1)
        
        current_ax = ax
        current_canvas = canvas
    entry_fields = [minx_entry, miny_entry, maxx_entry, maxy_entry]

    def on_select_legend():
        print("Legende testen", legende_var.get())
        global legende_set
        if legende_var.get():
            print("Legende aktivieren", legende_var.get())
            legende_set.set(True)
        else:
                legende_set.set(False)
        show_diagram()
    
    def new_diagram(event=None):
        for var in checkbox_vars_diagramm:  # Liste von BooleanVar(), z. B.
            var.set(False)
        for entry in entry_fields:  # Liste vorher definieren!
            entry.delete(0, tk.END)
            entry.insert(0, "0")
        show_diagram()
        
    legende_check = tk.Checkbutton(diagram_frame, text="Legende", variable=legende_var, onvalue=True, offvalue=False, command=on_select_legend)
    legende_check.grid(row=0, column=0, padx=(220,0), sticky = "W")
    
    # Event-Handler für Auswahländeru
    diagram_combobox.bind("<<ComboboxSelected>>", new_diagram)

    diagram_canvas_frame = ttk.Frame(diagram_frame,width=300, height=300)
    diagram_canvas_frame.grid(row=1, column=0, pady=5, columnspan=1, rowspan=7, sticky="W")
    diagram_canvas_frame.grid_propagate(False)  # Verhindert automatische Größenanpassung des Frames

    # Direkt beim Start Diagramm anzeigen
    show_diagram()
    


    def on_click(event):
         if event.button is MouseButton.LEFT:
             print('disconnecting callback')
             plt.disconnect(binding_id)


    binding_id = plt.connect('motion_notify_event', on_move)
    plt.connect('button_press_event', on_click)

    
    #def zustand_hinzufügen():
        

    #Berechnungen-------------------------------------------------------------------
    
    # Berechnung to the Labels
    calc_temp=0
    calc_s=0
    calc_p=0
    calc_h=0
    calc_d=0
    
    def calc():
        
        fluid_info(selected_fluid)#setzt Fluidinfo

        
        if check_input() == False:  # Falls check_input False zurückgibt, abbrechen
            return
    
        try:
            variable1 = selected_variable1.get()
            variable2 = selected_variable2.get()
            
            if variable1 == "Temperatur T":
                inconst_value = convert_to_SI(float(eingabe1_var.get()), "temperature", temp_unit)
            elif variable1 == "Druck p":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "pressure", pressure_unit)
            elif variable1 == "Dichte rho":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "density", density_unit)
            elif variable1 == "Spezifische Enthalpie h":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "enthalpy",  enthalpy_unit)
            elif variable1 == "Spezifische Entropie s":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "entropy",  entropy_unit)
            elif variable1 == "Innere Energie u":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "internal_energy", i_energy_unit)
            elif variable1 == "Cp":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "cp", cp_unit)
            elif variable1 == "Cv":
                inconst_value =convert_to_SI(float(eingabe1_var.get()),"cv", cv_unit)
            elif variable1 == "Volumen v":
                inconst_value =convert_to_SI(float(eingabe1_var.get()), "volume", volume_unit)
            else:
                inconst_value = float(eingabe1_var.get())
                
            
            if variable2 == "Temperatur T":
                const_value = convert_to_SI(float(eingabe2_var.get()), "temperature", temp_unit)
            elif variable2 == "Druck p":
                const_value = convert_to_SI(float(eingabe2_var.get()), "pressure",pressure_unit)
            elif variable2 == "Dichte rho":
                const_value = convert_to_SI(float(eingabe2_var.get()), "density",density_unit)
            elif variable2 == "Spezifische Enthalpie h":
                const_value = convert_to_SI(float(eingabe2_var.get()), "enthalpy",enthalpy_unit)
            elif variable2 == "Spezifische Entropie s":
                const_value = convert_to_SI(float(eingabe2_var.get()),"entropy",entropy_unit)
            elif variable2 == "Innere Energie u":
                const_value = convert_to_SI(float(eingabe2_var.get()),"internal_energy", i_energy_unit)
            elif variable2 == "Cp":
                const_value = convert_to_SI(float(eingabe2_var.get()),"cp", cp_unit)
            elif variable2 == "Cv":
                const_value = convert_to_SI(float(eingabe2_var.get()),"cv", cv_unit)
            elif variable2 == "Volumen v":
                const_value = convert_to_SI(float(eingabe2_var.get()),"volume", volume_unit)
            else:
                const_value = float(eingabe2_var.get())
                
           
            
            if variable1 == variable2:
                tkinter.messagebox.showwarning("Warnung", "Bitte zwei unterschiedliche Variablen zur Berechnung wählen!")
                return
                
            elif (variable1, variable2) in [("Spezifische Enthalpie h", "Temperatur T"), ("Temperatur T", "Spezifische Enthalpie h"), 
                                            ("Spezifische Entropie s", "Dampfqualität x"), ("Dampfqualität x", "Spezifische Entropie s"),
                                            ("Innere Energie u", "Temperatur T"),("Temperatur T","Innere Energie u" ),
                                            ("Innere Energie u", "Spezifische Enthalpie h"),("Spezifische Enthalpie h","Innere Energie u" ),
                                            ("Innere Energie u", "Spezifische Entropie s"),("Spezifische Entropie s","Innere Energie u" ),
                                            ("Innere Energie u", "Dampfqualität x"),("Dampfqualität x","Innere Energie u" ),
                                            ("Volumen v", "Dichte rho"), ("Dichte rho", "Volumen v")]:
                tkinter.messagebox.showwarning("Warnung", "Dieses Paar von Eingabevariablen ist nicht möglich! Bitte eine andere Kombination wählen.")
                return
            else:
                input1_code = get_input_code(variable1)
                input2_code = get_input_code(variable2)
                
            if not check_limits(variable1, variable2, const_value, inconst_value, maxtemp, mfloatemp, maxp, minp):
                return    
                
            if variable1 == "Volumen v":    # v umrechnen dass damit auch als eingabe gerechnet werden kann
                #helpdensity = 1/eingabe1_var.get()
                input1_code = "D"
                #inconst_value = helpdensity
                inconst_value = 1/inconst_value
            elif variable2 == "Volumen v":
                #helpdensity = 1/eingabe2_var.get()
                input2_code = "D"
                #const_value = helpdensity
                const_value = 1/const_value

            try:
                #print(input1_code, inconst_value, input2_code, const_value)
                calc_temp = CoolProp.PropsSI("T", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_p = CoolProp.PropsSI("P", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())                                    
                calc_d = CoolProp.PropsSI("D", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_h = CoolProp.PropsSI("H", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_s = CoolProp.PropsSI("S", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_x = CoolProp.PropsSI("Q", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())*100
                calc_u = CoolProp.PropsSI("U", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_vis = CoolProp.PropsSI("V", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_cp = CoolProp.PropsSI("CPMASS", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_cv = CoolProp.PropsSI("CVMASS", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                calc_v = 1/ (CoolProp.PropsSI("D", input1_code, inconst_value, input2_code, const_value, selected_fluid.get()))
                calc_state = CoolProp.PropsSI("PHASE", input1_code, inconst_value, input2_code, const_value, selected_fluid.get())
                
                
                
                calc_temp = convert_from_SI(calc_temp, "temperature", temp_unit)
                calc_p = convert_from_SI(calc_p, "pressure", pressure_unit)#Temperatur in gewählte Einheit zurück umwandeln
                calc_d = convert_from_SI(calc_d, "density", density_unit)
                calc_h = convert_from_SI(calc_h, "enthalpy", enthalpy_unit)
                calc_s = convert_from_SI(calc_s, "entropy", entropy_unit)
                calc_u = convert_from_SI(calc_u, "internal_energy", i_energy_unit)
                calc_cp = convert_from_SI(calc_cp, "cp", cp_unit)
                calc_cv = convert_from_SI(calc_cv, "cv", cv_unit)
                calc_v = convert_from_SI(calc_v, "volume", volume_unit)
                
                calc_state = state(calc_state)
                
                if calc_x == -100:
                    calc_x = 0
                
                data = [zustand_var.get(), von_var.get(), zu_var.get(), round(calc_temp, 3), round(calc_p, 3), round(calc_d, 3), round(calc_v, 3),round(calc_u, 3),
                        round(calc_h, 3), round(calc_s, 3), round(calc_vis, 3), calc_state, round(calc_x, 1), round(calc_cp, 3), round(calc_cv, 3)]
                
                tree2.insert("", "end", values=data)
               
            # except:
            #     tkinter.messagebox.showwarning("Warnung", "Berechnung fehlgeschlagen!")
            #     print("Berchnung fehlgeschlagen")
            except Exception as e:
                tkinter.messagebox.showwarning("Warnung", f"Berechnung fehlgeschlagen:\n{e}")
                print("Berechnung fehlgeschlagen:", e)
                    
        except ValueError:
            tkinter.messagebox.showwarning("Warnung", "Bitte gültige Zahlenwerte eingeben!")
    
    def get_input_code(variable_name):
        mapping = {
            "Temperatur T": "T",
            "Druck p": "P",
            "Dichte rho": "D",
            "Spezifische Enthalpie h": "H",
            "Spezifische Entropie s": "S",
            "Dampfqualität x": "Q",
            "Innere Energie u": "U",
            "Viskosität eta": "V",
            "Cp": "CPMASS",
            "Cv": "CVMASS",
            "Volume v": "D"
        }
        return mapping.get(variable_name, "")

    
    def state(calc_state):
        state_mapping = {
            0.0: "flüssig",
            3.0: "flüssig",
            2.0: "gasförmig",
            5.0: "gasförmig",
            1.0: "überkritisch",
            4.0: "krit. Punkt",
            6.0: "Nassdampfgebiet"
        }
        return state_mapping.get(calc_state, "unbekannt")

    def check_limits(variable1, variable2, const_value, inconst_value, maxtemp, mfloatemp, maxp, minp):
        # Temperaturprüfungen
        if variable1 == "Temperatur T":
            if inconst_value > maxtemp or inconst_value < mfloatemp:
                tkinter.messagebox.showwarning("Warnung", "Temperaturwert 1 liegt außerhalb der Fluidgrenzen!")
                return False
    
        if variable2 == "Temperatur T":
            if const_value > maxtemp or const_value < mfloatemp:
                tkinter.messagebox.showwarning("Warnung", "Temperaturwert 2 liegt außerhalb der Fluidgrenzen!")
                return False
    
        # Druckprüfungen
        if variable1 == "Druck p":
            if inconst_value > maxp or inconst_value < minp:
                tkinter.messagebox.showwarning("Warnung", "Druckwert 1 liegt außerhalb der Fluidgrenzen!")
                return False
    
        if variable2 == "Druck p":
            if const_value > maxp or const_value < minp:
                tkinter.messagebox.showwarning("Warnung", "Druckwert 2 liegt außerhalb der Fluidgrenzen!")
                return False
    
        return True

    def check_limitsw(variable1, variable2, start_value, const_value, end_value, maxtemp, mfloatemp, maxp, minp):
        # Temperaturprüfungen
        if variable1 == "Temperatur T":
            if end_value > maxtemp or start_value < mfloatemp:
                tkinter.messagebox.showwarning("Warnung", "Start- oder Endwert liegen außerhalb der Fluidgrenzen!")
                return False
    
        if variable2 == "Temperatur T":
            if const_value > maxtemp or const_value < mfloatemp:
                tkinter.messagebox.showwarning("Warnung", "Temperaturwert liegt außerhalb der Fluidgrenzen!")
                return False
    
        # Druckprüfungen
        if variable1 == "Druck p":
            if end_value > maxp or start_value < minp:
                tkinter.messagebox.showwarning("Warnung", "Start- oder Endwert liegen außerhalb der Fluidgrenzen!")
                return False
    
        if variable2 == "Druck p":
            if const_value > maxp or const_value < minp:
                tkinter.messagebox.showwarning("Warnung", "Druckwert 2 liegt außerhalb der Fluidgrenzen!")
                print (end_value, const_value, maxp, minp)
                return False
    
        return True


    # Use of Return Key
    def return_calc(event):
        calc()

    #diagram(selected_diagram.get())
    
    def rechnen():
            calc()
            create_figure(selected_fluid.get())
            show_diagram()
    

    def export_treeview_to_csv():
        rows = tree2.get_children()
        if not rows:
            tk.messagebox.showinfo("Info", "Keine Daten zum Exportieren.")
            return
    
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV-Dateien", "*.csv")],
            title="CSV-Datei speichern"
        )
        if not file_path:
            return  # Abgebrochen
    
        # CSV in einen StringIO-Puffer schreiben
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')  # Oder ',' für US-Format
    
        # Spaltenüberschriften schreiben
        headers = [tree2.heading(col)["text"] for col in tree2["columns"]]
        writer.writerow(headers)
    
        # Alle Datenzeilen schreiben
        for row_id in tree2.get_children():
            row_data = tree2.item(row_id)["values"]
            writer.writerow(row_data)
    
        # Inhalt in Datei speichern
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            file.write(output.getvalue())
    
        # In Zwischenablage kopieren
        window.clipboard_clear()
        window.clipboard_append(output.getvalue())
        window.update()  # Wichtig für Windows
    
        tk.messagebox.showinfo("Erfolg", f"CSV wurde erfolgreich gespeichert und kopiert:\n{file_path}")

    def delete_row():
        selected_item = tree2.selection()
        if selected_item:
            tree2.delete(selected_item)
        else:
            print("Keine Zeile ausgewählt")
    
    # Create Calc Button
    calc_btn = ttk.Button(main_frame, text="➕ Hinzufügen", command=rechnen, width=20)
    calc_btn.grid(row=9, column=2, sticky="Nw", columnspan=1, pady=10, padx=(380,0))
    main_frame.bind("<Return>", return_calc)

    csv_button = ttk.Button(main_frame, text="💾 CSV", command=export_treeview_to_csv, width=9)
    csv_button.grid(row=10, column=2, pady=10, sticky="w", padx=(380,0))  # Anpassen an dein Layout
    
    delete_button = ttk.Button(main_frame, text="🗑️Müll", command=delete_row, width=9, )
    delete_button.grid(row=10, column=2, pady=10, sticky="w", padx=(450,0))
    
    diagram_btn = ttk.Button(diagram_frame, text="↺ Aktualisieren", command=show_diagram, width=14)
    diagram_btn.grid(row=8, column=1, sticky="w", padx=(10,0))
    
        
        
    zustand_btn = ttk.Button(diagram_frame, text="➕ Isolinien", command=on_draw_selected_isoline_button_click, width=14)
    zustand_btn.grid(row=8, column=1, padx=(115,0), sticky="w")


    vier_label = tk.Label(main_frame, text="4. Bitte wählen Sie wo und welche ZÄ eingetragen werden soll", font=("Arial", 12, "bold"))
    vier_label.grid(row=8, column=2, columnspan=2, padx=20, pady=5, sticky="w")
    
    all_entry_fields = [minx_entry, miny_entry, maxx_entry, maxy_entry, eingabe1_entry, eingabe2_entry]
    checkbox_vars = [isobar_var, isotherm_var, isochor_var, isentropic_var, isenthalpic_var, isovapore_var, legende_var, legende_set]
    
    
    def reset_app():
        global selected_row_values, highlight_point
        #save_current_data(tree2, cache_kreisprozesse)
        
        load_history_from_file()     
        cache_kreisprozesse.clear()
        for item in tree2.get_children():
            row = tree2.item(item)["values"]
            append_to_history(history_kreisprozesse, row)
            append_to_cache(cache_kreisprozesse, row)    
        
    
        # ░1░ Diagramm + Toolbar löschen
        for widget in diagram_canvas_frame.winfo_children():
            widget.destroy()

        # ░2░ Eingabefelder leeren (alle tkinter.Entry Felder)
        for entry in all_entry_fields:  # Liste vorher definieren!
            entry.delete(0, tk.END)
            entry.insert(0, "0")
        
        default_units = {
            "Temperatur T": "Kelvin",
            "Druck p": "Pa",
            "Dichte rho": "kg/m³",
            "Volumen v": "m³/kg",
            "Innere Energie u": "J/kg",
            "Spezifische Enthalpie h": "J/kg",
            "Spezifische Entropie s": "J/kg*K",
            "Viskosität eta": "Pa*s",
            "Cp": "J/kg*K",
            "Cv": "J/kg*K"
        }
        for label, var in selected_vars.items():
            default = default_units.get(label)
            if default:
                var.set(default)
            
        # ░3░ Comboboxen auf Standard zurücksetzen
        fluid_combobox.set("Water")
        input1_combobox.set("Temperatur T")
        input2_combobox.set("Druck p")
        diagram_combobox.set("T-s-Diagramm")    # z. B.
        von_Combobox.set(1)
        zu_Combobox.set(1)
        zustand_Combobox.set("isobar")
        persisted_isolines.clear()
        
    
        # ░4░ Treeview leeren
        for item in tree2.get_children():
            tree2.delete(item)
    
        # ░5░ Checkboxen zurücksetzen
        for var in checkbox_vars:  # Liste von BooleanVar(), z. B.
            var.set(False)
        
        # ░8░ Fluid-Informationen zurücksetzen
        pure_info_label["text"] = "- Reines Fluid:"
        molarmass_info_label["text"] = "- Molare Masse: "
        gasconstant_info_label["text"] = "- Spez. Gaskonstante: "
        ctp_pressure_label["text"] = "- Druck: "
        ctp_temp_label["text"] = "- Temperatur: "
        ctp_den_label["text"] = "- Dichte: "
        tp_pressure_label["text"] = "- Druck: "
        tp_temp_label["text"] = "- Temperatur: "
        maxp_label["text"] = "- Max. Druck: "
        maxtemp_label["text"] = "- Max. Temperatur: "
        minp_label["text"] = "- Min. Druck: "
        mfloatemp_label["text"] = "- Min. Temperatur: "
        selected_row_values = None
        highlight_point = False
    
        # ░6░ Globale Plot-Objekte zurücksetzen
        show_diagram()
        print("Anwendung wurde vollständig zurückgesetzt.")
        
        
    def reset_app_delayed():
        # Neues kleines Fenster ohne Rand
        loading_window = tk.Toplevel(window)
        loading_window.title("Bitte warten...")
        loading_window.geometry("300x140")
        loading_window.resizable(False, False)
        loading_window.overrideredirect(True)  # Kein Rand, keine Titelleiste
        loading_window.configure(bg="white")  # Hintergrundfarbe

    
        # Fenster zentrieren
        x = window.winfo_x() + (window.winfo_width() // 2) - 125
        y = window.winfo_y() + (window.winfo_height() // 2) - 60
        loading_window.geometry(f"+{x}+{y}")
        
        # Info-Label
        label = tk.Label(loading_window, text="Zurücksetzen läuft...", font=("Arial", 12))
        label.pack(pady=(15, 5))
        label.configure(bg="white")  # Hintergrundfarbe

    
        # Lade-Animation (Text-Kreis)
        spinner_label = tk.Label(loading_window, font=("Consolas", 25))
        spinner_label.pack()
        spinner_label.configure(bg="white")  # Hintergrundfarbe

        # Animation: sich drehendes Zeichen
        spinner_frames = itertools.cycle(["◐", "◓", "◑", "◒"])
    
        def animate():
            spinner_label.config(text=next(spinner_frames))
            loading_window.after(100, animate)
    
        animate()  # Start Animation

        window.after(1000, lambda: [loading_window.destroy(), reset_app()])   

       
    reset_btn = ttk.Button(main_frame, text="🏠 Zurück zum Start", command=reset_app_delayed, width=25)
    reset_btn.grid(row=0, column=2, pady=10, padx=(340,0), sticky="w")
    
    def reload_kreisprozesse():
        load_history_from_file()
        update_cache_treeview(tree2, cache_kreisprozesse)
        
    
    
    cache_btn = ttk.Button(main_frame, text="Sitzung wiederherstellen", command=reload_kreisprozesse, width=25)
    cache_btn.grid(row=0, column=2, pady=10, padx=20, sticky="w")
    #update_cache_treeview(tree2, cache_kreisprozesse)

#Seite Kreislaeufe
#-----------------------------------------------------------------------------------------------------
#Seite Einstellungen
        

def show_einstellungen():
    global isolines, data, farben_iso, farben_data
    global style_comboboxes, kreis_canvas_list
    global isoline_frame, data_frame
    global left_var, right_var, top_var, bottom_var
    global kreis_canvas_data_list, anzahl_comboboxes
    
    for widget in main_frame.winfo_children():
        widget.destroy()
        
    kreis_canvas_data_list = []

    
    heading_label = tk.Label(main_frame, text="Einstellungen", font=("Arial", 20, "bold"), width=40)
    heading_label.grid(row=0, column=0, padx=20, pady=7, sticky="w", columnspan=2)
    heading_label.configure(background="peachpuff1")
    
    diagram_label=tk.Label(main_frame, text="3. Ändern des Diagrammes", font=("Arial", 12, "bold"))
    diagram_label.grid(row=1, column=3, pady=7, sticky="w", columnspan=2)
    
    
    iso_label= tk.Label(main_frame, text="1. Ändern der Isolinien", font=("Arial", 12, "bold"))
    iso_label.grid(row=1, column=0, padx=20, pady=7, sticky="w", columnspan=2)
    
    isoline_frame = ttk.LabelFrame(main_frame)
    isoline_frame.grid(row=2, column=0, columnspan=3, padx=20, pady=5, sticky="nw")
    
    data_label= tk.Label(main_frame, text="2. Ändern der Datenpunkte", font=("Arial", 12, "bold"))
    data_label.grid(row=3, column=0, padx=20, pady=7, sticky="w", columnspan=2)   

    data_frame = ttk.LabelFrame(main_frame)
    data_frame.grid(row=4, column=0, columnspan=1, padx=20, pady=5, sticky="nw")
    

    hinweis_frame = tk.LabelFrame(main_frame, text="Achtung!", fg="red", font=("Arial", 12, "bold"), labelanchor="n", bd=2, relief="solid", highlightcolor="red", highlightthickness=2)
    hinweis_frame.grid(row=4, column=3, sticky="ews", columnspan=2)
    
    hinweis_label = tk.Label(hinweis_frame, font=("Arial", 11),
                             text="Damit die Einstellungen der Isolinien und Datenpunkten \nübernommen werden, muss FluProp 3 neu gestartet werden!")                         
    hinweis_label.grid(row=0, column=0, padx=61, pady=5)

    
    iso_label= tk.Label(main_frame, text="1. Ändern der Isolinien", font=("Arial", 12, "bold"))
    iso_label.grid(row=1, column=0, padx=20, pady=7, sticky="w", columnspan=2)
    
    
    
    ttk.Label(isoline_frame, text="Isolinie", font=("Arial", 12)).grid(row=0, column=0, padx=25, sticky="w")
    ttk.Label(isoline_frame, text="Farbe", font=("Arial", 12)).grid(row=0, column=1, padx=10, sticky="w")
    ttk.Label(isoline_frame, text="Linienstil", font=("Arial", 12)).grid(row=0, column=2, padx=5, sticky="w")
    ttk.Label(isoline_frame, text="Dicke", font=("Arial", 12)).grid(row=0, column=3, padx=5, sticky="w")
    ttk.Label(isoline_frame, text="Anzahl", font=("Arial", 12)).grid(row=0, column=4, padx=5, sticky="w")
    ttk.Label(isoline_frame, text="___________________________________________________________", font=("Arial", 12)).grid(row=1, column=0, padx=5, sticky="w", columnspan=5)
    
    ttk.Label(data_frame, text="Daten", font=("Arial", 12)).grid(row=0, column=0, padx=25, sticky="w")
    ttk.Label(data_frame, text="Farbe", font=("Arial", 12)).grid(row=0, column=1, padx=5, sticky="w")
    ttk.Label(data_frame, text="Punktstil", font=("Arial", 12)).grid(row=0, column=2, padx=5, sticky="w")
    ttk.Label(data_frame, text="Größe", font=("Arial", 12)).grid(row=0, column=3, padx=5, sticky="w")
    ttk.Label(data_frame, text="_______________________________________________", font=("Arial", 12)).grid(row=1, column=0, padx=5, sticky="w", columnspan=4)
    
    
    isolines = ["Isobare", "Isotherme", "Isochore", "Isentrope", "Isenthalpe", "Isovapore", "Siedelinie", "Taulinie"][:len(isolines)]
    data =["Daten", "ausgewählte Daten", "Kritischer Punkt", "Tripelpunkt"]
    farben_iso = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff", "#aa00ff", "#00ffaa"]
    farben_data = ["#ff0000", "#00ff00", "#0000ff", "#ffff00"][:len(data)]
    linienstile = ["-", "--", "-."]
    dotstyle = ["o", "O", "-", "*","x", "+", "-", ".", "^"]

    style_comboboxes = []
    kreis_canvas_list = []
    anzahl_comboboxes = []



    def farbe_auswaehlen_iso(index):
        farbe = colorchooser.askcolor(title=f"Farbe für {isolines[index]} wählen")[1]
        if farbe:
            farben_iso[index] = farbe
            canvas = kreis_canvas_list[index]
            canvas.itemconfig("kreis", fill=farbe)

    def farbe_auswaehlen_data(index):
        farbe = colorchooser.askcolor(title=f"Farbe für {data[index]} wählen")[1]
        if farbe:
            farben_data[index] = farbe
            canvas = kreis_canvas_data_list[index]
            canvas.itemconfig("kreis", fill=farbe)
    




       
    # Isolinien-Einträge (ab Zeile 1)
    for i, isoline_name in enumerate(isolines):
        row = i + 4

        ttk.Label(isoline_frame, text=isoline_name,font=("Arial", 11)).grid(row=row, column=0, padx=25, pady=3, sticky="w")

        # Canvas für echten Kreis
        canvas = tk.Canvas(isoline_frame, width=30, height=30, highlightthickness=0)
        kreis = canvas.create_oval(5, 5, 15, 15, fill=farben_iso[i], tags="kreis")
        canvas.grid(row=row, column=1, padx=5, pady=5)
        kreis_canvas_list.append(canvas)

        # Klick auf Kreis → Farbwähler
        def bind_callback(index=i):
            return lambda event: farbe_auswaehlen_iso(index)
        canvas.bind("<Button-1>", bind_callback())

        # Combobox für Linienstil
        cb = ttk.Combobox(isoline_frame, values=linienstile, width=6)
        cb.set(linienstile[0])
        cb.grid(row=row, column=2, padx=5, pady=3)
        style_comboboxes.append(cb)
        
        dicke_value =(0.4,0.6,0.8,1,1.2,1.4,1.6,1.8,2,2.2,2.4,2.6,2.8,3)
        spin_box = ttk.Combobox(isoline_frame,values=dicke_value,  width=6,  state="readonly")
        spin_box.grid(row=row, column=3, padx=5, pady=3)
        spin_box.set(1)
        dicke_comboboxes.append(spin_box)
        #print(spin_box)

        anzahl_value =(4,6,8,10,12,14,16,18,20)
        combobox = ttk.Combobox(isoline_frame, values=anzahl_value,  width=6,  state="readonly")  # Werte entsprechend anpassen
        combobox.grid(row=row, column=4, padx=5, pady=3)
        combobox.set(6)
        anzahl_comboboxes.append(combobox)  # Füge die Combobox der Liste hinzu  
        #print(combobox)

    for i, data_name in enumerate(data):
        row = i + 4

        ttk.Label(data_frame, text=data_name,font=("Arial", 11)).grid(row=row, column=0, padx=25, pady=3, sticky="w")


        
        canvas = tk.Canvas(data_frame, width=30, height=30, highlightthickness=0)
        kreis = canvas.create_oval(5, 5, 15, 15, fill=farben_data[i], tags="kreis")
        canvas.grid(row=row, column=1, padx=5, pady=5)
        kreis_canvas_data_list.append(canvas)  # ← NEUE Liste!
        
        # Klick auf Kreis → Farbwähler (Korrekt!)
        def bind_callback(index=i):
            return lambda event: farbe_auswaehlen_data(index)
        canvas.bind("<Button-1>", bind_callback())

        
        
        # Combobox für Linienstil
        cb = ttk.Combobox(data_frame, values=dotstyle, width=6)
        cb.set(dotstyle[0])
        cb.grid(row=row, column=2, padx=5, pady=3)
        style_comboboxes.append(cb)
        
        size_value = (1,2,3,4,5,6,7,8,9,10)
        spin_box = ttk.Combobox(data_frame,values=size_value,  width=6,  state="readonly")
        spin_box.grid(row=row, column=3, padx=5, pady=3)
        spin_box.set(5)
    
    
    # Diagramm-Frame (breiter & höher)
    diagram_frame = ttk.LabelFrame(main_frame)
    diagram_frame.grid(row=2, column=3, rowspan=10, columnspan=4, pady=10, sticky="nw")

    # Spalten konfigurieren
    diagram_frame.columnconfigure(0, weight=1)  # Canvas
    diagram_frame.columnconfigure(1, weight=0)  # Label
    diagram_frame.columnconfigure(2, weight=0)  # Skala
    diagram_frame.columnconfigure(3, weight=0)  # Prozent

    # Diagramm-Canvas
    diagram_canvas_frame = ttk.Frame(diagram_frame, width=400, height=400)
    diagram_canvas_frame.grid(row=0, column=0, rowspan=10, padx=10, pady=10, sticky="nsew")

    # Fehlerlabel
    error_label = ttk.Label(diagram_frame, text="", foreground="red")
    error_label.grid(row=0, column=1, columnspan=3, pady=(5, 0), sticky="w")

    # Überschrift zu den Reglern
    ttk.Label(diagram_frame, text="Diagramm - Rand in %", font=("Arial", 10, "bold")).grid(
        row=1, column=1, columnspan=3, pady=(10, 5), sticky="w")

    def generate_random_points(num_points=100):
        return [(random.uniform(0, 1) * 10000, random.uniform(0, 1) * 1000) for _ in range(num_points)]

    def generate_heart_points(num_points=1000):
        t = np.linspace(0, 2 * np.pi, num_points)
        x = 16 * np.sin(t) ** 3 * 10000
        y = (13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)) * 1000
        return list(zip(x, y))

    def create_plot():
        global canvas, points

        fig = plt.Figure(figsize=(4.5, 4.5), dpi=65)
        ax = fig.add_subplot(111)

        if left_var.get() == 40 and right_var.get() == 60 and top_var.get() == 60 and bottom_var.get() == 40:
            points = generate_heart_points()
        else:
            points = generate_random_points()

        x_vals, y_vals = zip(*points)
        ax.scatter(x_vals, y_vals, label="Datenpunkte", c='blue', s=10)
        ax.set_title("T-s Diagramm")
        ax.set_xlabel("Entropie [J/kg*K]")
        ax.set_ylabel("Temperatur [Kelin]")
        ax.tick_params(axis='x', labelrotation=45)
        ax.tick_params(axis='y', labelrotation=45)

        try:
            fig.subplots_adjust(
                left=left_var.get() / 100,
                right=right_var.get() / 100,
                top=top_var.get() / 100,
                bottom=bottom_var.get() / 100
            )

            error_label.config(text="")

            if canvas:
                canvas.get_tk_widget().destroy()

            canvas = FigureCanvasTkAgg(fig, master=diagram_canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)

        except ValueError as e:
            print(f"[Fehler beim Zeichnen des Diagramms] {e}")
            error_label.config(text="⚠️ Ungültige Einstellung")

    # Regler mit Labels & Prozentwerten
    subplot_controls = {
        "Links": left_var,
        "Rechts": right_var,
        "Oben": top_var,
        "Unten": bottom_var
    }

    for i, (label, var) in enumerate(subplot_controls.items(), start=2):
        ttk.Label(diagram_frame, text=label).grid(row=i, column=1, sticky="e", padx=5, pady=2)

        value_label_var = tk.StringVar(value=f"{var.get()} %")
        ttk.Label(diagram_frame, textvariable=value_label_var).grid(row=i, column=3, sticky="w", padx=5)

        def on_scale_change(val, v=var, lv=value_label_var):
            lv.set(f"{int(float(val))} %")
            create_plot()

        scale = ttk.Scale(diagram_frame, from_=0, to=100, variable=var,
                          orient="horizontal", length=117, command=on_scale_change)
        scale.grid(row=i, column=2, padx=5)
    
    load_subplot_settings()
    #create_plot()
    #create_plot()
    

    def reset_defaults():
        # Setze alle Subplot-Einstellungen auf die Standardwerte zurück
        left_var.set(default_settings["left"])
        right_var.set(default_settings["right"])
        top_var.set(default_settings["top"])
        bottom_var.set(default_settings["bottom"])
        # Bestätigungslabel anzeigen
        reset_label = ttk.Label(main_frame, text="✔ Diagramme wurden zurückgesetzt")
        reset_label.configure(foreground="green")
        reset_label.grid(row=0, column=4, padx=(10,0), columnspan=3)
    
        # Nach 3 Sekunden Label wieder entfernen
        reset_label.after(3000, reset_label.destroy)

        # Erstelle das Diagramm erneut mit den Standardwerten
        create_plot()


    Zurücksetzen_btn=ttk.Button(diagram_frame, text="Zurücksetzen der Diagramme", command=reset_defaults, width=31)
    Zurücksetzen_btn.grid(row=6, column=1, padx=(10,0), pady=10, sticky="w", columnspan=3)
    
    save_btn=ttk.Button(main_frame, text="💾 Einstellungen speichern", command=save_subplot_settings)
    save_btn.grid(row=2, column=2, pady=(350,0), sticky="w", columnspan=2)
        
    # Lade gespeicherte Subplot-Einstellungen beim Start
    #load_subplot_settings()

    # Zeige das erste Diagramm mit den aktuellen Einstellungen
    create_plot()


#Seite Einstellungen
#-----------------------------------------------------------------------------------------------------
#Verlauf

# 
def show_verlauf():
    """Zeigt den Verlauf an und lädt die Historie."""
    for widget in main_frame.winfo_children():
        widget.destroy()

    # History-Daten laden
    load_history_from_file()
    
    heading_label = tk.Label(main_frame, text="Verlauf", font=("Arial", 20, "bold"), width=40)
    heading_label.grid(row=0, column=0, padx=20, pady=7, sticky="w", columnspan=3)
    heading_label.configure(background="khaki")

    label1 = tk.Label(main_frame, text="1. Verlauf der Seite Reinstoffe", font=("Arial", 12, "bold"))
    label1.grid(row=1, column=0, padx=20, pady=5, sticky="w")
    label2 = tk.Label(main_frame, text="2. Verlauf der Seite Kreisprozesse", font=("Arial", 12, "bold"))
    label2.grid(row=3, column=0, padx=20, pady=5, sticky="w")

    # Reinstoffe Tabelle
    tree_frame1 = tk.Frame(main_frame, width=1215, height=300)
    tree_frame1.grid(row=2, column=0, columnspan=1, sticky="nsew", padx=(40, 0), pady=10)
    tree_frame1.grid_propagate(False)

    tree_scroll_y = ttk.Scrollbar(tree_frame1, orient="vertical")
    tree_scroll_x = ttk.Scrollbar(tree_frame1, orient="horizontal")

    spaltennamen = ["🕒", "Temperatur", "Druck", "Dichte", "Volumen",
                    "Innere Energie", "spez. Enthalpie", "spez. Entropie",
                    "Viskosität", "Aggregatszustand", "Dampfqualität", "Cp", "Cv", "Einheiten"]
    treev = ttk.Treeview(tree_frame1, columns=spaltennamen, show="headings", yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

    treev.column("#0", width=120, anchor="center")  # Sichtbar machen, damit der Timestamp angezeigt wird
    treev.bind('<Motion>', 'break')  # Damit Spaltenbreite unveränderbar ist für User

    # Konfiguration der anderen Spalten
    for spalte in spaltennamen:
        treev.heading(spalte, text=spalte)
        treev.column(spalte, width=122, anchor="center")
    treev.column("Einheiten", width=400, anchor="center")
    
    tree_scroll_y.config(command=treev.yview)
    tree_scroll_x.config(command=treev.xview)

    treev.grid(row=0, column=0, sticky="nsew")
    tree_scroll_y.grid(row=0, column=1, sticky="ns")
    tree_scroll_x.grid(row=1, column=0, sticky="ew")

    tree_frame1.grid_rowconfigure(0, weight=1)
    tree_frame1.grid_columnconfigure(0, weight=1)

    #treev.bind("<<TreeviewSelect>>", lambda event, tree=treev: on_row_select(event, treev))

    # Kreisprozesse Tabelle
    tree_frame2 = tk.Frame(main_frame, width=1000, height=300)
    tree_frame2.grid(row=4, column=0, columnspan=1, sticky="nsew", padx=(40, 0), pady=10)
    tree_frame2.grid_propagate(False)

    tree_scroll_y2 = ttk.Scrollbar(tree_frame2, orient="vertical")
    tree_scroll_x2 = ttk.Scrollbar(tree_frame2, orient="horizontal")

    spaltennamen2 = ["🕒", "Zustandsänderung", "von", "zu", "Temperatur", "Druck", "Dichte",
                     "Volumen", "Innere Energie", "spez. Enthalpie", "spez. Entropie",
                     "Viskosität", "Aggregatszustand", "Dampfqualität", "Cp", "Cv", "Einheiten"]
    tree2v = ttk.Treeview(tree_frame2, columns=spaltennamen2, show="headings", yscrollcommand=tree_scroll_y2.set, xscrollcommand=tree_scroll_x2.set)

    tree2v.column("#0", width=120, anchor="center")  # Sichtbar machen, damit der Timestamp angezeigt wird
    tree2v.bind('<Motion>', 'break')

    # Konfiguration der anderen Spalten
    for spalte in spaltennamen2:
        tree2v.heading(spalte, text=spalte)
        tree2v.column(spalte, width=122, anchor="center")
    tree2v.column("von", width=50, anchor="center")
    tree2v.column("zu", width=50, anchor="center")
    tree2v.column("Einheiten", width=400, anchor="center")

    tree_scroll_y2.config(command=tree2v.yview)
    tree_scroll_x2.config(command=tree2v.xview)

    tree2v.grid(row=0, column=0, sticky="nsew")
    tree_scroll_y2.grid(row=0, column=1, sticky="ns")
    tree_scroll_x2.grid(row=1, column=0, sticky="ew")

    tree_frame2.grid_rowconfigure(0, weight=1)
    tree_frame2.grid_columnconfigure(0, weight=1)

    # History-Daten in die Tabellen laden
    update_history_treeview(treev, history_reinstoffe)
    update_history_treeview(tree2v, history_kreisprozesse)
    
    
#
#Seite Verlauf
#-----------------------------------------------------------------------------------------------------
# Startseite


def show_startseite():#gray94
    label1 =tk.Label(main_frame, text="______________", font=("Arial", 32, "bold"), fg="gray94")
    label1.grid(row=0, column=0, padx=(7,0))
    label2 =tk.Label(main_frame, text="________________________", font=("Arial", 32, "bold"), fg="gray94")
    label2.grid(row=0, column=1)
    label3 =tk.Label(main_frame, text="______________", font=("Arial", 32, "bold"), fg="gray94")
    label3.grid(row=0, column=2)

    title_label_fluprop = tk.Label(main_frame, text="FluProp", font=("Segoe UI Black", 40, "bold"), fg="black")
    title_label_fluprop.grid(row=1, column=1, sticky="w", padx=(170, 0), pady=(150, 0))
    title_label_3 = tk.Label(main_frame, text="3", font=("Segoe UI Black", 40, "bold"), fg="green3")
    title_label_3.grid(row=1, column=1, sticky="w", padx=(384, 0), pady=(150, 0))
    

    # Willkommenstext
    welcome_label = tk.Label(main_frame, text="Willkommen bei FluProp!" , font=("Arial", 14))
    welcome_label.grid(row=2, column=1, pady=(10, 0))
    welcome_label1 = tk.Label(main_frame, text="Das Programm zur Berechnung von thermodynamischen Stoffdaten.", font=("Arial", 14))
    welcome_label1.grid(row=3, column=1, pady=(0, 20))

    
    button1= tk.Button(main_frame, text="Reinstoffe", font=("Arial", 12), width=25, command=show_reinstoffe)
    button1.grid(row=4, column=1, pady=5)
    button2= tk.Button(main_frame, text="Stoffgemische", font=("Arial", 12), width=25, command=show_stoffgemische, foreground="gray78")
    button2.grid(row=5, column=1, pady=5)
    button3= tk.Button(main_frame, text="Kreisprozesse", font=("Arial", 12), width=25, command=show_kreisprozesse)
    button3.grid(row=6, column=1, pady=5)
    button4= tk.Button(main_frame, text="Verlauf", font=("Arial", 12), width=25, command=show_verlauf)
    button4.grid(row=7, column=1, pady=5)
    button5= tk.Button(main_frame, text="Einstellungen", font=("Arial", 12), width=25, command=show_einstellungen)
    button5.grid(row=8, column=1, pady=5)

# Startseite
#-----------------------------------------------------------------------------------------------------
# Ende


# Standardansicht setzen 

show_startseite()


def on_closing():
    if tkinter.messagebox.askyesno("FluProp 3 schließen", "Möchtest du FluProp 3 beenden?"):
        load_history_from_file()
        if tree is not None:
            cache_reinstoffe.clear()
        if tree2 is not None:
            cache_kreisprozesse.clear()

        # Reinstoffe sichern, nur wenn tree existiert
        if tree is not None:
            try:
                for item in tree.get_children():
                    row = tree.item(item)["values"]
                    append_to_history(history_reinstoffe, row)
                    append_to_cache(cache_reinstoffe, row)
            except Exception as e:
                print("Fehler beim Zugriff auf tree (Reinstoffe):", e)

        # Kreisprozesse sichern, nur wenn tree2 existiert
        if tree2 is not None:
            try:
                for item in tree2.get_children():
                    row = tree2.item(item)["values"]
                    append_to_history(history_kreisprozesse, row)
                    append_to_cache(cache_kreisprozesse, row)
            except Exception as e:
                print("Fehler beim Zugriff auf tree2 (Kreisprozesse):", e)

        save_history_to_file()
        window.destroy()
        plt.close("all")
window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()
