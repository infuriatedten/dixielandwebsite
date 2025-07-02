class SchedulerConfig:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "UTC"  # Or your desired timezone

    # Example job definition (can also be added dynamically)
    # JOBS = [
    #     {
    #         'id': 'weekly_tax_collection',
    #         'func': 'app.jobs.taxes:run_weekly_tax_collection', # Path to your job function
    #         'trigger': 'cron',
    #         'day_of_week': 'sun', # Run every Sunday
    #         'hour': 0,            # At midnight
    #         'minute': 0
    #     }
    # ]
