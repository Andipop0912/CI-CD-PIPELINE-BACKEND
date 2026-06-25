from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Attr
import logging

# -----------------------------------------
# APP + LOGGING
# -----------------------------------------
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

AWS_REGION = "us-east-1"
S3_BUCKET = "ci-cd-workshop-frontend-rahul"

s3 = boto3.client("s3", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

ASSIGNMENTS = dynamodb.Table("ci-cd-workshop-assignments")
SUBMISSIONS = dynamodb.Table("ci-cd-workshop-submissions")

log.info("Backend initialized")

# -----------------------------------------
@app.route("/")
def health():
    return {"status": "ok"}

# -----------------------------------------
@app.route("/create_assignment", methods=["POST"])
def create_assignment():
    data = request.json
    id = str(uuid.uuid4())

    ASSIGNMENTS.put_item(Item={
        "assignment_id": id,
        "title": data["title"],
        "teacher_name": data["teacher_name"],
        "subject": data["subject"],
        "description": data.get("description", ""),
        "due_date": data["due_date"],
        "created_at": datetime.utcnow().isoformat()
    })

    return {"message": "Assignment created", "id": id}

# -----------------------------------------
@app.route("/get_assignments")
def get_assignments():
    return {"assignments": ASSIGNMENTS.scan().get("Items", [])}

# -----------------------------------------
@app.route("/delete_assignment/<id>", methods=["DELETE"])
def delete_assignment(id):
    # Find submissions to delete files
    subs = SUBMISSIONS.scan(
        FilterExpression=Attr("assignment_id").eq(id)
    ).get("Items", [])

    # Delete all submissions + files
    for sub in subs:
        try:
            s3.delete_object(Bucket=S3_BUCKET, Key=sub["file_name"])
        except:
            pass

        SUBMISSIONS.delete_item(Key={"submission_id": sub["submission_id"]})

    # Delete assignment
    ASSIGNMENTS.delete_item(Key={"assignment_id": id})

    return {"message": "Assignment & related submissions deleted"}

# -----------------------------------------
@app.route("/submit_assignment", methods=["POST"])
def submit_assignment():
    assignment_id = request.form["assignment_id"]
    student_name = request.form["student_name"]
    comments = request.form.get("comments", "")
    file = request.files["file"]

    key = f"{assignment_id}/{uuid.uuid4()}_{file.filename}"
    s3.upload_fileobj(file, S3_BUCKET, key)

    submission_id = str(uuid.uuid4())

    SUBMISSIONS.put_item(Item={
        "submission_id": submission_id,
        "assignment_id": assignment_id,
        "student_name": student_name,
        "comments": comments,
        "file_name": key,
        "submitted_at": datetime.utcnow().isoformat()
    })

    return {"message": "Submission uploaded"}

# -----------------------------------------
@app.route("/get_submissions/<id>")
def get_submissions(id):
    subs = SUBMISSIONS.scan(
        FilterExpression=Attr("assignment_id").eq(id)
    ).get("Items", [])
    return {"submissions": subs}

# -----------------------------------------
@app.route("/delete_submission/<id>", methods=["DELETE"])
def delete_submission(id):
    # Find record
    sub = SUBMISSIONS.scan(
        FilterExpression=Attr("submission_id").eq(id)
    ).get("Items", [])

    if not sub:
        return {"error": "Not found"}, 404

    sub = sub[0]
    key = sub["file_name"]

    try:
        s3.delete_object(Bucket=S3_BUCKET, Key=key)
    except:
        pass

    SUBMISSIONS.delete_item(Key={"submission_id": id})

    return {"message": "Submission deleted"}

@app.route("/backend_version", methods=["GET"])
def backend_version():
    try:
        with open("backend_version.txt") as f:
            version = f.read().strip()
    except FileNotFoundError:
        version = "unknown"
    return jsonify({"backend_version": version})


# -----------------------------------------
app.run(host="0.0.0.0", port=5000, debug=True)
