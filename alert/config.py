log_levels = dict(
    critical='CRITICAL',
    error='ERROR',
    warning='WARNING',
    info='INFO',
    debug='DEBUG'
)

postgres = dict(
    database="rtls",
    user="indoorloc",
    password="indoorloc",
    #host="postgre",
    #host="10.4.12.95",
    host="10.0.109.85",
    #port="5432",
    port="5914",
)
"""
mail = dict(
    sender="smularc.sb@gmail.com",#"harishantht@smu.edu.sg",
    recipients=["thirahari@gmail.com"],
    smtp_server="smtp.gmail.com",#"smtp.smu.edu.sg",
    port=587,#465,
)
"""
mail = dict(
    sender="harishantht@smu.edu.sg",
    recipients=["harishantht@smu.edu.sg"],
    smtp_server="smtp.smu.edu",
    port=25,
)

general = dict(
    sleep_time=5,
    log_file_name="logs/alerts.log",
    log_level=log_levels["debug"],
    max_log_size=1024 ** 3,  # 1GB
    max_log_file_count=3,
    wait_time_for_db=20,
    mails_per_day=10,
)

