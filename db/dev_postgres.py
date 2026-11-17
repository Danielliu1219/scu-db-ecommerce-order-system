"""Start a checkout-specific PostgreSQL cluster without changing system services."""

import argparse
import hashlib
import os
import secrets
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(tempfile.gettempdir()) / (
    "scu-ecommerce-postgres-" + hashlib.sha256(str(ROOT).encode()).hexdigest()[:10]
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "stop"))
    parser.add_argument("--bin", type=Path, help="Directory containing initdb and pg_ctl")
    parser.add_argument("--port", type=int, default=55432)
    parser.add_argument("--env-file", type=Path, default=ROOT / "backend/.env")
    args = parser.parse_args()
    found = shutil.which("pg_ctl")
    binary = args.bin or (Path(found).parent if found else None)
    if binary is None:
        parser.error("Install PostgreSQL 18 binaries locally or specify --bin")
    suffix = ".exe" if os.name == "nt" else ""
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    def run(tool, *arguments):
        subprocess.run(
            [str(binary / (tool + suffix)), *map(str, arguments)], check=True, creationflags=flags
        )

    data = RUNTIME / "data"
    if args.action == "stop":
        if not (data / "PG_VERSION").is_file():
            raise SystemExit("No checkout-specific PostgreSQL cluster exists")
        run("pg_ctl", "-D", data, "-m", "fast", "-w", "stop")
        return
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", args.port)) == 0:
            raise SystemExit("Port already in use; no instance started")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    password_file = RUNTIME / "owner.secret"
    if not (data / "PG_VERSION").exists():
        password_file.write_text(secrets.token_hex(24), encoding="utf-8")
        run(
            "initdb",
            "-D",
            data,
            "--username=scu_owner",
            f"--pwfile={password_file}",
            "--auth=scram-sha-256",
            "--encoding=UTF8",
            "--locale=C",
        )
    if not password_file.is_file():
        raise SystemExit("Cluster credential file missing; no credentials were reset")
    run(
        "pg_ctl",
        "-D",
        data,
        "-l",
        RUNTIME / "postgres.log",
        "-o",
        f"-h 127.0.0.1 -p {args.port} -c timezone=Asia/Shanghai",
        "-w",
        "start",
    )
    if not args.env_file.exists():
        values = dict(dotenv_values(ROOT / "backend/.env"))
        password = password_file.read_text(encoding="utf-8").strip()
        for key, database in (
            ("DATABASE_URL", "scu_ecommerce"),
            ("TEST_DATABASE_URL", "scu_ecommerce_test"),
        ):
            values[key] = URL.create(
                "postgresql+psycopg",
                username="scu_owner",
                password=password,
                host="127.0.0.1",
                port=args.port,
                database=database,
            ).render_as_string(hide_password=False)
        values.setdefault("JWT_SECRET", secrets.token_hex(32))
        values.setdefault("APP_TIMEZONE", "Asia/Shanghai")
        args.env_file.parent.mkdir(parents=True, exist_ok=True)
        args.env_file.write_text(
            "\n".join(f"{k}={v}" for k, v in values.items() if v is not None) + "\n",
            encoding="utf-8",
        )
    print(
        f"Isolated PostgreSQL ready on 127.0.0.1:{args.port}; existing env files and services preserved"
    )


if __name__ == "__main__":
    main()
