#!/usr/bin/env python3
"""DeskPet offline-persistent deadline alarms. Korea local time; alert 1h early.

Commands:
  add TITLE '2026-11-20 15:00'
  add TITLE '+61m'
  list
  remove ID
  test
  run

SQLite is stored on the Raspberry Pi at ~/deskpet/reminders.sqlite3.
"""
from __future__ import annotations

import argparse

try:
    import fcntl  # Linux(Pi) 전용
except ImportError:  # Windows 등에서 단위 테스트할 때
    fcntl = None
import hashlib
import math
import os
from pathlib import Path
import re
import shutil
import sqlite3
import struct
import subprocess
import sys
import time
import wave
from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import deskpet_env  # noqa: F401  (.env 로드)

TZ = ZoneInfo('Asia/Seoul')
ALERT_BEFORE_SEC = 3600  # 마감 1시간 전
TTS_VOICE = os.environ.get('DESKPET_TTS_VOICE', 'ko-KR-SunHiNeural')
BASE = Path(os.environ.get('DESKPET_HOME', Path.home() / 'deskpet'))
DB = BASE / 'reminders.sqlite3'
AUDIO_DIR = BASE / 'reminder_audio'
LOCK = BASE / '.audio_playback.lock'
DEVICE = os.environ.get('DESKPET_AUDIO_DEVICE', 'plughw:2,0')


def now():
    return datetime.now(TZ)


def local_time(epoch):
    return datetime.fromtimestamp(epoch, TZ).strftime('%Y-%m-%d %H:%M')


def parse_deadline(value):
    """Accept ISO/RFC3339 or local YYYY-MM-DD HH:MM; +Nm/+Nh for tests."""
    if isinstance(value, (int, float)):
        # Epoch millis are common in JSON APIs; accept seconds too.
        epoch = float(value) / (1000 if float(value) > 1e11 else 1)
        dt = datetime.fromtimestamp(epoch, TZ)
    elif isinstance(value, str):
        s = value.strip()
        rel = re.fullmatch(r'\+(\d+)([mh])', s, flags=re.IGNORECASE)
        if rel:
            count = int(rel.group(1))
            dt = now() + timedelta(minutes=count if rel.group(2).lower() == 'm' else count * 60)
        else:
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
                raise ValueError('날짜만으로는 마감 시각을 알 수 없습니다. 시간까지 입력하세요.')
            try:
                dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
            except ValueError as exc:
                raise ValueError('마감은 "2026-11-20 15:00" 형식으로 입력하세요.') from exc
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ)
            else:
                dt = dt.astimezone(TZ)
    else:
        raise ValueError('지원하지 않는 마감 형식입니다.')
    if dt.timestamp() <= time.time():
        raise ValueError('마감 시각은 현재보다 미래여야 합니다.')
    return dt


