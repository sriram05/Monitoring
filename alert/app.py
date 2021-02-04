import psycopg2
import psycopg2.extras
import config
import smtplib
import ssl
from email.mime.text import MIMEText
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from datetime import datetime, timezone, timedelta


logger = logging.getLogger(__name__)

log_level = logging.getLevelName(config.general['log_level'])

handler = logging.handlers.RotatingFileHandler(config.general['log_file_name'],
                                               maxBytes=config.general["max_log_size"],
                                               backupCount=config.general["max_log_file_count"])

syserr_handler = logging.StreamHandler(sys.stderr)
logger.addHandler(syserr_handler)

logger.setLevel(log_level)

formatter = logging.Formatter('%(asctime)s: %(levelname)-8s: %(threadName)-12s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

mail_count = 1
count_reset_time = time.time()


def main():
    wait_time_for_db = config.general["wait_time_for_db"]
    logger.info("Waiting [%s] seconds for DB to come up", wait_time_for_db)
    time.sleep(wait_time_for_db)
    while 1:
        alerts = get_alerts()
        num_of_alerts = len(alerts)
        if num_of_alerts > 0:
            logger.info("found [%d] alerts", num_of_alerts)
            send_alerts(alerts)
        time.sleep(config.general["sleep_time"])


def get_alerts():
    query = "SELECT * FROM sys_admin.alerts where tried=%s"
    values = [False]
    rows = []
    con = None
    try:
        con = psycopg2.connect(database=config.postgres["database"],
                               user=config.postgres["user"],
                               password=config.postgres["password"],
                               host=config.postgres["host"],
                               port=config.postgres["port"])
        cursor = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(query, values)
        rows = cursor.fetchall()
    except Exception as e:
        logger.error(str(e))
    finally:
        if con:
            con.close()
    return rows


def mark_tried(alert_id):
    query = "UPDATE sys_admin.alerts SET tried=%s where id=%s"
    values = [True, alert_id]
    try:
        con = psycopg2.connect(database=config.postgres["database"],
                               user=config.postgres["user"],
                               password=config.postgres["password"],
                               host=config.postgres["host"],
                               port=config.postgres["port"])
        cursor = con.cursor()
        cursor.execute(query, values)
        con.commit()
        logger.info("alert %d marked as tried", alert_id)
    except Exception as e:
        logger.error(str(e))
        if con:
            con.rollback()
    finally:
        if con:
            con.close()


def mark_sent(alert_id):
    query = "UPDATE sys_admin.alerts SET sent=%s where id=%s"
    values = [True, alert_id]
    try:
        con = psycopg2.connect(database=config.postgres["database"],
                               user=config.postgres["user"],
                               password=config.postgres["password"],
                               host=config.postgres["host"],
                               port=config.postgres["port"])
        cursor = con.cursor()
        cursor.execute(query, values)
        con.commit()
        logger.info("alert %d marked as sent", alert_id)
    except Exception as e:
        logger.error(str(e))
        if con:
            con.rollback()
    finally:
        if con:
            con.close()


def get_alert_type(alert_type):
    if alert_type == 1:
        return "DEBUG"
    if alert_type == 2:
        return "WARNING"
    if alert_type == 3:
        return "CRITICAL"
    return "INFO"


def send_alerts(alerts):
    global mail_count
    for row in alerts:
        alert = dict(row)
        if not is_mail_limit_exceeded():
            logger.info("sending alert with id [%d]", alert['id'])
            context = ssl.create_default_context()
            #with smtplib.SMTP_SSL(config.mail["smtp_server"], config.mail["port"], context=context) as server:
            with smtplib.SMTP(config.mail["smtp_server"], config.mail["port"]) as server:  
                server.ehlo()
                body = "Message :%s\n\nCurrent Mail Count(daily) :%d/%d\nTime :%s " % \
                       (alert['message'],
                        mail_count,
                        config.general['mails_per_day'],
                        alert['timestamp'],
                        #datetime.fromtimestamp(alert['timestamp'], timezone(timedelta(hours=8))).strftime("%c"),
                        )
                recipients = config.mail['recipients']
                message = MIMEText(body)
                message['Subject'] = "[%s][%s] %s" % (get_alert_type(alert['type']), alert['process'], alert["subject"])
                message['From'] = config.mail["sender"]
                message['To'] = ", ".join(recipients)
                #server.login(config.mail["sender"],"sMualerts@2021")
                server.sendmail(config.mail["sender"], config.mail['recipients'], message.as_string())
                mail_count += 1
                mark_sent(alert["id"])
        else:
            logger.warning("maximum daily mail count[%d] exceeded, not sending the mail", config.general['mails_per_day'])
        mark_tried(alert["id"])


def is_mail_limit_exceeded():
    global mail_count
    global count_reset_time
    logger.info("current mail count [%d]", mail_count)
    if time.time() - count_reset_time > 86400:
        logger.info("resetting mail count [%d]", mail_count)
        mail_count = 0
        count_reset_time = time.time()
    return mail_count >= config.general['mails_per_day']


if __name__ == '__main__':
    main()

