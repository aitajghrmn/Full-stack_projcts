

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  


# ──────────────────────────────────────────────
#  Məlumat strukturu (dict + list)
# ──────────────────────────────────────────────
students = {}      # { id: { "id": int, "name": str, "grades": list } }
_next_id = 1       # avtomatik ID sayğacı


def _new_id():
    global _next_id
    nid = _next_id
    _next_id += 1
    return nid


# ──────────────────────────────────────────────
#  Köməkçi funksiyalar
# ──────────────────────────────────────────────
def calc_average(grades):
    return round(sum(grades) / len(grades), 2) if grades else None


def student_dict(s):
    return {
        "id":      s["id"],
        "name":    s["name"],
        "grades":  s["grades"],
        "average": calc_average(s["grades"])
    }


# ──────────────────────────────────────────────
#  ENDPOINT-lər
# ──────────────────────────────────────────────

# GET /students — bütün tələbələr
@app.route("/students", methods=["GET"])
def get_students():
    return jsonify([student_dict(s) for s in students.values()])


# POST /students — yeni tələbə əlavə et
@app.route("/students", methods=["POST"])
def add_student():
    data = request.get_json()
    name = (data or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "Ad boş ola bilməz!"}), 400
    sid = _new_id()
    students[sid] = {"id": sid, "name": name, "grades": []}
    return jsonify(student_dict(students[sid])), 201


# DELETE /students/<id> — tələbəni sil
@app.route("/students/<int:sid>", methods=["DELETE"])
def remove_student(sid):
    if sid not in students:
        return jsonify({"error": "Tələbə tapılmadı!"}), 404
    removed = students.pop(sid)
    return jsonify({"message": f"{removed['name']} silindi."})


# POST /students/<id>/grades — qiymət əlavə et
@app.route("/students/<int:sid>/grades", methods=["POST"])
def add_grade(sid):
    if sid not in students:
        return jsonify({"error": "Tələbə tapılmadı!"}), 404
    data = request.get_json()
    try:
        grade = float((data or {}).get("grade", ""))
    except (ValueError, TypeError):
        return jsonify({"error": "Qiymət rəqəm olmalıdır!"}), 400
    if not (0 <= grade <= 100):
        return jsonify({"error": "Qiymət 0–100 arasında olmalıdır!"}), 400
    students[sid]["grades"].append(grade)
    return jsonify(student_dict(students[sid]))


# GET /students/top — ən yüksək orta qiymətli tələbə
@app.route("/students/top", methods=["GET"])
def top_student():
    ranked = [s for s in students.values() if s["grades"]]
    if not ranked:
        return jsonify({"error": "Heç bir tələbənin qiyməti yoxdur!"}), 404
    best = max(ranked, key=lambda s: calc_average(s["grades"]))
    return jsonify(student_dict(best))


# ──────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