def db_connect():
    BASE.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA busy_timeout=20000')
    con.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        deadline_ts INTEGER NOT NULL,
        alert_ts INTEGER NOT NULL,
        state TEXT NOT NULL DEFAULT 'pending',
        source_key TEXT UNIQUE,
        voice_file TEXT,
        created_ts INTEGER NOT NULL,
        alerted_ts INTEGER
    )''')
    con.execute('CREATE INDEX IF NOT EXISTS idx_due ON reminders(state, alert_ts)')
    con.commit()
    return con


def audio_lock():
    BASE.mkdir(parents=True, exist_ok=True)
    f = LOCK.open('a+')
    if fcntl:
        fcntl.flock(f, fcntl.LOCK_EX)
    return f


def make_beep():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    path = AUDIO_DIR / 'beep.wav'
    if path.exists():
        return path
    rate = 48000
    samples = bytearray()
    for frequency in (660, 880):
        count = int(rate * 0.15)
        for idx in range(count):
            fade = min(1.0, idx / (rate * 0.012), (count - idx) / (rate * 0.018))
            amp = int(32767 * 0.13 * max(0, fade) * math.sin(2 * math.pi * frequency * idx / rate))
            samples.extend(struct.pack('<hh', amp, amp))
        samples.extend(b'\0\0\0\0' * int(rate * 0.12))
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(samples)
    return path


def tts_cache(title, reminder_id, late=False):
    """Generate speech when saved, so the future alarm can work without internet."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    wav = AUDIO_DIR / f'{reminder_id}.wav'
    mp3 = AUDIO_DIR / f'{reminder_id}.mp3'
    message = (
        f'마감 알림입니다. {title}. 마감까지 한 시간 미만 남았습니다.' if late
        else f'마감 한 시간 전 알림입니다. {title}. 마감까지 한 시간 남았습니다.'
    )
    edge = Path(sys.executable).with_name('edge-tts')
    cmd = str(edge) if edge.exists() else shutil.which('edge-tts')
    if not cmd or not shutil.which('ffmpeg'):
        print('[안내] edge-tts 또는 ffmpeg 없음: 알람은 부저음으로 작동합니다.', flush=True)
        return ''
    try:
        subprocess.run(
            [cmd, '--voice', TTS_VOICE, '--text', message, '--write-media', str(mp3)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=30,
        )
        subprocess.run([
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(mp3),
            '-af', 'volume=0.35', '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', str(wav),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=20)
        return str(wav)
    except (subprocess.SubprocessError, OSError) as exc:
        print(f'[안내] 음성 생성 실패(부저음 알림은 유지): {exc}', flush=True)
        return ''
    finally:
        mp3.unlink(missing_ok=True)


def add_reminder(title, deadline, source_key=None, cache_voice=True):
    title = str(title).strip()[:150]
    if not title:
        raise ValueError('제목을 입력하세요.')
    due = parse_deadline(deadline)
    due_ts = int(due.timestamp())
    key = source_key or 'local:' + hashlib.sha256(f'{title}|{due_ts}'.encode()).hexdigest()[:24]
    alert_ts = due_ts - ALERT_BEFORE_SEC
    late = alert_ts <= time.time()
    con = db_connect()
    try:
        old = con.execute('SELECT * FROM reminders WHERE source_key=?', (key,)).fetchone()
        if old and old['title'] == title and old['deadline_ts'] == due_ts:
            print(f'이미 저장된 알림입니다: {old["id"]}', flush=True)
            return old['id']
        reminder_id = old['id'] if old else uuid4().hex[:10]
        # Persist FIRST. Voice generation may fail, but the reminder must remain.
        if old:
            con.execute('''UPDATE reminders SET title=?, deadline_ts=?, alert_ts=?, state='pending',
                voice_file='', alerted_ts=NULL WHERE id=?''', (title, due_ts, alert_ts, reminder_id))
        else:
            con.execute('''INSERT INTO reminders
                (id,title,deadline_ts,alert_ts,state,source_key,voice_file,created_ts)
                VALUES (?,?,?,?,?,?,?,?)''',
                (reminder_id, title, due_ts, alert_ts, 'pending', key, '', int(time.time())))
        con.commit()
        print(f'[저장] {title} | 마감 {local_time(due_ts)} | 알림 {local_time(alert_ts)} (한국시간)', flush=True)
        if late:
            print('[안내] 마감 1시간 이내이므로 실행 중인 알람 서비스가 곧 알려줍니다.', flush=True)
        if cache_voice:
            voice_file = tts_cache(title, reminder_id, late=late)
            con.execute('UPDATE reminders SET voice_file=? WHERE id=?', (voice_file, reminder_id))
            con.commit()
        return reminder_id
    finally:
        con.close()


def list_reminders():
    con = db_connect()
    try:
        rows = con.execute('SELECT * FROM reminders ORDER BY deadline_ts ASC').fetchall()
        if not rows:
            print('저장된 마감 알림이 없습니다.')
        for r in rows:
            print(f'{r["id"]} | {r["state"]:8} | {r["title"]} | 마감 {local_time(r["deadline_ts"])} | 알림 {local_time(r["alert_ts"])}')
    finally:
        con.close()


def play_file(path):
    subprocess.run(['aplay', '-q', '-D', DEVICE, str(path)], check=True, timeout=40)


def notify(title, voice_file=''):
    print(f'🔔 마감 알림: {title}', flush=True)
    fd = audio_lock()
    try:
        play_file(make_beep())
        if voice_file and Path(voice_file).is_file():
            play_file(voice_file)
        else:
            print('[안내] 저장된 음성 없음: 알림음만 재생했습니다.', flush=True)
    finally:
        if fcntl:
            fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()


def check_due():
    con = db_connect()
    try:
        current = int(time.time())
        # Past-deadline notifications are discarded; during the last hour, notify immediately.
        con.execute("UPDATE reminders SET state='expired' WHERE state='pending' AND deadline_ts<=?", (current,))
        con.execute("UPDATE reminders SET state='pending' WHERE state='notifying'")
        con.commit()
        rows = con.execute('''SELECT * FROM reminders
            WHERE state='pending' AND alert_ts<=? AND deadline_ts>? ORDER BY deadline_ts''',
            (current, current)).fetchall()
        for row in rows:
            changed = con.execute("UPDATE reminders SET state='notifying' WHERE id=? AND state='pending'", (row['id'],)).rowcount
            con.commit()
            if not changed:
                continue
            try:
                notify(row['title'], row['voice_file'] or '')
            except (OSError, subprocess.SubprocessError) as exc:
                print(f'[오류] 알림 재생 실패 (다음 주기에 재시도): {exc}', flush=True)
                con.execute("UPDATE reminders SET state='pending' WHERE id=?", (row['id'],))
            else:
                con.execute("UPDATE reminders SET state='alerted', alerted_ts=? WHERE id=?",
                            (int(time.time()), row['id']))
            con.commit()
    finally:
        con.close()


def register_from_backend(response):
    """Register only a task_created response with explicit structured deadline.

    Returns True if registered. Text-only TTS replies are intentionally not guessed.
    """
    if not isinstance(response, dict):
        return False
    event_type = str(response.get('type', '')).lower()
    if event_type not in ('task_created', 'task_updated', 'task_create', 'created'):
        return False
    title_fields = ('title', 'name', 'task_title', 'summary', 'content', 'description')
    date_fields = ('deadline', 'due_at', 'due_date', 'deadline_at', 'due_datetime', 'dueAt', 'deadlineAt', 'due')
    queue = [response]
    seen = set()
    candidates = []
    while queue:
        item = queue.pop(0)
        if not isinstance(item, dict) or id(item) in seen:
            continue
        seen.add(id(item))
        if len(seen) > 50:
            break
        candidates.append(item)
        for v in item.values():
            if isinstance(v, dict):
                queue.append(v)
            elif isinstance(v, list):
                queue.extend(x for x in v[:10] if isinstance(x, dict))
    for item in candidates:
        due = next((item[k] for k in date_fields if item.get(k)), None)
        if due is None:
            continue
        title = next((item[k] for k in title_fields if isinstance(item.get(k), str) and item[k].strip()), None)
        if not title:
            title = str(response.get('stt_text') or '데스크펫 작업')
        ext_id = item.get('id') or item.get('task_id') or item.get('taskId')
        key = f'backend:{ext_id}' if ext_id else None
        try:
            add_reminder(title, due, source_key=key)
            return True
        except (ValueError, TypeError, OverflowError) as exc:
            print(f'[알람] 마감 시각 해석 실패: {exc}', flush=True)
    print('[알람] 작업은 생성됐지만 응답 JSON에 구조화된 마감 시각이 없어 자동 저장하지 못했습니다.', flush=True)
    print('[알람] 서버 응답에 task.deadline 또는 task.due_at 등을 포함하거나 수동 add 명령을 사용하세요.', flush=True)
    return False


def main():
    parser = argparse.ArgumentParser(description='데스크펫 마감 1시간 전 로컬 알람')
    sub = parser.add_subparsers(dest='command', required=True)
    add = sub.add_parser('add', help='작업과 마감 저장')
    add.add_argument('title')
    add.add_argument('deadline', help='YYYY-MM-DD HH:MM (한국시간) 또는 +61m')
    sub.add_parser('list', help='등록된 알람 확인')
    rm = sub.add_parser('remove', help='알람 삭제')
    rm.add_argument('id')
    sub.add_parser('test', help='바로 알림 소리와 음성 테스트')
    sub.add_parser('run', help='상시 감시 실행 (systemd)')
    args = parser.parse_args()
    if args.command == 'add':
        add_reminder(args.title, args.deadline)
    elif args.command == 'list':
        list_reminders()
    elif args.command == 'remove':
        con = db_connect()
        try:
            row = con.execute('SELECT voice_file FROM reminders WHERE id=?', (args.id,)).fetchone()
            con.execute('DELETE FROM reminders WHERE id=?', (args.id,))
            con.commit()
            if row and row['voice_file']:
                Path(row['voice_file']).unlink(missing_ok=True)
            print('삭제 완료' if row else '해당 ID 없음')
        finally:
            con.close()
    elif args.command == 'test':
        print('지금 즉시 알람 테스트(작업 등록 없음)')
        tmp_id = 'test_' + uuid4().hex[:6]
        voice = tts_cache('보고서 작성', tmp_id)
        notify('보고서 작성', voice)
        if voice:
            Path(voice).unlink(missing_ok=True)
    elif args.command == 'run':
        print(f'[가동] 마감 알람 감시 중 | DB={DB} | 장치={DEVICE} | Ctrl+C 종료', flush=True)
        while True:
            check_due()
            time.sleep(4)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n알람 서비스 종료')
    except ValueError as exc:
        print(f'[입력 오류] {exc}', file=sys.stderr)
        sys.exit(2)
