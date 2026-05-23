from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB = 'holberton.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row  # dict kimi oxumaq ucun
    return conn


# ── 1. Leaderboard ──────────────────────────────────────────
@app.route('/api/leaderboard')
def leaderboard():
    
    conn = get_db()
    rows = conn.execute('''
        SELECT
            s.id,
            s.first_name,
            s.last_name,
            s.cohort,
            ROUND(AVG(r.score), 1)        AS avg_score,
            COUNT(DISTINCT r.id)          AS review_count,
            COUNT(DISTINCT sub.id)        AS submission_count
        FROM students s
        LEFT JOIN reviews r   ON r.reviewee_id = s.id
        LEFT JOIN submissions sub ON sub.student_id = s.id
        GROUP BY s.id
        ORDER BY avg_score DESC
    ''').fetchall()
    conn.close()

    result = []
    for i, row in enumerate(rows):
        result.append({
            'rank':             i + 1,
            'id':               row['id'],
            'first_name':       row['first_name'],
            'last_name':        row['last_name'],
            'cohort':           row['cohort'],
            'avg_score':        row['avg_score'] or 0,
            'review_count':     row['review_count'],
            'submission_count': row['submission_count'],
        })
    return jsonify(result)


# ── 2. Tək tələbənin profili ────────────────────────────────
@app.route('/api/student/<int:student_id>')
def student_profile(student_id):
    
    conn = get_db()

    student = conn.execute(
        'SELECT * FROM students WHERE id = ?', (student_id,)
    ).fetchone()

    if not student:
        return jsonify({'error': 'Tapılmadı'}), 404

    # Proyekt üzrə ortalama qiymətlər
    project_scores = conn.execute('''
        SELECT
            p.name            AS project_name,
            ROUND(AVG(r.score), 1) AS avg_score,
            COUNT(r.id)       AS review_count
        FROM reviews r
        JOIN projects p ON p.id = r.project_id
        WHERE r.reviewee_id = ?
        GROUP BY p.id
        ORDER BY p.id
    ''', (student_id,)).fetchall()

    # Verdiyi review-lar
    given_reviews = conn.execute('''
        SELECT
            s.first_name || ' ' || s.last_name AS to_student,
            p.name  AS project_name,
            r.score,
            r.comment
        FROM reviews r
        JOIN students s ON s.id = r.reviewee_id
        JOIN projects p ON p.id = r.project_id
        WHERE r.reviewer_id = ?
        ORDER BY r.reviewed_at DESC
        LIMIT 10
    ''', (student_id,)).fetchall()

    conn.close()

    return jsonify({
        'student': dict(student),
        'project_scores': [dict(r) for r in project_scores],
        'given_reviews':  [dict(r) for r in given_reviews],
    })


# ── 3. Bütün proyektlər ─────────────────────────────────────
@app.route('/api/projects')
def projects():
    conn = get_db()
    rows = conn.execute('''
        SELECT
            p.id,
            p.name,
            p.description,
            ROUND(AVG(r.score), 1) AS avg_score,
            COUNT(DISTINCT sub.student_id) AS submitters
        FROM projects p
        LEFT JOIN reviews r ON r.project_id = p.id
        LEFT JOIN submissions sub ON sub.project_id = p.id
        GROUP BY p.id
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ── 4. Statistika ───────────────────────────────────────────
@app.route('/api/stats')
def stats():
    conn = get_db()
    total_students  = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    total_reviews   = conn.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]
    total_projects  = conn.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
    overall_avg     = conn.execute('SELECT ROUND(AVG(score),1) FROM reviews').fetchone()[0]
    conn.close()
    return jsonify({
        'total_students': total_students,
        'total_reviews':  total_reviews,
        'total_projects': total_projects,
        'overall_avg':    overall_avg,
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
