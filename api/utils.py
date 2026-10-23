from datetime import datetime, timezone, timedelta

# Zona Waktu Indonesia Barat (UTC+7)
WIB = timezone(timedelta(hours=7))


def now_wib(*args, **kwargs) -> datetime:
    """
    Mengembalikan datetime saat ini dalam zona waktu UTC+7 (WIB)
    sebagai naive datetime (tanpa tzinfo) agar kompatibel dengan
    kolom db.DateTime di SQLAlchemy dan MySQL.
    Menerima *args, **kwargs agar dapat dipanggil langsung (now_wib())
    maupun sebagai callback oleh SQLAlchemy ColumnDefault / onupdate.
    """
    return datetime.now(WIB).replace(tzinfo=None)


def today_wib():
    """
    Mengembalikan tanggal hari ini (date) berdasarkan zona waktu UTC+7 (WIB).
    """
    return datetime.now(WIB).date()
