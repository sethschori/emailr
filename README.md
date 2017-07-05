# emailr
This is a web app which allows users to schedule and receive weekly recurring reminder emails. It is written in Python/Flask.

You can see this code in action at <a href="http://jog.gy/">jog.gy</a>. The jog.gy site is running on Amazon Web Services. The web app is running on Elastic Beanstalk/EC2 with a RDS/PostgreSQL database, a Lambda function (`messenger.py`) checks the database every five minutes and sends any pending emails using Simple Email Service (SES).

I created this when I was on a programming retreat at Recurse Center.
