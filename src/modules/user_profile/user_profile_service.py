# src/modules/user_profile/user_profile_service.py
"""Extra personal information (age, sex, address, job, country). A user has NO profile after
registering: the row is created the first time the user saves the "update information" form."""
from src.common.db import db_transaction
from src.common.validators import parse_sex, require_text, validate_date_of_birth
from src.modules.audit_logs.audit_actions import AuditAction


class UserProfileService:
    def __init__(self, profile_repository, audit_service):
        self.repo = profile_repository
        self.audit = audit_service
        self.conn = profile_repository.conn

    def get_profile(self, user_id):
        """Returns the profile dict, or None when the user has not created one yet."""
        with db_transaction(self.conn, "View user profile"):
            return self.repo.get_profile(user_id)

    def save_profile(self, user_id, date_of_birth, sex, address, job, country):
        date_of_birth, age = validate_date_of_birth(date_of_birth)
        sex = parse_sex(sex)
        address = require_text(address, "Address", 255)
        job = require_text(job, "Job", 100)
        country = require_text(country, "Country", 100)
        with db_transaction(self.conn, "Save user profile"):
            self.repo.save_profile(user_id, date_of_birth, age, sex, address, job, country)
            self.audit.record(user_id, AuditAction.UPDATE_PROFILE)
            return self.repo.get_profile(user_id)
