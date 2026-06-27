class AppError(Exception):
    status_code: int = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class DatabaseError(AppError):
    status_code = 500


class SMTPError(AppError):
    status_code = 502


class AuthenticationError(AppError):
    status_code = 401


class PartNotFoundError(AppError):
    status_code = 404


class ApproverNotFoundError(AppError):
    status_code = 422


class BatchNotFoundError(AppError):
    status_code = 404


class OrderNotFoundError(AppError):
    status_code = 404
