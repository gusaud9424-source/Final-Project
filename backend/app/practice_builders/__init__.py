from .command_injection import CommandInjectionBuilder
from .csrf import CsrfBuilder
from .file_upload import FileUploadBuilder
from .sql_injection import SqlInjectionBuilder
from .sql_injection_blind import SqlInjectionBlindBuilder
from .xss_dom import XssDomBuilder
from .xss_reflected import XssReflectedBuilder
from .xss_stored import XssStoredBuilder

PRACTICE_BUILDERS = {
    "command-injection": CommandInjectionBuilder(),
    "xss-reflected": XssReflectedBuilder(),
    "xss-dom": XssDomBuilder(),
    "xss-stored": XssStoredBuilder(),
    "sql-injection": SqlInjectionBuilder(),
    "sql-injection-blind": SqlInjectionBlindBuilder(),
    "file-upload": FileUploadBuilder(),
    "csrf": CsrfBuilder(),
}
