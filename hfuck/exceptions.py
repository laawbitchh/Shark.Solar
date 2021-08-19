class HCaptchaError(Exception):
    pass

class ApiError(HCaptchaError):
    pass

class SolveFailed(HCaptchaError):
    pass