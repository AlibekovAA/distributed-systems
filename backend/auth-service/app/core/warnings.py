import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="passlib.utils", message="'crypt' is deprecated")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="crypt")
warnings.filterwarnings("ignore", category=UserWarning, module="sqlalchemy")
