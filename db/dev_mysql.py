"""Optional isolated local MySQL. Does not start/modify the MySQL80 service."""

import argparse
import os
import secrets
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import pymysql

ROOT = Path(__file__).resolve().parents[1]
# MySQL on Windows does not reliably reopen Unicode data-directory paths.
RUNTIME = Path(tempfile.gettempdir()) / "scu-ecommerce-dev-mysql"
ENV = ROOT / "backend/.env"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop"])
    parser.add_argument("--bin", default=r"C:\Program Files\MySQL\MySQL Server 8.0\bin")
    parser.add_argument("--port", type=int, default=33316)
    args = parser.parse_args()
    password_file = RUNTIME / "root.secret"
    if args.action == "stop":
        password = password_file.read_text()
        conn = pymysql.connect(host="127.0.0.1", port=args.port, user="root", password=password)
        try:
            conn.cursor().execute("SHUTDOWN")
        finally:
            conn.close()
        print("Isolated instance stopped")
        return
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", args.port)) == 0:
            raise SystemExit("Port already in use; no instance started")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    data = RUNTIME / "data"
    binary = str(Path(args.bin) / "mysqld.exe")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    common = [
        binary,
        "--no-defaults",
        f"--basedir={Path(args.bin).parent}",
        f"--datadir={data}",
    ]
    fresh = not (data / "mysql").exists()
    if fresh:
        subprocess.run(
            common + ["--initialize-insecure"],
            check=True,
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    password = "" if fresh or not password_file.exists() else password_file.read_text()
    process = subprocess.Popen(
        common
        + [
            "--console",
            "--bind-address=127.0.0.1",
            f"--port={args.port}",
            "--mysqlx=OFF",
            f"--log-error={RUNTIME / 'mysql.log'}",
            "--innodb-buffer-pool-size=128M",
        ],
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        try:
            conn = pymysql.connect(
                host="127.0.0.1",
                port=args.port,
                user="root",
                password=password,
                connect_timeout=1,
            )
            break
        except pymysql.Error:
            if process.poll() is not None:
                raise SystemExit(f"MySQL exited; inspect {RUNTIME / 'mysql.log'}")
            time.sleep(0.5)
    else:
        raise SystemExit(f"MySQL did not become ready; inspect {RUNTIME / 'mysql.log'}")
    if fresh or not password_file.exists():
        password = secrets.token_hex(24)
        with conn.cursor() as cursor:
            cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (password,))
        password_file.write_text(password)
    conn.close()
    if not ENV.exists():
        base = f"mysql+pymysql://root:{password}@127.0.0.1:{args.port}/"
        ENV.write_text(
            f"DATABASE_URL={base}scu_ecommerce?charset=utf8mb4\nTEST_DATABASE_URL={base}scu_ecommerce_test?charset=utf8mb4\nJWT_SECRET={secrets.token_hex(32)}\nAPP_TIMEZONE=Asia/Shanghai\n",
            encoding="utf-8",
        )
    print(
        f"Isolated MySQL ready on 127.0.0.1:{args.port}; account root configured locally; existing service untouched"
    )


if __name__ == "__main__":
    main()
