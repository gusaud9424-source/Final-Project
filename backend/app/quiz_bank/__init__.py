from .command_injection import QUESTIONS as COMMAND_INJECTION_QUESTIONS
from .xss_reflected import QUESTIONS as XSS_REFLECTED_QUESTIONS
from .xss_dom import QUESTIONS as XSS_DOM_QUESTIONS
from .xss_stored import QUESTIONS as XSS_STORED_QUESTIONS
from .sql_injection import QUESTIONS as SQL_INJECTION_QUESTIONS
from .sql_injection_blind import QUESTIONS as SQL_INJECTION_BLIND_QUESTIONS
from .file_upload import QUESTIONS as FILE_UPLOAD_QUESTIONS
from .csrf import QUESTIONS as CSRF_QUESTIONS

QUIZ_BANKS = {
    "command-injection": COMMAND_INJECTION_QUESTIONS,
    "xss-reflected": XSS_REFLECTED_QUESTIONS,
    "xss-dom": XSS_DOM_QUESTIONS,
    "xss-stored": XSS_STORED_QUESTIONS,
    "sql-injection": SQL_INJECTION_QUESTIONS,
    "sql-injection-blind": SQL_INJECTION_BLIND_QUESTIONS,
    "file-upload": FILE_UPLOAD_QUESTIONS,
    "csrf": CSRF_QUESTIONS,
}
