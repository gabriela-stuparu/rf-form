from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import csv
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

CSV_FILE = "masuratori.csv"

@app.route('/')
def index():
    """Serve the main HTML file"""
    return send_from_directory('.', 'rf_form.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

def ensure_csv_header():
    """Ensure CSV file exists and has header"""
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        with open(CSV_FILE, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "lat", "lon", "azimut"])

@app.route('/adauga', methods=['POST'])
def adauga():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"mesaj": "Nu s-au primit date"}), 400
        
        lat = data.get("lat")
        lon = data.get("lon")
        azim = data.get("azim", "")  # azim is optional
        
        # Validate required fields
        if not lat or not lon:
            return jsonify({"mesaj": "Latitudinea și longitudinea sunt obligatorii"}), 400
        
        # Validate lat/lon are numbers
        try:
            float(lat)
            float(lon)
            if azim and azim.strip():  # Only validate azim if it's provided
                float(azim)
        except ValueError:
            return jsonify({"mesaj": "Coordonatele trebuie să fie numere valide"}), 400
        
        # Ensure CSV file has header
        ensure_csv_header()
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save to CSV file
        with open(CSV_FILE, "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, lat, lon, azim if azim else ""])
        
        print(f"[✅] Coordonate primite: {lat}, {lon}, {azim}")
        return jsonify({"mesaj": "Date salvate cu succes"}), 200
        
    except Exception as e:
        print(f"[❌] Eroare: {str(e)}")
        return jsonify({"mesaj": "Eroare la salvarea datelor"}), 500

@app.route('/coordonate', methods=['GET'])
def get_coordonate():
    """Retrieve all saved coordinates"""
    try:
        if not os.path.exists(CSV_FILE):
            return jsonify({"coordonate": [], "mesaj": "Nu există coordonate salvate"}), 200
        
        coordonate = []
        with open(CSV_FILE, "r", newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                coordonate.append({
                    "timestamp": row.get("timestamp", ""),
                    "lat": row.get("lat", ""),
                    "lon": row.get("lon", ""),
                    "azimut": row.get("azimut", "")
                })
        
        return jsonify({
            "coordonate": coordonate,
            "total": len(coordonate),
            "mesaj": f"Au fost găsite {len(coordonate)} coordonate"
        }), 200
        
    except Exception as e:
        print(f"[❌] Eroare la citirea coordonatelor: {str(e)}")
        return jsonify({"mesaj": "Eroare la citirea coordonatelor"}), 500

@app.route('/sterge', methods=['DELETE'])
def sterge_coordonate():
    """Delete all coordinates"""
    try:
        if os.path.exists(CSV_FILE):
            # Clean the file but keep the header
            with open(CSV_FILE, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "lat", "lon", "azimut"])
        return jsonify({"mesaj": "Toate coordonatele au fost șterse"}), 200
    except Exception as e:
        print(f"[❌] Eroare la ștergerea coordonatelor: {str(e)}")
        return jsonify({"mesaj": "Eroare la ștergerea coordonatelor"}), 500

@app.route('/sterge/<int:index>', methods=['DELETE'])
def sterge_coordonata_index(index):
    """Delete a specific coordinate by index"""
    try:
        if not os.path.exists(CSV_FILE):
            return jsonify({"mesaj": "Nu există coordonate de șters"}), 404
        
        # Read all coordinates
        coordonate = []
        with open(CSV_FILE, "r", newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                coordonate.append(row)
        
        # Check if index is valid
        if index < 0 or index >= len(coordonate):
            return jsonify({"mesaj": "Index invalid"}), 400
        
        # Remove the coordinate at the specified index
        coordonate.pop(index)
        
        # Rewrite the CSV file
        with open(CSV_FILE, "w", newline='') as f:
            if coordonate:
                fieldnames = ["timestamp", "lat", "lon", "azimut"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(coordonate)
            else:
                # If no coordinates left, just write header
                writer = csv.writer(f)
                writer.writerow(["timestamp", "lat", "lon", "azimut"])
        
        return jsonify({"mesaj": f"Coordonata #{index + 1} a fost ștearsă cu succes"}), 200
        
    except Exception as e:
        print(f"[❌] Eroare la ștergerea coordonatei: {str(e)}")
        return jsonify({"mesaj": "Eroare la ștergerea coordonatei"}), 500

if __name__ == '__main__':
    # Ensure CSV file exists with header on startup
    ensure_csv_header()
    print("Server pornit pe http://0.0.0.0:5173")
    print("Acces web la: http://localhost:5173 sau http://192.168.1.129:5173")
    print("Endpoints disponibile:")
    print("   GET / - Pagina principala (rf_form.html)")
    print("   GET /admin.html - Interfata de administrare")
    print("   POST /adauga - Adauga coordonate")
    print("   GET /coordonate - Preia toate coordonatele")
    print("   DELETE /sterge - Sterge toate coordonatele")
    print("   DELETE /sterge/<index> - Sterge coordonata la indexul specificat")
    port = int(os.environ.get('PORT', 5173))
    app.run(host='0.0.0.0', port=port, debug=False)
