from flask import jsonify

from services import report_service


def summary_report():
    return jsonify(report_service.build_summary()), 200


def user_report(user_id):
    return jsonify(report_service.build_user_report(user_id)), 200
